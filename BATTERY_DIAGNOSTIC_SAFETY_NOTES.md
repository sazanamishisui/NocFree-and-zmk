# v0.7.2 local battery diagnostic safety correction

## Why the dongle diagnostic was retired

The first diagnostic log contained `peripheral=234`. Valid split slots are
only 0 through 2. In the pinned ZMK source, a non-split BLE disconnection can
produce `-EINVAL` (`-22`), which becomes 234 when stored in an unsigned byte.
The split central then uses that value as a battery-array index without first
checking the range.

The `level=0%` events at power-off are also disconnect sentinels, not ADC
measurements. They must not be used to calibrate either half.

This is a dongle-side software memory-safety problem. It does not assert an
unknown keyboard GPIO and does not indicate electrical damage to the halves.

## Safety changes

- The normal dongle now sets
  `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=n`.
- The unsafe `nocfree_and_dongle_battery_diagnostic` artifact is no longer
  built.
- Separate `nocfree_and_left_battery_diagnostic` and
  `nocfree_and_right_battery_diagnostic` images measure their own local ADC.
- Each local diagnostic is standalone USB-only firmware. It does not use BLE,
  split communication, Studio, or central battery fetching.
- The divider enable GPIO is active only during each sample. The ZMK driver
  waits 10 ms, reads the verified AIN2 input, and disables it again.
- The diagnostic prints one line every five seconds:

  `NOCFREE_LOCAL_BATTERY millivolts=3980 level=70%`

The number above is only an example, not an expected result.

## Immediate action before building v0.7.2

Stop the PowerShell serial capture and flash the released v0.6.5 normal
`nocfree_and_dongle.uf2` to the XIAO. Do not run a settings reset. The left,
right, and Pad may remain on their current firmware.

## Test procedure after all GitHub Actions jobs pass

1. Flash the newly built normal `nocfree_and_dongle.uf2` to the XIAO. Confirm
   left/right/Pad input, `Fn+U`, `Fn+1`, and layer LED operation.
2. Test only one keyboard half at a time.
3. Enter that half's UF2 mode and flash its matching battery diagnostic image.
4. Reconnect its USB cable normally and open the new diagnostic COM port at
   115200 baud.
5. Save the first five lines and another five lines after one or two minutes.
6. Close the COM port, enter UF2 mode, and restore that half's normal
   peripheral image.
7. Confirm the half reconnects to the dongle, then repeat for the other half.

No settings-reset image is needed. While a half has standalone diagnostic
firmware installed, it is expected not to send keys through the dongle.

USB power can charge the battery and raise its voltage. For that reason, the
first readings after connection are especially useful. The raw millivolt
values will show whether the present 120/143 divider ratio is plausible before
any percentage calibration is changed.
