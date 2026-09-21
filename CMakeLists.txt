# SPDX-License-Identifier: MIT

zephyr_library()

zephyr_library_sources_ifdef(CONFIG_NOCFREE_KSCAN_PCA9555
                             drivers/kscan/kscan_pca9555.c)
zephyr_library_sources_ifdef(CONFIG_NOCFREE_RECOVERY_CDC_1200_TOUCH
                             src/cdc_1200_touch.c)

# Compiled for every role, but the implementation is emitted only when the
# dongle keymap enables the matching devicetree behavior node.
zephyr_library_sources(src/behavior_bt_output.c)
