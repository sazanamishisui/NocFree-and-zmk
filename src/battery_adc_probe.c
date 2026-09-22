/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Compare AIN2 with the verified battery-divider enable inactive and active.
 */

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(nocfree_battery_adc_probe, LOG_LEVEL_INF);

#define BATTERY_NODE DT_CHOSEN(zmk_battery)
#define ADC_NODE DT_IO_CHANNELS_CTLR(BATTERY_NODE)
#define ADC_CHANNEL DT_IO_CHANNELS_INPUT(BATTERY_NODE)

static const struct device *const adc = DEVICE_DT_GET(ADC_NODE);
static const struct gpio_dt_spec divider_enable =
    GPIO_DT_SPEC_GET(BATTERY_NODE, power_gpios);

static int16_t sample_buffer;

static struct adc_channel_cfg channel_config = {
    .gain = ADC_GAIN_1_6,
    .reference = ADC_REF_INTERNAL,
    .acquisition_time = ADC_ACQ_TIME(ADC_ACQ_TIME_MICROSECONDS, 40),
    .input_positive = SAADC_CH_PSELP_PSELP_AnalogInput0 + ADC_CHANNEL,
};

static struct adc_sequence sequence = {
    .channels = BIT(0),
    .buffer = &sample_buffer,
    .buffer_size = sizeof(sample_buffer),
    .resolution = 12,
    .oversampling = 4,
    .calibrate = true,
};

static int take_sample(int16_t *raw, int32_t *pin_mv) {
    int rc = adc_read(adc, &sequence);

    sequence.calibrate = false;
    if (rc != 0) {
        return rc;
    }

    *raw = sample_buffer;
    *pin_mv = sample_buffer;
    return adc_raw_to_millivolts(adc_ref_internal(adc), channel_config.gain,
                                 sequence.resolution, pin_mv);
}

static void battery_adc_probe_work(struct k_work *work) {
    struct k_work_delayable *delayable = k_work_delayable_from_work(work);
    int16_t off_raw = 0;
    int16_t on_raw = 0;
    int32_t off_pin_mv = 0;
    int32_t on_pin_mv = 0;
    int rc;

    rc = gpio_pin_set_dt(&divider_enable, 0);
    if (rc != 0) {
        LOG_ERR("NOCFREE_ADC_PROBE disable_error=%d", rc);
        goto reschedule;
    }

    /* Let the measurement node discharge before checking the disabled state. */
    k_sleep(K_MSEC(100));
    rc = take_sample(&off_raw, &off_pin_mv);
    if (rc != 0) {
        LOG_ERR("NOCFREE_ADC_PROBE off_sample_error=%d", rc);
        goto reschedule;
    }

    rc = gpio_pin_set_dt(&divider_enable, 1);
    if (rc != 0) {
        LOG_ERR("NOCFREE_ADC_PROBE enable_error=%d", rc);
        goto reschedule;
    }

    /* Match the established ZMK battery driver's divider settling delay. */
    k_sleep(K_MSEC(10));
    rc = take_sample(&on_raw, &on_pin_mv);
    (void)gpio_pin_set_dt(&divider_enable, 0);
    if (rc != 0) {
        LOG_ERR("NOCFREE_ADC_PROBE on_sample_error=%d", rc);
        goto reschedule;
    }

    const int32_t factory_mv =
        (int32_t)(((int64_t)on_raw * 3300 * 130) / (4095 * 100));
    const int32_t current_zmk_mv =
        (int32_t)(((int64_t)on_pin_mv * 143) / 120);

    LOG_INF("NOCFREE_ADC_PROBE off_raw=%d off_pin_mv=%d "
            "on_raw=%d on_pin_mv=%d factory_mv=%d current_zmk_mv=%d",
            off_raw, off_pin_mv, on_raw, on_pin_mv, factory_mv,
            current_zmk_mv);

reschedule:
    /* The divider is inactive between samples, including every error path. */
    (void)gpio_pin_set_dt(&divider_enable, 0);
    k_work_reschedule(delayable, K_SECONDS(5));
}

K_WORK_DELAYABLE_DEFINE(battery_adc_probe, battery_adc_probe_work);

static int battery_adc_probe_init(void) {
    if (!device_is_ready(adc) || !device_is_ready(divider_enable.port)) {
        LOG_ERR("NOCFREE_ADC_PROBE device_not_ready");
        return -ENODEV;
    }

    int rc = gpio_pin_configure_dt(&divider_enable, GPIO_OUTPUT_INACTIVE);
    if (rc != 0) {
        return rc;
    }

    rc = adc_channel_setup(adc, &channel_config);
    if (rc != 0) {
        return rc;
    }

    k_work_schedule(&battery_adc_probe, K_SECONDS(3));
    return 0;
}

SYS_INIT(battery_adc_probe_init, APPLICATION,
         CONFIG_APPLICATION_INIT_PRIORITY);
