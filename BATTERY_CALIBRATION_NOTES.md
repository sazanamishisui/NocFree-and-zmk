# v0.7.4 left/right battery calibration

## Evidence

The v0.7.3 standalone ADC probes measured the divider with its active-high
enable both inactive and active. Both halves were tested over USB and while
running from their batteries.

| Half | Divider off | Divider on at AIN2 | Effective 3/2 result |
|---|---:|---:|---:|
| Left | 0 mV | 2.802--2.821 V | 4.203--4.231 V |
| Right | 1--5 mV | 2.788--2.804 V | 4.182--4.206 V |

The keyboards had just been charged and their charge indicators extinguished
quickly. The old `143/120` ratio reported only about 3.33--3.36 V. The effective
`3/2` ratio is consistent with a charged single-cell Li-ion battery and with
the agreement between two independently tested halves.

The factory firmware's ADC conversion is retained as historical evidence for
pin discovery only. Its raw count cannot be inserted into the ZMK calculation
because the ADC reference and gain configuration are not established as being
the same.

## v0.7.4 implementation

- `output-ohms = <2>`
- `full-ohms = <3>`
- AIN2 remains P0.04 on both halves.
- Divider enable remains P0.05 left and P0.31 right, active high.
- The values 2 and 3 express only the measured calibration ratio; they are not
  physical resistor measurements.
- XIAO split-central battery fetching remains disabled because of the pinned
  ZMK source-index bug documented in `BATTERY_DIAGNOSTIC_SAFETY_NOTES.md`.

## First test

Do not flash until all GitHub Actions jobs are green. Flash the normal left and
right peripheral images without a settings reset, then verify ordinary input,
split reconnection, USB/Bluetooth output switching, and layer indication. The
standalone ADC probe images may be used to confirm that `calibrated_mv` is near
4.2 V after charging; they intentionally do not provide normal split input.

Precise percentage calibration should be refined from discharge observations.
This change establishes a plausible voltage scale and does not yet add a
low-battery LED policy.
