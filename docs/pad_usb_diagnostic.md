# NocFree Pad standalone USB and I2C diagnostic

`nocfree_and_pad_usb_diagnostic.uf2` is a temporary fault-isolation image. It
uses the same scanner as the normal split-peripheral image, but sends key
events directly to the PC over USB HID. BLE and split operation are disabled
in this image.

The v0.6.2 variant also emits a read-only PCA9555 register report over the
same USB CDC port used for 1200-baud recovery. Open that COM port at 115200
baud to capture the report.

That capture showed valid key changes at addresses `0x20` and `0x22`, while
`0x24` consistently returned I/O error `-5`. The v0.6.3 wiring-probe variant
therefore scans all 16 inputs of each live expander and no longer requires the
absent `0x24` device.

This answers one narrow question without changing the working keyboard halves
or the dongle's stored bonds:

- If the Pad types over USB, its I2C bus, expander addresses, key map and scan
  driver work. The remaining fault is in BLE split discovery/pairing.
- If the Pad does not type over USB, investigate the Pad I2C pins, expander
  addresses and input-bit map before changing any BLE settings.

## Safety

- Do not flash a settings-reset image for this test.
- Do not change the left, right or dongle firmware.
- The diagnostic UF2 uses the same protected nRF52833 application partition as
  the normal Pad image and retains the 1200-baud CDC recovery path.
- After the test, use the Pad's COM port at 1200 baud to enter UF2 mode and
  restore `nocfree_and_pad_peripheral.uf2`.

## Test

1. Connect the Pad to the PC with a data-capable USB cable.
2. Enter UF2 mode through the existing 1200-baud CDC recovery interface.
3. Copy `nocfree_and_pad_usb_diagnostic.uf2` to the UF2 drive.
4. Wait for the drive to disappear and for USB to re-enumerate.
5. Turn the Japanese IME off and open a text editor.
6. Press all 21 physical keys once in the row order below, left to right.
7. Preserve the resulting 21-character string exactly. It identifies the
   actual expander bit used by each physical key.

The probe emits these identifiers:

| Electrical input | Text output |
| --- | --- |
| PCA `0x20`, bits 0-15 | `A` through `P` |
| PCA `0x22`, bits 0-9 | `Q` through `Z` |
| PCA `0x22`, bits 10-15 | `1` through `6` |

Press the physical keys in this order:

| Row | Left to right |
| --- | --- |
| 1 | Num Lock, F3, F4, F7 |
| 2 | Esc, divide, multiply, minus |
| 3 | 7, 8, 9, plus |
| 4 | 4, 5, 6 |
| 5 | 1, 2, 3, Enter |
| 6 | 0, decimal |
