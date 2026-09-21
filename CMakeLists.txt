# SPDX-License-Identifier: MIT

zephyr_library()

zephyr_library_sources_ifdef(CONFIG_NOCFREE_KSCAN_PCA9555
                             drivers/kscan/kscan_pca9555.c)
zephyr_library_sources_ifdef(CONFIG_NOCFREE_RECOVERY_CDC_1200_TOUCH
                             src/cdc_1200_touch.c)
zephyr_library_sources_ifdef(CONFIG_NOCFREE_PAD_I2C_DIAGNOSTIC
                             src/pad_i2c_diagnostic.c)

# The output router is dongle-only. ZMK's event manager headers are internal
# application headers, so expose that include directory to this module target.
if(CONFIG_SHIELD_NOCFREE_AND_DONGLE)
  zephyr_library_include_directories(${APPLICATION_SOURCE_DIR}/include)
  zephyr_library_sources(src/behavior_bt_output.c)
  zephyr_library_sources(src/layer_led_indicator.c)
endif()
