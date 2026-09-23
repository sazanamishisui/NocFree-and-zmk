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
- While hardware VBUS is present, the line remains released so the charging
  circuit owns the indication.
- After VBUS disappears, the probe pulls the line low for three seconds, then
  releases it for three seconds, repeating until USB is reconnected.
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
5. Look for a clear three-seconds/three-seconds alternation. Record which
   physical LED lights and whether it lights during the pull-low phase or the
   released phase.
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

## Build hotfix 01

The first v0.8 upload did not expose ZMK's application include directory to
the module library, so `zmk/usb.h` was not found while compiling the LED probe.
Hotfix 01 adds that include directory only when
`CONFIG_NOCFREE_LOW_BATTERY_LED_PROBE=y`; runtime behavior is unchanged.

## Probe hotfix 02

The first hardware test showed no pulses: the LED extinguished normally after
about ten seconds on USB, then remained continuously lit after USB removal.
The ZMK USB connection state therefore did not provide a reliable physical
VBUS gate for this diagnostic, and the released state itself may correspond to
LED-on on this shared circuit.

Hotfix 02 reads the nRF52833 hardware VBUS-detect bit directly. With VBUS
absent it alternates three seconds of open-drain low and three seconds of
electrical release. This makes both the pin effect and the physical polarity
unambiguous while still never driving the shared line high.
