# v0.3.0 patch contents

## Changes in v0.3.2

- Replaced connection-state polling with one non-blocking 750 ms delayed BLE
  output request. The v0.3.1 polling path did not change output in field tests
  even when the selected phone was already connected.
- The delayed callback invokes the same endpoint API used by ZMK's `OUT_BLE`.
- `Fn+U` still cancels a pending switch before selecting USB.

## Changes in v0.3.1

- `Fn+1` through `Fn+5` select a Bluetooth profile, then poll its connection
  state every 100 ms before selecting BLE output.
- The connection wait times out after five seconds and leaves USB selected.
- `Fn+U` now uses the same native behavior with parameter 5, cancelling any
  pending Bluetooth switch before selecting USB.
- A newer profile request replaces an older pending request.

## Changes from v0.2.2 in v0.3.0

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
