# v0.1 patch contents

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
