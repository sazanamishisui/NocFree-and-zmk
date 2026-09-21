# NocFree & JIS — ZMK USB Dongle prototype v0.5.0

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

## Host output switching in v0.3.3

The Fn number-row uses Studio-compatible stock profile bindings. A separate
position-event listener handles output routing so a single chord switches the
XIAO dongle to the requested BLE host even when Studio has retained its
dynamic keymap:

- `Fn+1` through `Fn+5`: use stock `BT_SEL` for Bluetooth profile 1 through 5;
  the event listener then prefers BLE after a 750 ms non-blocking delay
- `Fn+U`: cancel any pending BLE switch and prefer USB output to the PC or KVM
  connected to the XIAO
- `Fn+0`: clear the bond for the currently selected Bluetooth profile

The pinned ZMK revision did not reliably apply `OUT_BLE` when output selection
and `BT_SEL` were placed in one queued macro. v0.3.0 also showed that selecting
BLE immediately after changing profiles can occur before the new profile is
ready. The connection-state polling attempted in v0.3.1 and the custom-key
delayed switch in v0.3.2 did not trigger the output change in field tests.
v0.3.3 observes the physical Fn profile keys independently of Studio's dynamic
binding, schedules the same 750 ms output request, and keeps `Fn+U` as the
explicit recovery and cancellation path.

## Editable layers in v0.4.1

ZMK Studio exposes three initially transparent layers for user editing:

- `Fn+N`: toggle the Nav layer
- `Fn+M`: toggle the Numpad layer
- `Fn+W`: toggle the Work layer

Press the same chord again to return to Base. Because these are toggle layers,
verify the active layer before typing sensitive text. Press `Esc` on any of the
three editable layers for an emergency return to Base. Keep each layer's `Esc`
binding unchanged while experimenting in Studio. `Fn+1` through `Fn+5` and
`Fn+U` remain reserved for host-output selection and should not be moved in
Studio while the v0.3.3 position-event output router is in use.

The dongle build explicitly supplies this shield keymap through CMake's
`KEYMAP_FILE`. This prevents the original two-layer NocFree config keymap from
silently taking priority. Artifact verification also checks the compiled
devicetree for all five editable layer names.

## XIAO RGB layer indicator in v0.5.0

The XIAO nRF52840 dongle's onboard active-low RGB LED shows the highest active
ZMK layer. This keeps layer indication on the USB-powered central and does not
consume either keyboard half's battery.

| Layer | LED |
| --- | --- |
| Base | Off |
| Fn | Blue while Fn is held |
| Nav | Green |
| Numpad | Red |
| Work | Purple (red + blue) |
| Future or unexpected layer | White |

The implementation uses the XIAO board's Zephyr devicetree LED aliases rather
than hard-coded GPIO polarity. It is compiled only for
`CONFIG_SHIELD_NOCFREE_AND_DONGLE`; the left and right firmware images are
unchanged. Brightness control is intentionally deferred: v0.5.0 first tests
whether the onboard LED is visible and comfortable in normal use.

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

1. Overlay these files onto the `v0.5-led-indicator` branch created from the
   tested v0.4.1 source.
2. Push to GitHub.
3. Confirm **Validate sources**, **Firmware**, and **Verify built artifacts**
   all pass.
4. Inspect the produced firmware ZIP for the three normal images and the three
   settings-reset images.

This bundle was statically checked, but it has **not** been compiled in this
ChatGPT environment because the ZMK/Zephyr toolchain and Git dependencies are
not available locally. GitHub Actions is therefore the first authoritative
compile test.

For an existing working v0.4.1 installation, flash only
`nocfree_and_dongle.uf2` to the XIAO. Do not flash a settings-reset image and
do not rewrite either keyboard half; the pairing and Studio settings should
remain intact.

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
