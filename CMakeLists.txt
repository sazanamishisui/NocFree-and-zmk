# SPDX-License-Identifier: MIT

zephyr_library()

zephyr_library_sources_ifdef(CONFIG_NOCFREE_KSCAN_PCA9555
                             drivers/kscan/kscan_pca9555.c)
zephyr_library_sources_ifdef(CONFIG_NOCFREE_RECOVERY_CDC_1200_TOUCH
                             src/cdc_1200_touch.c)
zephyr_library_sources_ifdef(CONFIG_NOCFREE_PAD_I2C_DIAGNOSTIC
                             src/pad_i2c_diagnostic.c)
zephyr_library_sources_ifdef(CONFIG_NOCFREE_LOCAL_BATTERY_DIAGNOSTIC
                             src/local_battery_diagnostic.c)
zephyr_library_sources_ifdef(CONFIG_NOCFREE_BATTERY_ADC_PROBE
                             src/battery_adc_probe.c)

if(CONFIG_NOCFREE_LOW_BATTERY_LED_PROBE)
  zephyr_library_sources(src/low_battery_led_probe.c)
endif()

# The output router is dongle-only. ZMK's event manager headers are internal
# application headers, so expose that include directory to this module target.
if(CONFIG_SHIELD_NOCFREE_AND_DONGLE)
  zephyr_library_include_directories(${APPLICATION_SOURCE_DIR}/include)
  zephyr_library_sources(src/behavior_bt_output.c)
  zephyr_library_sources(src/layer_led_indicator.c)
  zephyr_library_sources_ifdef(
    CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING
    src/peripheral_battery_event_compat.c)
  zephyr_library_sources_ifdef(CONFIG_NOCFREE_BATTERY_DIAGNOSTIC
                               src/battery_diagnostic.c)
endif()
