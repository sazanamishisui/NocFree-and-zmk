# v0.9.0 on-demand dongle battery display patch contents

## Changes in v0.9.0

- Added a dongle-local `Battery Status` behavior and assigned it to
  `Fn+Enter` in the stock Fn layer.
- The XIAO reads each keyboard half's standard BLE Battery Level
  characteristic only after that chord is pressed. Continuous ZMK split
  battery fetching stays disabled.
- Restricts reads to the currently verified split slots: source 0 is right and
  source 1 is left. All connection roles, slot indices, payload lengths, and
  percentage values are checked before use; the Pad and host BLE links are
  ignored.
- Displays one white marker followed by the left level, then two white markers
  followed by the right level. Green is 51--100%, yellow is 16--50%, red is
  0--15%, and two purple flashes mean unavailable or invalid data.
- Restores the current layer colour automatically after the sequence, even if
  the active layer changed while battery status was displayed.
- Adds a 2.5-second timeout. A silent or disconnected half becomes purple
  rather than blocking keyboard input or displaying an old percentage.
- Does not change either keyboard half, its ADC/divider control, local
  low-battery warning, Pad firmware, scanner, debounce, pairing settings, or
  USB/Bluetooth output routing.

# v0.8.1 local low-battery indicator patch contents

## Changes in v0.8.1

- Added a normal-firmware low-battery indicator independently to the left and
  right keyboard halves; each consumes only its own local ZMK battery state.
- At 15% or below, the matching red LED emits two 180 ms pulses separated by
  220 ms, repeating once per minute while running from battery.
- Uses the verified active-low open-drain pins: P0.09 left and P0.17 right.
- Reads the nRF52833 hardware VBUS-detect bit before every pulse phase. While
  USB power is present, the pin is released and the charging circuit owns it.
- Uses battery state events while healthy, so no periodic indicator timer runs
  continuously at normal charge. A single five-second startup check covers an
  unchanged cached battery value.
- Kept XIAO split-central battery fetching disabled. The Pad remains excluded
  because its battery measurement and indicator circuit are not verified.
- Did not change scanners, split links, Studio, keymap, output switching,
  pairing data, XIAO layer RGB, sleep policy, or charging control.

# v0.8 low-battery LED probe patch contents

## Changes in v0.8 probe stage

- Added standalone left/right probe images for the shared red
  charge/low-battery indicator.
- Declared the factory-derived pins as active-low open-drain only: P0.09 left
  and P0.17 right. The normal firmware does not configure or drive them yet.
- The probe starts with the line electrically released, continues releasing it
  while USB is present, and double-blinks only after USB disconnects.
- The probe never actively drives the shared line high, avoiding contention
  with the keyboard charging circuit.
- Disabled BLE, split operation, battery sampling, and settings changes in the
  two diagnostic images.
- Added source and built-artifact checks for GPIO mode, USB gating, link-map
  isolation, flash bounds, and the two exact pins.
- Did not enable the final percentage threshold or permanent warning policy;
  those follow only after both physical LEDs are verified.
- Probe hotfix 02 replaces ZMK logical USB-state gating with the nRF52833
  hardware VBUS-detect bit and uses a clear three-second low/release cycle.

# v0.7.4 battery calibration patch contents

## Changes in v0.7.4

- Replaced the provisional `143/120` left/right voltage conversion with an
  effective `3/2` full/output ratio derived from v0.7.3 measurements.
- Verified both halves independently: the disabled divider measured about
  0 V, while the enabled AIN2 input measured about 2.79--2.82 V immediately
  after charging. The new ratio converts those values to about 4.18--4.23 V.
- Updated the standalone ADC probes to print both `previous_mv` and
  `calibrated_mv`, avoiding the invalid comparison of raw counts from
  differently configured ADC implementations.
- Kept the verified pinout unchanged: P0.04/AIN2 on both halves, with
  active-high enable on P0.05 left and P0.31 right.
- Kept the divider disabled at boot, between samples, and on probe error paths.
- Kept unsafe split-central battery fetching disabled on the XIAO dongle.
- Did not alter the key scanners, debounce, split links, Pad, keymap, Studio,
  USB/Bluetooth output switching, layer LED, pairing data, or sleep policy.

# v0.7.1 diagnostic patch contents

## Changes in v0.7.1

- Added a separate `nocfree_and_dongle_battery_diagnostic.uf2` image.
- The diagnostic dongle retains the normal keymap, ZMK Studio, USB/Bluetooth
  switching and layer LED while enabling USB CDC logging temporarily.
- Uses ZMK's user-configurable minimal-logging mode so unrelated debug traffic
  is suppressed while the dedicated battery module remains at INFO level.
- Added a dongle-only event listener that prints the split source index and
  received percentage as `NOCFREE_BATTERY peripheral=N level=P%`.
- Kept logging and the diagnostic listener disabled in the normal dongle image.
- Added source and built-artifact checks requiring the diagnostic listener in
  the diagnostic map file and forbidding it in the normal dongle map file.
- No keyboard-half, Pad, ADC, divider, charge, keymap or pairing setting was
  changed.

# v0.7.0 patch contents

## Changes in v0.7.0

- Enabled battery measurement and BLE Battery Service reporting on the left
  and right keyboard halves only.
- Reproduced the factory v2.4.5 pinout: both halves sample `P0.04/AIN2`; the
  active-high divider enable is `P0.05` on the left and `P0.31` on the right.
- Matched the factory firmware's verified 4290 mV full-scale conversion with
  an effective `143/120` ZMK calibration (ZMK's SAADC base is 3600 mV).
  The reduced devicetree values express only that ratio and do not claim the
  physical resistor values.
- Kept the divider disabled at boot and between samples. ZMK's voltage-divider
  driver enables it only for a sample, waits 10 ms, reads the ADC, then disables
  it again even when the ADC read fails.
- Enabled peripheral Battery Service fetching on the XIAO dongle so later
  low-battery indication can consume left/right battery events.
- Added a dongle-only compatibility event definition for the pinned ZMK
  revision. That revision calls the peripheral-battery event while fetching,
  but otherwise links its implementation only when the central reports a local
  battery; the USB-powered XIAO intentionally has no local battery source.
- Updated artifact checks to distinguish the dormant VBAT divider built into
  the upstream XIAO board definition from the two enabled NocFree dividers.
- Deliberately left Pad battery reporting disabled until its exact factory
  firmware/hardware revision is confirmed.
- Did not alter the XIAO layer LED, keymap, scanner, debounce, output switching,
  deep-sleep policy or charge-status pins.

# v0.6.0 patch contents

## Changes in v0.6.0

- Added `nocfree_and_pad/nrf52833/zmk` as a third BLE split peripheral.
- Reused the proven nRF52833 flash protection, CDC 1200-baud recovery,
  internal-RC clock, 1M-PHY link margin and PCA9555 scanner configuration.
- Declared the Pad's 21 populated PCA9555 inputs as six rows containing
  4, 4, 4, 3, 4 and 2 keys; unpopulated expander bits remain excluded.
- Preserved all keyboard positions 0-84 and appended Pad positions 85-105.
- Expanded the dongle transform, physical Studio layout and all six keymap
  layers from 85 to 106 positions.
- Added the factory-equivalent Pad Base bindings: Num Lock/F3/F4/F7,
  Esc/divide/multiply/minus, 7/8/9/plus, 4/5/6, 1/2/3/Enter and 0/decimal.
- Increased the dongle split count from two to three peripherals and reserved
  eight bonds: three split devices plus five host profiles.
- Added normal and settings-reset Pad images. The Firmware ZIP should now
  contain four normal images and four settings-reset images.
- Documented that the factory top-left + top-right DFU chord is available only
  before ZMK is flashed; subsequent DFU entry uses the retained 1200-baud CDC
  recovery path.
- Extended source and built-artifact checks to the Pad key map, transform,
  flash boundaries, nRF52833 UF2 family, recovery code and BLE role.
- Left the stable left/right scanners, debounce values, Bluetooth output
  switcher and XIAO RGB indicator unchanged.

## Changes in v0.5.0

- Added a dongle-only layer indicator using the XIAO nRF52840 onboard RGB LED.
- The indicator follows the highest active ZMK layer, including momentary Fn
  and the three Studio-editable toggle layers.
- Color map: Base off, Fn blue, Nav green, Numpad red, Work purple, and any
  future or unexpected layer white.
- Uses the Zephyr board's `led0`, `led1`, and `led2` devicetree aliases, so the
  XIAO active-low LED wiring is handled by the GPIO API instead of hard-coded
  polarity logic.
- Added source and built-link-map checks. The new object must be present in the
  dongle image and absent from both keyboard-half images.
- Preserved the v0.3.3 USB/Bluetooth output router and v0.4.1 five-layer
  keymap without modification.

## Changes in v0.4.1

- Explicitly passes the dongle shield keymap through `KEYMAP_FILE` in both the
  firmware matrix and the artifact-verification build.
- This fixes the field-observed case where the two-layer
  `config/nocfree_and.keymap` took priority over the dongle's five editable
  layers.
- Added a built-devicetree test requiring Base, Fn, Nav, Numpad, and Work in
  the actual dongle image, preventing another source-versus-build mismatch.

## Changes in v0.4.0

- Exposed the previously reserved `Nav`, `Numpad`, and `Work` layers to ZMK
  Studio. Their initial bindings remain transparent, so enabling the layers
  does not change normal typing until the user edits them.
- Added tap-to-toggle access from the Fn layer:
  - `Fn+N`: toggle Nav (layer 2)
  - `Fn+M`: toggle Numpad (layer 3)
  - `Fn+W`: toggle Work (layer 4)
- Assigned `Esc` on each editable layer to `&to 0` as an emergency return to
  Base. This prevents a Studio edit from leaving the user stuck on a layer.
- Kept layer 5 hidden as `Reserved` for future expansion.
- Preserved the v0.3.3 USB/Bluetooth output router without modification.

## Changes in v0.3.3

- Restored the Studio-compatible stock bindings on `Fn+1` through `Fn+5`:
  `&bt BT_SEL 0` through `&bt BT_SEL 4`.
- Replaced the custom key behavior with a position-event listener. When one of
  those five physical keys is pressed while Fn is active, the listener waits
  750 ms and then requests BLE output.
- `Fn+U` uses stock `&out OUT_USB`; the listener also cancels any pending BLE
  request at that position.
- This addresses field evidence that Studio continued to execute its saved
  standard Bluetooth binding instead of the custom `bt_out` binding.

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

Apply these complete files over the `v0.6-numpad-integration` branch created
from the released v0.5.0 source.

## Replaced files

- `.github/workflows/build.yml`
- `build.yaml`
- `boards/nocfree/nocfree_and/board.yml`
- `boards/nocfree/nocfree_and/nocfree_and.zmk.yml`
- `boards/nocfree/nocfree_and/Kconfig.defconfig`
- `boards/nocfree/nocfree_and/Kconfig.nocfree_and_pad`
- `boards/nocfree/nocfree_and/nocfree_and_pad.keymap`
- `boards/nocfree/nocfree_and/nocfree_and_pad_nrf52833_zmk.dts`
- `boards/nocfree/nocfree_and/nocfree_and_pad_nrf52833_zmk_defconfig`
- `boards/shields/nocfree_and/Kconfig.defconfig`
- `boards/shields/nocfree_and/nocfree_and-layouts.dtsi`
- `boards/shields/nocfree_and/nocfree_and_dongle.overlay`
- `boards/shields/nocfree_and/nocfree_and_dongle.keymap`
- `tests/ansi_spec.py`
- `tests/run.sh`
- `tests/test_board_definition.py`
- `tests/test_artifacts.py`
- `README_DONGLE.md`
- `PATCH_NOTES.md`

## Existing supporting files (may remain in the repository)

- `dts/bindings/behaviors/nocfree,behavior-bt-output.yaml`
- `src/behavior_bt_output.c`
- `src/layer_led_indicator.c`
- `CMakeLists.txt`

## Intentionally unchanged

- `boards/nocfree/nocfree_and/nocfree_and_left_nrf52833_zmk.dts`
- `boards/nocfree/nocfree_and/nocfree_and_right_nrf52833_zmk.dts`
- `boards/nocfree/nocfree_and/nocfree_and_left_nrf52833_zmk_defconfig`
- `boards/nocfree/nocfree_and/nocfree_and_right_nrf52833_zmk_defconfig`
- `drivers/kscan/kscan_pca9555.c`
- NocFree debounce values
- JIS 85-key physical mapping on the two keyboard halves
- NocFree protected flash partition layout
- `config/west.yml` ZMK revision

This minimizes regression risk in the portion of the community firmware that
already has good field reports for chatter and split stability.
