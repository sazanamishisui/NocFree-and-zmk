# v0.2.2 patch contents

## Changes from v0.2.1

- Changed each BLE profile macro to explicit press-only activation.
- `OUT_BLE` still runs first, followed by a 100 ms wait and `BT_SEL`.
- This addresses the field-observed v0.2.1 failure where the profile connected
  but the dongle continued sending output to USB.

## Changes from v0.2

- Reordered each BLE profile macro to select BLE output before `BT_SEL`.
- Added a 100 ms inter-action wait; `BT_SEL` remains the final macro action.
- v0.2.1 did not resolve the field-observed USB routing problem; v0.2.2 adds
  explicit press-only activation for the two system behaviors.

## Changes from v0.1

- Added one-step BLE host switching macros on `Fn+1` through `Fn+5`.
- Kept `Fn+U` as the explicit USB output selector.
- Marked Nav, Numpad, Work, and Reserved as ZMK Studio reserve layers.
- Added source validation for the output macros and reserve-layer metadata.

Apply these paths over `electricdoc187/NocFree-and-zmk` branch `jis-studio`.
All listed files are complete files, not fragments.

## Replaced files

- `build.yaml`
- `.github/workflows/build.yml`
- `tests/test_artifacts.py`
- `tests/run.sh`

## New files

- `boards/shields/nocfree_and/Kconfig.shield`
- `boards/shields/nocfree_and/Kconfig.defconfig`
- `boards/shields/nocfree_and/nocfree_and_dongle.conf`
- `boards/shields/nocfree_and/nocfree_and_dongle.overlay`
- `boards/shields/nocfree_and/nocfree_and-layouts.dtsi`
- `boards/shields/nocfree_and/nocfree_and_dongle.keymap`
- `README_DONGLE.md`

## Intentionally unchanged

- `boards/nocfree/nocfree_and/nocfree_and_left_nrf52833_zmk.dts`
- `boards/nocfree/nocfree_and/nocfree_and_right_nrf52833_zmk.dts`
- `drivers/kscan/kscan_pca9555.c`
- NocFree debounce values
- JIS 85-key physical mapping on the two keyboard halves
- NocFree protected flash partition layout
- `config/west.yml` ZMK revision

This minimizes regression risk in the portion of the community firmware that
already has good field reports for chatter and split stability.
