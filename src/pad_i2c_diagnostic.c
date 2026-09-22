/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Read-only periodic PCA9555 report for the standalone Pad USB diagnostic.
 */

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>

LOG_MODULE_REGISTER(nocfree_pad_i2c_diag, CONFIG_ZMK_LOG_LEVEL);

#define PCA9555_INPUT_PORT0 0x00
#define PCA9555_POLARITY_PORT0 0x04
#define PCA9555_CONFIGURATION_PORT0 0x06

#define PCA_SPEC(label) I2C_DT_SPEC_GET(DT_NODELABEL(label))

static const struct i2c_dt_spec expanders[] = {
    PCA_SPEC(pca20),
    PCA_SPEC(pca22),
};

static int read_pair(const struct i2c_dt_spec *spec, uint8_t reg, uint16_t *value) {
    uint8_t bytes[2];
    int err = i2c_write_read_dt(spec, &reg, sizeof(reg), bytes, sizeof(bytes));

    if (err) {
        return err;
    }

    *value = (uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8);
    return 0;
}

static void report_expander(const struct i2c_dt_spec *spec) {
    uint16_t inputs;
    uint16_t polarity;
    uint16_t configuration;

    if (!i2c_is_ready_dt(spec)) {
        LOG_ERR("PCA 0x%02x: I2C controller is not ready", spec->addr);
        return;
    }

    int input_err = read_pair(spec, PCA9555_INPUT_PORT0, &inputs);
    int polarity_err = read_pair(spec, PCA9555_POLARITY_PORT0, &polarity);
    int configuration_err =
        read_pair(spec, PCA9555_CONFIGURATION_PORT0, &configuration);

    if (input_err || polarity_err || configuration_err) {
        LOG_ERR("PCA 0x%02x: read errors input=%d polarity=%d config=%d", spec->addr,
                input_err, polarity_err, configuration_err);
        return;
    }

    LOG_INF("PCA 0x%02x: input=0x%04x polarity=0x%04x config=0x%04x", spec->addr,
            inputs, polarity, configuration);
}

static void diagnostic_work_handler(struct k_work *work);

K_WORK_DELAYABLE_DEFINE(diagnostic_work, diagnostic_work_handler);

static void diagnostic_work_handler(struct k_work *work) {
    ARG_UNUSED(work);

    LOG_INF("NocFree Pad I2C diagnostic sample");
    for (size_t i = 0; i < ARRAY_SIZE(expanders); i++) {
        report_expander(&expanders[i]);
    }

    k_work_schedule(&diagnostic_work, K_SECONDS(2));
}

static int pad_i2c_diagnostic_init(void) {
    k_work_schedule(&diagnostic_work, K_SECONDS(3));
    return 0;
}

SYS_INIT(pad_i2c_diagnostic_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
