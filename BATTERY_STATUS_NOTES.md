# NocFree v0.11.0 on-demand battery status with Pad

## Scope

This revision updates the Pad and dongle. It reads the standard Battery Level
characteristic exposed by all three split peripherals. It does not enable
`CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING`, subscribe to battery
notifications, or write any peripheral.

## First build gate

Do not flash until **Validate sources**, **Firmware**, and
**Verify built artifacts** are all green. The authoritative compile test is
GitHub Actions because the local workspace does not contain the complete
ZMK/Zephyr toolchain.

After the build passes, flash `nocfree_and_pad_peripheral.uf2`, then
`nocfree_and_dongle.uf2`. Do not flash a settings-reset image and do not
reflash either keyboard half.

## First test

1. Flash the normal Pad image, then the normal dongle image.
2. Confirm normal left/right/Pad typing and `Fn+U` / `Fn+1` output switching.
3. Press `Fn+Enter` and observe:
   - one white flash, then the left battery colour;
   - two white flashes, then the right battery colour;
   - three white flashes, then the Pad battery colour;
   - return to the current layer colour.
4. Turn the left half off and press `Fn+Enter`. Left should show two purple
   flashes and right should still show a level colour.
5. Restore the left half, turn the right half off, and press `Fn+V` using only
   the left half. Left should show its level colour and right should show two
   purple flashes. This verifies the saved split-slot mapping and the
   left-only diagnostic path.
6. Turn only the Pad off and request status. Its three-marker result should be
   purple while both halves still show their level colours.
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

The dongle performs a BLE GATT one-byte read by characteristic UUID only when
`Fn+Enter` or `Fn+V` is pressed. The Pad uses only the independently verified
P0.04/AIN2 input and briefly asserts P0.31 for each standard battery sample.
The plausible failures are limited to
wrong/unavailable indication, a short BLE transaction delay, or a software
fault in the experimental dongle image.

If typing becomes unstable, restore the released v0.9.1 dongle and Pad images.
No settings-reset image is required.
