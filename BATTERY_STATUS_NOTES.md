# NocFree v0.9.0 on-demand battery status

## Scope

This change is dongle-only. It reads the standard Battery Level characteristic
already exposed by the normal v0.8.1 left and right images. It does not enable
`CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING`, subscribe to battery
notifications, write either half, or alter the Pad.

## First build gate

Do not flash until **Validate sources**, **Firmware**, and
**Verify built artifacts** are all green. The authoritative compile test is
GitHub Actions because the local workspace does not contain the complete
ZMK/Zephyr toolchain.

After the build passes, use only `nocfree_and_dongle.uf2` for the first test.
Do not flash a settings-reset image and do not reflash either keyboard half.

## First test

1. Flash `nocfree_and_dongle.uf2` to the XIAO.
2. Open ZMK Studio and run **Restore Stock Settings** once. This is necessary
   because the saved Studio keymap can otherwise leave `Fn+Enter` transparent.
3. Confirm normal left/right/Pad typing and `Fn+U` / `Fn+1` output switching.
4. Press `Fn+Enter` and observe:
   - one white flash, then the left battery colour;
   - two white flashes, then the right battery colour;
   - return to the current layer colour.
5. Turn the left half off and press `Fn+Enter`. Left should show two purple
   flashes and right should still show a level colour.
6. Restore left, then repeat with only the right half off. This verifies the
   saved split-slot mapping as well as the unavailable-data path.
7. With everything on, type quickly across both halves and the Pad immediately
   before, during, and after a battery request. There should be no stuck,
   repeated, or missing key.

## Colours

- green: 51--100%
- yellow: 16--50%
- red: 0--15%
- two purple flashes: disconnected, timed out, missing Battery Service, or
  invalid value

## Risk and rollback

The new code performs a BLE GATT one-byte read by characteristic UUID only when
`Fn+Enter` is pressed. It never drives a keyboard-half GPIO and therefore adds
no electrical or charging-circuit risk. The plausible failures are limited to
wrong/unavailable indication, a short BLE transaction delay, or a software
fault in the experimental dongle image.

If typing becomes unstable, unplug the XIAO and flash the released v0.8.1-era
dongle UF2. The left, right, and Pad images and their settings do not need to be
changed.
