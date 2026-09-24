# Battery ADC probes

## Purpose

The v0.7.2 local diagnostic repeatedly reported approximately 3.3 V on both
halves, including a right half whose charge light extinguished immediately.
That result cannot distinguish a battery-divider conversion error from an ADC
input that is observing the 3.3 V power domain.

This diagnostic measures AIN2 twice per cycle:

1. divider enable inactive, after 100 ms of settling;
2. divider enable active, after the established 10 ms settling delay.

It prints the unscaled ADC count, voltage at the ADC pin, the previous v0.7.2
conversion, and the hardware-calibrated v0.7.4 conversion.

## Safety boundary

- Only the already verified AIN2 input is read.
- Only the already verified divider-enable output is driven: P0.05 on the left
  and P0.31 on the right.
- The divider is forced inactive after every sample and on every error path.
- No lighting, charging, power-latch, or unverified GPIO is touched.
- The probe is standalone USB-only firmware and does not change settings.

## Artifacts

- `nocfree_and_left_battery_adc_probe.uf2`
- `nocfree_and_right_battery_adc_probe.uf2`

Do not flash either artifact until Validate sources, Firmware, and Verify built
artifacts are all green.

## Expected log format

```text
NOCFREE_ADC_PROBE off_raw=12 off_pin_mv=10 on_raw=3200 on_pin_mv=2812 previous_mv=3351 calibrated_mv=4218
```

The numbers above are examples only.

Hardware logs from both halves verified that the divider output falls to
approximately 0 V while disabled and rises to approximately 2.79--2.82 V while
enabled. Immediately after charging, the effective `3/2` conversion produces
approximately 4.18--4.23 V; the previous `143/120` conversion incorrectly
reported approximately 3.33--3.36 V.

The most important comparison is `off_raw` versus `on_raw`:

- large increase when enabled: the enable pin controls the measured divider;
- little or no change: the assumed enable pin or measurement point is wrong;
- correct switching but implausible converted voltage: revise calibration only
  after the raw counts are understood.

For the battery-powered sample, boot the probe with USB attached, close the COM
port, leave the power switch on, unplug USB for 60 seconds, then reconnect USB.
The logging buffer should preserve the measurements taken while USB was absent.
After testing, use the same COM port at 1200 baud and restore the matching
normal peripheral image. A settings reset is not needed.

## Pad verification stage after v0.9.1

`nocfree_and_pad_battery_adc_probe.uf2` extends the same USB-only raw probe to
the Pad, without enabling battery reporting in the normal Pad firmware.

The pin choice is derived independently from both supplied factory images,
`NocFree_and_V2.1.0_Pad.uf2` and `NocFree_and_V2.2.1_Pad.uf2`. In both images:

- the battery helper is initialized with Arduino D15 as its analog input;
- Arduino D16 is configured as the active-high divider control;
- the compiled Pad pin table maps D15 to P0.04/AIN2 and D16 to P0.31.

The diagnostic still requires a hardware confirmation before these pins are
used by normal firmware. Flash only the Pad probe, open its USB COM port, and
capture several `NOCFREE_ADC_PROBE` lines. The expected signature is an
`off_pin_mv` near 0 V and an `on_pin_mv` near 2.7--2.8 V at high charge. Stop
and restore `nocfree_and_pad_peripheral.uf2` if the Pad becomes warm, resets
repeatedly, or the off/on readings do not differ substantially.

After the log is captured, use the Pad COM port at 1200 baud and restore the
normal Pad image. Do not use a settings-reset image; this test does not alter
pairing data.
