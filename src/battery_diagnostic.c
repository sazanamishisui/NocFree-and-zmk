/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Print battery events received by the USB dongle from split peripherals.
 */

#include <zephyr/logging/log.h>

#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>

LOG_MODULE_REGISTER(nocfree_battery_diagnostic, LOG_LEVEL_INF);

static int battery_diagnostic_listener(const zmk_event_t *eh) {
    const struct zmk_peripheral_battery_state_changed *event =
        as_zmk_peripheral_battery_state_changed(eh);

    if (event == NULL) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    LOG_INF("NOCFREE_BATTERY peripheral=%u level=%u%%", event->source,
            event->state_of_charge);
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(nocfree_battery_diagnostic, battery_diagnostic_listener);
ZMK_SUBSCRIPTION(nocfree_battery_diagnostic, zmk_peripheral_battery_state_changed);
