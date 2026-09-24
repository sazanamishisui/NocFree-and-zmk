/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * On-demand, bounds-checked reads of the standard Battery Service exposed by
 * the two NocFree keyboard halves and Pad. This intentionally does not enable ZMK's
 * continuous split-central battery fetching path.
 */

#define DT_DRV_COMPAT nocfree_behavior_battery_status

#include <errno.h>
#include <string.h>

#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/util.h>

#include <drivers/behavior.h>
#include <zmk/behavior.h>

#include "nocfree_layer_led_indicator.h"

LOG_MODULE_REGISTER(nocfree_battery_status, CONFIG_ZMK_LOG_LEVEL);

/* Observed and preserved pairing order: source 0 = right, 1 = left, 2 = Pad. */
#define RIGHT_SOURCE 0
#define LEFT_SOURCE 1
#define PAD_SOURCE 2
#define PERIPHERAL_SOURCE_COUNT 3
#define QUERY_TIMEOUT K_MSEC(2500)

/*
 * This function is global in the pinned ZMK split BLE central implementation,
 * but is not part of its public header. Keeping the declaration here avoids
 * patching upstream ZMK while still using its authoritative connection-to-slot
 * mapping. Every returned value is bounds checked before it is used.
 */
extern int peripheral_slot_index_for_conn(struct bt_conn *conn);

struct battery_query_slot {
    struct bt_conn *conn;
    struct bt_gatt_read_params read;
    uint8_t level;
    bool done;
};

static struct battery_query_slot slots[PERIPHERAL_SOURCE_COUNT];
static atomic_t query_active;
static atomic_t enumeration_complete;
static atomic_t pending_mask;
static atomic_t valid_mask;
static atomic_t displayed;

static void maybe_finish_query(void);

static void finish_slot(uint8_t source, bool valid, uint8_t level) {
    if (source >= ARRAY_SIZE(slots)) {
        return;
    }

    struct battery_query_slot *slot = &slots[source];
    if (slot->done) {
        return;
    }

    slot->done = true;
    if (valid && level <= 100U) {
        slot->level = level;
        atomic_or(&valid_mask, BIT(source));
    }

    if (slot->conn != NULL) {
        bt_conn_unref(slot->conn);
        slot->conn = NULL;
    }

    atomic_and(&pending_mask, ~BIT(source));
    maybe_finish_query();
}

static uint8_t battery_read_cb(struct bt_conn *conn, uint8_t err,
                               struct bt_gatt_read_params *params,
                               const void *data, uint16_t length) {
    ARG_UNUSED(conn);

    struct battery_query_slot *slot =
        CONTAINER_OF(params, struct battery_query_slot, read);
    uint8_t source = (uint8_t)(slot - slots);

    if (err != 0U || data == NULL || length < 1U) {
        finish_slot(source, false, 0U);
        return BT_GATT_ITER_STOP;
    }

    finish_slot(source, true, ((const uint8_t *)data)[0]);
    return BT_GATT_ITER_STOP;
}

static void start_query_for_conn(struct bt_conn *conn, void *user_data) {
    ARG_UNUSED(user_data);

    struct bt_conn_info info;
    if (bt_conn_get_info(conn, &info) != 0 || info.role != BT_CONN_ROLE_CENTRAL) {
        return;
    }

    int source = peripheral_slot_index_for_conn(conn);
    if (source < 0 || source >= PERIPHERAL_SOURCE_COUNT) {
        /* Ignore host-facing BLE links and every invalid split-slot index. */
        return;
    }

    struct battery_query_slot *slot = &slots[source];
    if (slot->conn != NULL || atomic_test_bit(&pending_mask, source)) {
        return;
    }

    slot->conn = bt_conn_ref(conn);
    slot->done = false;
    atomic_or(&pending_mask, BIT(source));

    /* One Read-Using-Characteristic-UUID operation; no subscription/cache. */
    (void)memset(&slot->read, 0, sizeof(slot->read));
    slot->read.func = battery_read_cb;
    slot->read.handle_count = 0;
    slot->read.by_uuid.start_handle = 0x0001;
    slot->read.by_uuid.end_handle = 0xffff;
    slot->read.by_uuid.uuid = BT_UUID_BAS_BATTERY_LEVEL;

    int rc = bt_gatt_read(conn, &slot->read);
    if (rc != 0) {
        finish_slot((uint8_t)source, false, 0U);
    }
}

static void show_results(void) {
    atomic_val_t valid = atomic_get(&valid_mask);

    nocfree_layer_led_show_battery(
        slots[LEFT_SOURCE].level, (valid & BIT(LEFT_SOURCE)) != 0,
        slots[RIGHT_SOURCE].level, (valid & BIT(RIGHT_SOURCE)) != 0,
        slots[PAD_SOURCE].level, (valid & BIT(PAD_SOURCE)) != 0);
}

static void timeout_work_handler(struct k_work *work) {
    ARG_UNUSED(work);

    if (!atomic_get(&query_active) || !atomic_cas(&displayed, 0, 1)) {
        return;
    }

    /* Pending sides are deliberately shown as unavailable (purple). */
    show_results();

    if (atomic_get(&pending_mask) == 0) {
        atomic_set(&query_active, 0);
    }
}

K_WORK_DELAYABLE_DEFINE(timeout_work, timeout_work_handler);

static void result_work_handler(struct k_work *work) {
    ARG_UNUSED(work);

    (void)k_work_cancel_delayable(&timeout_work);
    show_results();
    atomic_set(&query_active, 0);
}

K_WORK_DEFINE(result_work, result_work_handler);

static void maybe_finish_query(void) {
    if (!atomic_get(&enumeration_complete) || atomic_get(&pending_mask) != 0) {
        return;
    }

    if (atomic_cas(&displayed, 0, 1)) {
        k_work_submit(&result_work);
    } else {
        /* The timeout already displayed the available results. */
        atomic_set(&query_active, 0);
    }
}

static int request_battery_status(void) {
    if (!atomic_cas(&query_active, 0, 1)) {
        return -EBUSY;
    }

    (void)memset(slots, 0, sizeof(slots));
    atomic_set(&enumeration_complete, 0);
    atomic_set(&pending_mask, 0);
    atomic_set(&valid_mask, 0);
    atomic_set(&displayed, 0);

    k_work_reschedule(&timeout_work, QUERY_TIMEOUT);
    bt_conn_foreach(BT_CONN_TYPE_LE, start_query_for_conn, NULL);
    atomic_set(&enumeration_complete, 1);
    maybe_finish_query();
    return 0;
}

static int on_battery_status_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
    ARG_UNUSED(binding);
    ARG_UNUSED(event);

    (void)request_battery_status();
    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_battery_status_released(struct zmk_behavior_binding *binding,
                                      struct zmk_behavior_binding_event event) {
    ARG_UNUSED(binding);
    ARG_UNUSED(event);
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api battery_status_driver_api = {
    .binding_pressed = on_battery_status_pressed,
    .binding_released = on_battery_status_released,
    .locality = BEHAVIOR_LOCALITY_CENTRAL,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .get_parameter_metadata = zmk_behavior_get_empty_param_metadata,
#endif
};

#define BATTERY_STATUS_INST(n)                                                                    \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, NULL, NULL, POST_KERNEL,                               \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,                                  \
                            &battery_status_driver_api);

DT_INST_FOREACH_STATUS_OKAY(BATTERY_STATUS_INST)
