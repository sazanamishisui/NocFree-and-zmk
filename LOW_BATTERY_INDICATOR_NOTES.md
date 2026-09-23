# v0.8.1 local low-battery warning

## Policy

Each keyboard half monitors only its own local ZMK battery state:

- threshold: 15% or below;
- pattern: 180 ms on, 220 ms off, 180 ms on;
- repeat interval: one minute;
- left indicator: P0.09;
- right indicator: P0.17;
- electrical mode: active-low open drain;
- USB behavior: electrically released whenever hardware VBUS is present.

The warning subscribes to `zmk_battery_state_changed`. A single delayed startup
check reads ZMK's cached level after five seconds, covering the case where the
level did not generate a new event. No periodic indicator work remains scheduled
while the battery is above 15%.

## Scope and safety boundary

- The left and right probe tests verified the pin, visible red LED, low/release
  behavior, and VBUS gating on real hardware.
- The code never actively drives the shared charge-indicator line high.
- The charging circuit owns the line whenever USB power is present.
- The XIAO does not fetch peripheral battery levels.
- The Pad is excluded because its battery and indicator wiring are not verified.
- This feature does not control charging and does not change pairing settings.

## First normal-firmware test

Do not flash until Validate sources, Firmware, and Verify built artifacts are
all green. Flash one normal peripheral at a time without a settings reset.

At the currently charged level, no low-battery pulses should occur. Verify
ordinary keys, cross-half modifiers, Pad input, split reconnection,
USB/Bluetooth output switching, and the XIAO layer indicator. Connect USB to the
updated half and confirm that its normal charge indication remains unchanged.

The 15% warning will be validated naturally as each half discharges. If a red
double pulse appears much earlier than expected, capture a local battery
diagnostic before changing the threshold or conversion curve.
