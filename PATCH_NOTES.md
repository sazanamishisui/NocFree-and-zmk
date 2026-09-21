# v0.3.0 patch contents

## Changes from v0.2.2

- Replaced the five queued BLE macros with one native `bt_out` behavior.
- The behavior calls profile selection and BLE output selection inside the same
  key-press callback, so profile switching cannot interrupt a later queued
  macro action.
- Added the behavior driver, devicetree binding, and module build entry.
- `Fn+1` through `Fn+5` now bind directly to `&bt_out 0` through `&bt_out 4`.

v0.2, v0.2.1, and v0.2.2 all confirmed that `BT_SEL` worked while the queued
`OUT_BLE` action did not reliably change the selected transport. v0.3.0 no
longer uses a macro for this operation.

Apply these complete files over the current `v0.2-keymap-studio` branch.

## Replaced files

- `CMakeLists.txt`
- `tests/test_artifacts.py`
- `boards/shields/nocfree_and/nocfree_and_dongle.keymap`
- `README_DONGLE.md`
- `PATCH_NOTES.md`

## New files

- `dts/bindings/behaviors/nocfree,behavior-bt-output.yaml`
- `src/behavior_bt_output.c`

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
