# v0.6.4 Pad USB HID activation fix

The v0.6.2 boot log exposed two independent faults:

1. the production Pad definition incorrectly required a non-responding
   expander at `0x24`; and
2. the standalone diagnostic inherited
   `CONFIG_USB_DEVICE_INITIALIZE_AT_BOOT=y` from the peripheral board while
   also enabling `CONFIG_ZMK_USB=y`.

The first fault was isolated by the v0.6.3 two-expander wiring probe. This
patch fixes the second fault for that diagnostic only. It explicitly disables
Zephyr's automatic USB start and lets ZMK enable the composite USB device once.
The CDC console and 1200-baud recovery interface remain compiled into the same
device and are started together with USB HID by ZMK.

The expected boot log must no longer contain:

```text
USB device support already enabled
Unable to enable USB
```

Normal left, right, Pad-peripheral, dongle and settings-reset builds are not
changed by this diagnostic-only CMake override.
