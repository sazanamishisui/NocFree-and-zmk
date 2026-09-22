/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Read the battery divider on one NocFree half and print the local voltage.
 * This deliberately avoids the split-central battery subscription path.
 */

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(nocfree_local_battery_diagnostic, LOG_LEVEL_INF);

#define BATTERY_NODE DT_CHOSEN(zmk_battery)

static const struct device *const battery = DEVICE_DT_GET(BATTERY_NODE);

static void local_battery_diagnostic_work(struct k_work *work) {
    struct k_work_delayable *delayable = k_work_delayable_from_work(work);

    struct sensor_value voltage;
    struct sensor_value state_of_charge;
    int rc = sensor_sample_fetch_chan(battery, SENSOR_CHAN_GAUGE_VOLTAGE);

    if (rc != 0) {
        LOG_ERR("NOCFREE_LOCAL_BATTERY sample_error=%d", rc);
        goto reschedule;
    }

    rc = sensor_channel_get(battery, SENSOR_CHAN_GAUGE_VOLTAGE, &voltage);
    if (rc != 0) {
        LOG_ERR("NOCFREE_LOCAL_BATTERY voltage_error=%d", rc);
        goto reschedule;
    }

    rc = sensor_channel_get(battery, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE,
                            &state_of_charge);
    if (rc != 0) {
        LOG_ERR("NOCFREE_LOCAL_BATTERY level_error=%d", rc);
        goto reschedule;
    }

    const int32_t millivolts = voltage.val1 * 1000 + voltage.val2 / 1000;
    LOG_INF("NOCFREE_LOCAL_BATTERY millivolts=%d level=%d%%", millivolts,
            state_of_charge.val1);

reschedule:
    k_work_reschedule(delayable, K_SECONDS(5));
}

K_WORK_DELAYABLE_DEFINE(local_battery_diagnostic,
                        local_battery_diagnostic_work);

static int local_battery_diagnostic_init(void) {
    if (!device_is_ready(battery)) {
        LOG_ERR("NOCFREE_LOCAL_BATTERY device_not_ready");
        return -ENODEV;
    }

    /* Leave time for the USB CDC logging port to enumerate. */
    k_work_schedule(&local_battery_diagnostic, K_SECONDS(3));
    return 0;
}

SYS_INIT(local_battery_diagnostic_init, APPLICATION,
         CONFIG_APPLICATION_INIT_PRIORITY);
