/*
 * SPDX-License-Identifier: MIT
 *
 * Select a Bluetooth host profile and prefer BLE output atomically from the
 * perspective of ZMK's behavior queue. This avoids a profile change
 * interrupting a second behavior queued by a macro.
 */

#define DT_DRV_COMPAT nocfree_behavior_bt_output

#include <errno.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>

#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <zmk/ble.h>
#include <zmk/endpoints.h>

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
static const struct behavior_parameter_value_metadata profile_values[] = {
    {
        .display_name = "Profile",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_RANGE,
        .range = {.min = 0, .max = ZMK_BLE_PROFILE_COUNT - 1},
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

static int on_keymap_binding_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
    (void)event;

    if (binding->param1 >= ZMK_BLE_PROFILE_COUNT) {
        return -EINVAL;
    }

    int err = zmk_ble_prof_select(binding->param1);
    if (err < 0) {
        return err;
    }

    return zmk_endpoint_set_preferred_transport(ZMK_TRANSPORT_BLE);
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
