/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Local low-battery warning for one NocFree keyboard half.
 */

#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>

#include <nrf.h>

#include <zmk/battery.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>

#define INDICATOR_NODE                                                         \
    DT_COMPAT_GET_ANY_STATUS_OKAY(nocfree_open_drain_indicator)

#define LOW_BATTERY_THRESHOLD 15
#define INITIAL_LEVEL_DELAY K_SECONDS(5)
#define USB_RECHECK_DELAY K_SECONDS(10)
#define WARNING_REPEAT_DELAY K_MINUTES(1)
#define WARNING_ON_TIME K_MSEC(180)
#define WARNING_GAP_TIME K_MSEC(220)

static const struct gpio_dt_spec indicator =
    GPIO_DT_SPEC_GET(INDICATOR_NODE, gpios);

enum warning_phase {
    WARNING_IDLE,
    WARNING_FIRST_ON,
    WARNING_GAP,
    WARNING_SECOND_ON,
};

static enum warning_phase phase;
static uint8_t battery_level = UINT8_MAX;
static bool indicator_ready;

static bool usb_vbus_present(void) {
    return (NRF_POWER->USBREGSTATUS & POWER_USBREGSTATUS_VBUSDETECT_Msk) != 0;
}

static void release_indicator(void) {
    if (indicator_ready) {
        /* Active-low open drain: inactive is an electrical release. */
        (void)gpio_pin_set_dt(&indicator, 0);
    }
}

static bool battery_is_low(void) {
    return battery_level <= LOW_BATTERY_THRESHOLD;
}

static void warning_work_handler(struct k_work *work) {
    struct k_work_delayable *delayable = k_work_delayable_from_work(work);

    if (battery_level == UINT8_MAX) {
        battery_level = zmk_battery_state_of_charge();
    }

    if (!battery_is_low()) {
        phase = WARNING_IDLE;
        release_indicator();
        return;
    }

    if (usb_vbus_present()) {
        phase = WARNING_IDLE;
        release_indicator();
        k_work_reschedule(delayable, USB_RECHECK_DELAY);
        return;
    }

    switch (phase) {
    case WARNING_IDLE:
        (void)gpio_pin_set_dt(&indicator, 1);
        phase = WARNING_FIRST_ON;
        k_work_reschedule(delayable, WARNING_ON_TIME);
        break;
    case WARNING_FIRST_ON:
        release_indicator();
        phase = WARNING_GAP;
        k_work_reschedule(delayable, WARNING_GAP_TIME);
        break;
    case WARNING_GAP:
        (void)gpio_pin_set_dt(&indicator, 1);
        phase = WARNING_SECOND_ON;
        k_work_reschedule(delayable, WARNING_ON_TIME);
        break;
    case WARNING_SECOND_ON:
    default:
        release_indicator();
        phase = WARNING_IDLE;
        k_work_reschedule(delayable, WARNING_REPEAT_DELAY);
        break;
    }
}

K_WORK_DELAYABLE_DEFINE(warning_work, warning_work_handler);

static void update_battery_level(uint8_t level) {
    battery_level = level;

    if (battery_is_low()) {
        if (!k_work_delayable_is_pending(&warning_work)) {
            k_work_reschedule(&warning_work, K_NO_WAIT);
        }
    } else {
        (void)k_work_cancel_delayable(&warning_work);
        phase = WARNING_IDLE;
        release_indicator();
    }
}

static int low_battery_listener(const zmk_event_t *eh) {
    const struct zmk_battery_state_changed *event =
        as_zmk_battery_state_changed(eh);

    if (event == NULL) {
        return -ENOTSUP;
    }

    update_battery_level(event->state_of_charge);
    return 0;
}

ZMK_LISTENER(nocfree_low_battery_indicator, low_battery_listener);
ZMK_SUBSCRIPTION(nocfree_low_battery_indicator, zmk_battery_state_changed);

static int low_battery_indicator_init(void) {
    if (!gpio_is_ready_dt(&indicator)) {
        return -ENODEV;
    }

    int rc = gpio_pin_configure_dt(&indicator, GPIO_OUTPUT_INACTIVE);
    if (rc != 0) {
        return rc;
    }

    indicator_ready = true;
    release_indicator();
    k_work_schedule(&warning_work, INITIAL_LEVEL_DELAY);
    return 0;
}

SYS_INIT(low_battery_indicator_init, APPLICATION,
         CONFIG_APPLICATION_INIT_PRIORITY);
