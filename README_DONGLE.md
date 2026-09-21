# NocFree & JIS — ZMK USB Dongle prototype v0.3.0

This patch is intended to be applied on top of:

- Repository: `electricdoc187/NocFree-and-zmk`
- Branch: `jis-studio`
- Pinned ZMK revision: `6e2ef41e022d555b10f116e395832913f71717b3`

## Goal

Keep the already-stable NocFree ZMK input path intact while moving the split
central, host USB HID, ZMK Studio, and layer state to a dedicated USB dongle.

```text
NocFree Left  nRF52833 -- BLE peripheral --                                           +-- XIAO nRF52840 -- USB HID -- PC
NocFree Right nRF52833 -- BLE peripheral --/
```

The NocFree halves continue to use their existing PCA9555 scanner and ZMK
debounce settings. No ESB/nRF24L01 path is used.

## Dongle hardware assumed by v0.1

Seeed Studio XIAO nRF52840 / XIAO BLE, built as `xiao_ble//zmk`.

The dongle has no keyboard matrix of its own. `nocfree_and_dongle.overlay`
therefore uses `zmk,kscan-mock` and copies the exact 85-position JIS matrix
transform and physical layout from the JIS branch.

## Layers

The dongle keymap contains six compile-time layers so ZMK Studio has room to
edit them without increasing the nRF52833 workload:

0. Base (same JIS mapping as the source branch)
1. Fn (same behavior as the source branch)
2. Nav (initially transparent)
3. Numpad (initially transparent)
4. Work (initially transparent)
5. Reserved (initially transparent)

The last four are deliberately transparent in v0.1. This keeps first-boot
behavior identical to the existing two-layer firmware; they can be populated
later in ZMK Studio.

## Host output switching in v0.3

The Fn number-row bindings now combine host profile selection and output
routing so a single chord switches the XIAO dongle to the requested BLE host:

- `Fn+1` through `Fn+5`: select Bluetooth profile 1 through 5, then prefer BLE
- `Fn+U`: prefer USB output to the PC or KVM connected to the XIAO
- `Fn+0`: clear the bond for the currently selected Bluetooth profile

The pinned ZMK revision did not reliably apply `OUT_BLE` when output selection
and `BT_SEL` were placed in one queued macro. v0.3 therefore uses a small native
behavior: it selects the requested profile and then selects BLE output inside
the same key-press callback. ZMK persists the selected output route in settings,
so `Fn+U` remains the explicit recovery path back to USB output.

## Important topology change

The source branch defines the left half as split central. v0.1 does **not**
rewrite the NocFree board files. Instead `build.yaml` overrides the left and
right builds with `CONFIG_ZMK_SPLIT_ROLE_CENTRAL=n`, following ZMK's dongle
integration method.

The left build additionally disables ZMK USB HID and explicitly keeps the
existing CDC/1200-baud recovery USB interface initialized. This mirrors the
right-half recovery arrangement while making the dongle the only host-facing
HID device.

## First build gate — do not flash before it is green

1. Overlay these files onto a checkout/fork of the `jis-studio` branch.
2. Push to GitHub.
3. Confirm **Validate sources**, **Firmware**, and **Verify built artifacts**
   all pass.
4. Inspect the produced firmware ZIP for the three normal images and the three
   settings-reset images.

This bundle was statically checked, but it has **not** been compiled in this
ChatGPT environment because the ZMK/Zephyr toolchain and Git dependencies are
not available locally. GitHub Actions is therefore the first authoritative
compile test.

## Pairing / flashing order after CI passes

Changing from left-central to dongle-central changes the split bonding graph.
Old settings must not be reused.

1. Keep the original working firmware files available for rollback.
2. Flash the generated `settings_reset` image to **left**, **right**, and
   **dongle**, one device at a time.
3. Flash `nocfree_and_left_peripheral` to the left half.
4. Flash `nocfree_and_right_peripheral` to the right half.
5. Flash `nocfree_and_dongle` to the XIAO nRF52840.
6. Power-cycle/reset all three devices. If split pairing is slow, reset the
   dongle and both halves close together.
7. Connect the dongle to the PC by USB and verify basic Base/Fn input before
   opening ZMK Studio.

## Initial acceptance tests

Do not judge v0.1 by features. Judge it by stability first:

- Every physical key produces exactly one press and one release.
- No repeated characters during sustained normal typing.
- No phantom key when pressing common 2/3/4-key combinations.
- Turn right half off/on: left remains usable and right reconnects.
- Turn left half off/on: right reconnects independently through dongle.
- Sleep both halves, then test first-key wake repeatedly.
- Unplug/replug the USB dongle and reboot the PC.
- Run prolonged typing before assigning macros or advanced layers.

## Rollback

The original board definitions are intentionally left intact. To return to the
existing JIS left-central firmware, restore the original `build.yaml`, reset
settings on both halves, and flash the original left/right images.
