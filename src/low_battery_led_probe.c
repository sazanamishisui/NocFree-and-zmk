/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Safely verify the shared red charge/low-battery indicator.
 */

#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <nrf.h>

LOG_MODULE_REGISTER(nocfree_low_battery_led_probe, LOG_LEVEL_INF);

#define INDICATOR_NODE                                                         \
    DT_COMPAT_GET_ANY_STATUS_OKAY(nocfree_open_drain_indicator)

static const struct gpio_dt_spec indicator =
    GPIO_DT_SPEC_GET(INDICATOR_NODE, gpios);

#define PHASE_TICKS 12
#define PROBE_TICK_MS 250

static bool pulling_low;
static uint8_t phase_ticks;

static void release_indicator(void) {
    /* With GPIO_ACTIVE_LOW | GPIO_OPEN_DRAIN, inactive means high impedance. */
    (void)gpio_pin_set_dt(&indicator, 0);
}

static bool usb_vbus_present(void) {
    return (NRF_POWER->USBREGSTATUS & POWER_USBREGSTATUS_VBUSDETECT_Msk) != 0;
}

static void indicator_probe_work(struct k_work *work) {
    struct k_work_delayable *delayable = k_work_delayable_from_work(work);

    if (usb_vbus_present()) {
        pulling_low = false;
        phase_ticks = 0;
        release_indicator();
        k_work_reschedule(delayable, K_MSEC(PROBE_TICK_MS));
        return;
    }

    if (phase_ticks == 0) {
        pulling_low = !pulling_low;
        if (pulling_low) {
            /* Active-low open drain can pull low but can never drive high. */
            (void)gpio_pin_set_dt(&indicator, 1);
            LOG_INF("NOCFREE_LED_PROBE phase=pull_low");
        } else {
            release_indicator();
            LOG_INF("NOCFREE_LED_PROBE phase=release");
        }
    }

    phase_ticks = (phase_ticks + 1) % PHASE_TICKS;
    k_work_reschedule(delayable, K_MSEC(PROBE_TICK_MS));
}

K_WORK_DELAYABLE_DEFINE(indicator_probe, indicator_probe_work);

static int indicator_probe_init(void) {
    if (!gpio_is_ready_dt(&indicator)) {
        LOG_ERR("NOCFREE_LED_PROBE device_not_ready");
        return -ENODEV;
    }

    /* GPIO_OUTPUT_INACTIVE plus the DT open-drain flag starts released. */
    int rc = gpio_pin_configure_dt(&indicator, GPIO_OUTPUT_INACTIVE);
    if (rc != 0) {
        release_indicator();
        LOG_ERR("NOCFREE_LED_PROBE configure_error=%d", rc);
        return rc;
    }

    release_indicator();
    LOG_INF("NOCFREE_LED_PROBE ready; disconnect USB to alternate low/release");
    k_work_schedule(&indicator_probe, K_MSEC(PROBE_TICK_MS));
    return 0;
}

SYS_INIT(indicator_probe_init, APPLICATION,
         CONFIG_APPLICATION_INIT_PRIORITY);
