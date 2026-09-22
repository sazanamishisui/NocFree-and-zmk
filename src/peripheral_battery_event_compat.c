/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 */

#include <zephyr/sys/util.h>

#include <zmk/events/battery_state_changed.h>

/*
 * The pinned ZMK revision emits this event when a split central fetches a
 * peripheral Battery Service, but compiles the event implementation only when
 * the central also reports its own battery. A USB dongle has no local battery,
 * so provide only the missing peripheral event implementation here.
 *
 * Keep the reporting guard to avoid a duplicate definition if a future dongle
 * gains a real battery or the upstream build condition is corrected.
 */
#if IS_ENABLED(CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING) &&                       \
    !IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING)
ZMK_EVENT_IMPL(zmk_peripheral_battery_state_changed);
#endif
