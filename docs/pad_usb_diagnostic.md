# NocFree Pad standalone USB and I2C diagnostic

`nocfree_and_pad_usb_diagnostic.uf2` is a temporary fault-isolation image. It
reads the Pad's three PCA9555 expanders using the same scanner as the normal
split-peripheral image, but sends key events directly to the PC over USB HID.
BLE and split operation are disabled in this image.

The v0.6.2 variant also emits a read-only PCA9555 register report over the
same USB CDC port used for 1200-baud recovery. Open that COM port at 115200
baud to capture the report.

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
5. Open a text editor, press the Pad's top-left Num Lock key once, then test all
   21 keys.
6. Record whether any key produces input and whether each physical key matches
   the expected symbol.

The expected physical order is:

| Row | Left to right |
| --- | --- |
| 1 | Num Lock, F3, F4, F7 |
| 2 | Esc, divide, multiply, minus |
| 3 | 7, 8, 9, plus |
| 4 | 4, 5, 6 |
| 5 | 1, 2, 3, Enter |
| 6 | 0, decimal |
