/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Route output after the stock Studio Bluetooth-profile keys are pressed.
 *
 * ZMK Studio can keep its dynamic keymap binding (&bt BT_SEL n) even when a
 * firmware update changes that position to a custom behavior. Observe the
 * physical Fn+1..5 positions instead, allow the stock profile selection to
 * finish, and then prefer BLE. Fn+U cancels a pending switch and prefers USB.
 */

#include <zephyr/kernel.h>
#include <zmk/event_manager.h>
#include <zmk/endpoints.h>
#include <zmk/events/position_state_changed.h>
#include <zmk/keymap.h>

#define BLE_OUTPUT_SWITCH_DELAY_MS 750
#define FN_LAYER 1

/* Linear positions in the 85-key dongle keymap. */
#define POSITION_FN_1 16
#define POSITION_FN_5 20
#define POSITION_FN_U 37

static bool ble_output_pending;

static void ble_output_work_handler(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(ble_output_work, ble_output_work_handler);

static void cancel_pending_ble_output(void) {
    ble_output_pending = false;
    (void)k_work_cancel_delayable(&ble_output_work);
}

static void ble_output_work_handler(struct k_work *work) {
    (void)work;

    if (!ble_output_pending) {
        return;
    }

    ble_output_pending = false;
    (void)zmk_endpoint_set_preferred_transport(ZMK_TRANSPORT_BLE);
}

static int route_profile_key_output(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *event = as_zmk_position_state_changed(eh);

    if (event == NULL || !event->state || !zmk_keymap_layer_active(FN_LAYER)) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    if (event->position >= POSITION_FN_1 && event->position <= POSITION_FN_5) {
        cancel_pending_ble_output();
        ble_output_pending = true;
        (void)k_work_reschedule(&ble_output_work, K_MSEC(BLE_OUTPUT_SWITCH_DELAY_MS));
    } else if (event->position == POSITION_FN_U) {
        cancel_pending_ble_output();
        (void)zmk_endpoint_set_preferred_transport(ZMK_TRANSPORT_USB);
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(nocfree_profile_output_router, route_profile_key_output);
ZMK_SUBSCRIPTION(nocfree_profile_output_router, zmk_position_state_changed);
