/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Show the highest active ZMK layer on the XIAO nRF52840 RGB LED.
 */

#include <errno.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>
#include <zephyr/sys/util.h>
#include <zmk/event_manager.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/keymap.h>

#include "nocfree_layer_led_indicator.h"

#define BASE_LAYER 0
#define FN_LAYER 1
#define NAV_LAYER 2
#define NUMPAD_LAYER 3
#define WORK_LAYER 4

static const struct gpio_dt_spec red_led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static const struct gpio_dt_spec green_led = GPIO_DT_SPEC_GET(DT_ALIAS(led1), gpios);
static const struct gpio_dt_spec blue_led = GPIO_DT_SPEC_GET(DT_ALIAS(led2), gpios);

static bool indicator_ready;
static bool battery_display_active;

struct led_step {
    bool red;
    bool green;
    bool blue;
    k_timeout_t duration;
};

#define MAX_BATTERY_LED_STEPS 24
#define MARKER_ON_TIME K_MSEC(160)
#define MARKER_OFF_TIME K_MSEC(140)
#define LEVEL_ON_TIME K_MSEC(1200)
#define INVALID_ON_TIME K_MSEC(250)
#define INVALID_OFF_TIME K_MSEC(150)
#define SIDE_GAP_TIME K_MSEC(300)

static struct led_step battery_steps[MAX_BATTERY_LED_STEPS];
static size_t battery_step_count;
static size_t battery_step_index;

static void set_indicator(bool red, bool green, bool blue) {
    if (!indicator_ready) {
        return;
    }

    (void)gpio_pin_set_dt(&red_led, red);
    (void)gpio_pin_set_dt(&green_led, green);
    (void)gpio_pin_set_dt(&blue_led, blue);
}

static void update_layer_indicator(void) {
    zmk_keymap_layer_index_t highest = zmk_keymap_highest_layer_active();
    zmk_keymap_layer_id_t layer = zmk_keymap_layer_index_to_id(highest);

    switch (layer) {
    case BASE_LAYER:
        set_indicator(false, false, false);
        break;
    case FN_LAYER:
        set_indicator(false, false, true);
        break;
    case NAV_LAYER:
        set_indicator(false, true, false);
        break;
    case NUMPAD_LAYER:
        set_indicator(true, false, false);
        break;
    case WORK_LAYER:
        set_indicator(true, false, true);
        break;
    default:
        set_indicator(true, true, true);
        break;
    }
}

static void append_step(bool red, bool green, bool blue, k_timeout_t duration) {
    if (battery_step_count >= ARRAY_SIZE(battery_steps)) {
        return;
    }

    battery_steps[battery_step_count++] =
        (struct led_step){.red = red, .green = green, .blue = blue, .duration = duration};
}

static void append_marker(unsigned int flashes) {
    for (unsigned int i = 0; i < flashes; i++) {
        append_step(true, true, true, MARKER_ON_TIME);
        append_step(false, false, false, MARKER_OFF_TIME);
    }
}

static void append_level(uint8_t level, bool valid) {
    if (!valid || level > 100U) {
        /* Two purple flashes mean that no trustworthy value was returned. */
        append_step(true, false, true, INVALID_ON_TIME);
        append_step(false, false, false, INVALID_OFF_TIME);
        append_step(true, false, true, INVALID_ON_TIME);
        return;
    }

    if (level <= 15U) {
        append_step(true, false, false, LEVEL_ON_TIME);
    } else if (level <= 50U) {
        append_step(true, true, false, LEVEL_ON_TIME);
    } else {
        append_step(false, true, false, LEVEL_ON_TIME);
    }
}

static void battery_led_work_handler(struct k_work *work) {
    struct k_work_delayable *delayable = k_work_delayable_from_work(work);

    if (battery_step_index >= battery_step_count) {
        battery_display_active = false;
        update_layer_indicator();
        return;
    }

    const struct led_step *step = &battery_steps[battery_step_index++];
    set_indicator(step->red, step->green, step->blue);
    k_work_reschedule(delayable, step->duration);
}

K_WORK_DELAYABLE_DEFINE(battery_led_work, battery_led_work_handler);

void nocfree_layer_led_show_battery(uint8_t left_level, bool left_valid,
                                    uint8_t right_level, bool right_valid,
                                    uint8_t pad_level, bool pad_valid) {
    if (!indicator_ready) {
        return;
    }

    (void)k_work_cancel_delayable(&battery_led_work);
    battery_step_count = 0;
    battery_step_index = 0;

    /* One white marker = left, two = right, three = Pad. */
    append_marker(1);
    append_level(left_level, left_valid);
    append_step(false, false, false, SIDE_GAP_TIME);
    append_marker(2);
    append_level(right_level, right_valid);
    append_step(false, false, false, SIDE_GAP_TIME);
    append_marker(3);
    append_level(pad_level, pad_valid);

    battery_display_active = true;
    k_work_reschedule(&battery_led_work, K_NO_WAIT);
}

static int layer_indicator_init(void) {
    const struct gpio_dt_spec *leds[] = {&red_led, &green_led, &blue_led};

    for (size_t i = 0; i < ARRAY_SIZE(leds); i++) {
        if (!gpio_is_ready_dt(leds[i])) {
            return -ENODEV;
        }

        int err = gpio_pin_configure_dt(leds[i], GPIO_OUTPUT_INACTIVE);
        if (err < 0) {
            return err;
        }
    }

    indicator_ready = true;
    update_layer_indicator();
    return 0;
}

SYS_INIT(layer_indicator_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);

static int layer_indicator_event_listener(const zmk_event_t *eh) {
    if (as_zmk_layer_state_changed(eh) != NULL && !battery_display_active) {
        update_layer_indicator();
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(nocfree_layer_indicator, layer_indicator_event_listener);
ZMK_SUBSCRIPTION(nocfree_layer_indicator, zmk_layer_state_changed);
