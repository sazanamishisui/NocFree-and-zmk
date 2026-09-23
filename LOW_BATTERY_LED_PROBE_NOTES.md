# v0.8 shared red low-battery LED probe

## Purpose

Verify the factory-derived shared red indicator pins before implementing a
permanent low-battery warning:

- left: P0.09;
- right: P0.17.

The same line is also used by the charging circuit. The diagnostic therefore
uses active-low open-drain mode: it may pull the line low, but it cannot
actively drive it high.

## Safety behavior

- Initial state is electrically released.
- While USB is present, the line remains released so the charging circuit owns
  the indication.
- After USB disconnects, the probe produces two 180 ms pulses separated by
  220 ms, then waits five seconds.
- Battery measurement, BLE, split communication, and settings changes are
  disabled in the diagnostic image.
- The normal left/right images declare the pin metadata but do not configure
  or drive the pin at this stage.

## Artifacts

- `nocfree_and_left_low_battery_led_probe.uf2`
- `nocfree_and_right_low_battery_led_probe.uf2`

Do not flash until Validate sources, Firmware, and Verify built artifacts are
all green.

## Test one half at a time

1. Keep the matching normal peripheral UF2 available for restoration.
2. Set the half's power switch ON and flash its matching LED probe over USB.
3. Leave USB connected for at least ten seconds. The shared red indicator must
   not be commanded by the probe during this interval; ordinary charge-state
   behavior may remain visible.
4. Unplug USB without switching the half off.
5. Look for two short red pulses every five seconds. Record which physical LED
   lights and whether the cadence is clearly visible.
6. Reconnect USB. Probe-generated double pulses must stop within one second.
7. Use the CDC port at 1200 baud and restore the matching normal peripheral
   image. A settings reset is not needed.
8. Repeat on the other half only after the first has behaved as expected.

Stop the test and restore the normal image if an LED stays continuously lit
after USB removal, USB reconnection does not stop the pulses, the keyboard
becomes warm, or charging behavior changes unexpectedly.

## Next gate

Only after both halves pass will normal firmware subscribe to each half's local
battery state and request the same open-drain pulse below a conservative
threshold. XIAO split-central battery fetching remains disabled.
