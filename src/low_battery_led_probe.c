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
#include <zephyr/usb/usb_device.h>

#include <zmk/usb.h>

LOG_MODULE_REGISTER(nocfree_low_battery_led_probe, LOG_LEVEL_INF);

#define INDICATOR_NODE                                                         \
    DT_COMPAT_GET_ANY_STATUS_OKAY(nocfree_open_drain_indicator)

static const struct gpio_dt_spec indicator =
    GPIO_DT_SPEC_GET(INDICATOR_NODE, gpios);

static uint8_t blink_phase;

static void release_indicator(void) {
    /* With GPIO_ACTIVE_LOW | GPIO_OPEN_DRAIN, inactive means high impedance. */
    (void)gpio_pin_set_dt(&indicator, 0);
}

static bool usb_is_disconnected(void) {
    return zmk_usb_get_conn_state() == USB_DC_DISCONNECTED;
}

static void indicator_probe_work(struct k_work *work) {
    struct k_work_delayable *delayable = k_work_delayable_from_work(work);

    if (!usb_is_disconnected()) {
        blink_phase = 0;
        release_indicator();
        k_work_reschedule(delayable, K_MSEC(500));
        return;
    }

    switch (blink_phase) {
    case 0:
    case 2:
        /* Active-low open drain: active pulls low and can never drive high. */
        (void)gpio_pin_set_dt(&indicator, 1);
        blink_phase++;
        k_work_reschedule(delayable, K_MSEC(180));
        break;
    case 1:
        release_indicator();
        blink_phase++;
        k_work_reschedule(delayable, K_MSEC(220));
        break;
    default:
        release_indicator();
        blink_phase = 0;
        k_work_reschedule(delayable, K_SECONDS(5));
        break;
    }
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
    LOG_INF("NOCFREE_LED_PROBE ready; disconnect USB to start double blink");
    k_work_schedule(&indicator_probe, K_MSEC(500));
    return 0;
}

SYS_INIT(indicator_probe_init, APPLICATION,
         CONFIG_APPLICATION_INIT_PRIORITY);
