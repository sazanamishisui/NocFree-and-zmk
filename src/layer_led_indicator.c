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

#define BASE_LAYER 0
#define FN_LAYER 1
#define NAV_LAYER 2
#define NUMPAD_LAYER 3
#define WORK_LAYER 4

static const struct gpio_dt_spec red_led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static const struct gpio_dt_spec green_led = GPIO_DT_SPEC_GET(DT_ALIAS(led1), gpios);
static const struct gpio_dt_spec blue_led = GPIO_DT_SPEC_GET(DT_ALIAS(led2), gpios);

static bool indicator_ready;

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
    if (as_zmk_layer_state_changed(eh) != NULL) {
        update_layer_indicator();
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(nocfree_layer_indicator, layer_indicator_event_listener);
ZMK_SUBSCRIPTION(nocfree_layer_indicator, zmk_layer_state_changed);
