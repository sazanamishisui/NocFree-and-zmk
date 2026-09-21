/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Select a Bluetooth host profile and switch output to BLE after a short,
 * non-blocking delay. Parameter ZMK_BLE_PROFILE_COUNT selects USB and cancels
 * any pending BLE switch.
 */

#define DT_DRV_COMPAT nocfree_behavior_bt_output

#include <errno.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <zmk/ble.h>
#include <zmk/endpoints.h>

#define BLE_OUTPUT_SWITCH_DELAY_MS 750
#define USB_OUTPUT_PARAM ZMK_BLE_PROFILE_COUNT

static bool ble_output_pending;
static uint8_t pending_profile;

static void ble_output_work_handler(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(ble_output_work, ble_output_work_handler);

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
static const struct behavior_parameter_value_metadata profile_values[] = {
    {
        .value = 0,
        .display_name = "BLE Profile 1",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
    {
        .value = 1,
        .display_name = "BLE Profile 2",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
    {
        .value = 2,
        .display_name = "BLE Profile 3",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
    {
        .value = 3,
        .display_name = "BLE Profile 4",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
    {
        .value = 4,
        .display_name = "BLE Profile 5",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
    {
        .value = USB_OUTPUT_PARAM,
        .display_name = "USB Output",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
};

static const struct behavior_parameter_metadata_set profile_set = {
    .param1_values = profile_values,
    .param1_values_len = ARRAY_SIZE(profile_values),
};

static const struct behavior_parameter_metadata metadata = {
    .sets_len = 1,
    .sets = &profile_set,
};
#endif /* IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA) */

static void cancel_pending_ble_output(void) {
    ble_output_pending = false;
    (void)k_work_cancel_delayable(&ble_output_work);
}

static void ble_output_work_handler(struct k_work *work) {
    (void)work;

    if (!ble_output_pending) {
        return;
    }

    /* A later profile-selection request supersedes this one. */
    if (zmk_ble_active_profile_index() != pending_profile) {
        ble_output_pending = false;
        return;
    }

    ble_output_pending = false;
    (void)zmk_endpoint_set_preferred_transport(ZMK_TRANSPORT_BLE);
}

static int on_keymap_binding_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
    (void)event;

    if (binding->param1 == USB_OUTPUT_PARAM) {
        cancel_pending_ble_output();
        return zmk_endpoint_set_preferred_transport(ZMK_TRANSPORT_USB);
    }

    if (binding->param1 > ZMK_BLE_PROFILE_COUNT) {
        return -EINVAL;
    }

    cancel_pending_ble_output();

    int err = zmk_ble_prof_select(binding->param1);
    if (err < 0) {
        return err;
    }

    /*
     * Keep USB selected while the requested BLE host connects. This prevents
     * reports leaking to the previous BLE host and gives Fn+U an immediate,
     * deterministic cancellation path.
     */
    err = zmk_endpoint_set_preferred_transport(ZMK_TRANSPORT_USB);
    if (err < 0) {
        return err;
    }

    pending_profile = binding->param1;
    ble_output_pending = true;
    (void)k_work_reschedule(&ble_output_work, K_MSEC(BLE_OUTPUT_SWITCH_DELAY_MS));
    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_keymap_binding_released(struct zmk_behavior_binding *binding,
                                      struct zmk_behavior_binding_event event) {
    (void)binding;
    (void)event;
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api behavior_bt_output_driver_api = {
    .binding_pressed = on_keymap_binding_pressed,
    .binding_released = on_keymap_binding_released,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .parameter_metadata = &metadata,
#endif
};

BEHAVIOR_DT_INST_DEFINE(0, NULL, NULL, NULL, NULL, POST_KERNEL,
                        CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,
                        &behavior_bt_output_driver_api);

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
