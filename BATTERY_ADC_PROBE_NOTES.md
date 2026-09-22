# v0.7.3 battery ADC probe

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
