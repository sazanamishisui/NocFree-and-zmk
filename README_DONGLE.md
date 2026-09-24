# NocFree & JIS + Pad — ZMK USB Dongle prototype v0.6.0

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
NocFree Pad   nRF52833 -- BLE peripheral --/
```

The NocFree halves continue to use their existing PCA9555 scanner and ZMK
debounce settings. No ESB/nRF24L01 path is used.

## On-demand battery display in v0.9.1

Press `Fn+Enter` or `Fn+V` to make the XIAO read the two keyboard halves'
standard BLE Battery Level characteristics. `Fn+Enter` is convenient in normal
use; `Fn+V` is entirely on the left half and remains available while the right
half is off. This is an on-demand GATT read: the unsafe
continuous split-central battery-fetch option remains disabled. The halves
continue their existing once-per-minute local measurements for their own
low-battery warning, but do not continuously forward values to the dongle.

The XIAO temporarily replaces its layer colour with this sequence:

1. one white flash, then the left level;
2. a short dark gap;
3. two white flashes, then the right level;
4. automatic return to the current layer colour.

Green means 51--100%, yellow 16--50%, red 0--15%, and two purple flashes mean
that the value was unavailable or invalid. A 2.5-second timeout prevents an
unresponsive half from blocking the feature.

The current pairing has been observed as split source 0 = right, source 1 =
left, and source 2 = Pad. v0.9.0 checks every source index before access and
ignores source 2. If the XIAO settings are erased and all peripherals are
paired again in a different order, verify the mapping by powering one half off
at a time before trusting the left/right labels.

Only `nocfree_and_dongle.uf2` needs to be flashed for the first v0.9.1 test.
Keep both halves on their already-tested v0.8.1 normal images. Because Studio
stores keymap overrides in XIAO settings, run **Restore Stock Settings** once
after flashing so both battery shortcuts and the direct-layer bindings receive
the new stock settings.

## Dongle hardware assumed by v0.1

Seeed Studio XIAO nRF52840 / XIAO BLE, built as `xiao_ble//zmk`.

The dongle has no keyboard matrix of its own. `nocfree_and_dongle.overlay`
therefore uses `zmk,kscan-mock` and copies the exact 85-position JIS matrix
transform and extends its physical layout from 85 to 106 positions for the
21-key NocFree Pad.

## NocFree Pad integration in v0.6.0

The Pad is a third BLE split peripheral. It uses the same nRF52833, I2C pins,
three PCA9555 addresses, protected flash layout, debounce values and
1200-baud recovery path as the keyboard halves. The scanner declares only the
21 populated inputs, in six physical rows of 4, 4, 4, 3, 4 and 2 keys.

Keyboard positions 0-84 are unchanged. Pad positions are appended at 85-105,
so existing JIS bindings and the v0.3.3 output-switch listener retain their
position numbers. ZMK Studio displays the Pad to the right of the keyboard and
can edit its bindings on every exposed layer.

The dongle now reserves three split-peripheral bonds plus the existing five
host profiles (`BT_MAX_PAIRED=8`). This does not convert the Pad into an
independent host keyboard: all three input devices still depend on the XIAO
central.

The factory Pad firmware version cannot be identified reliably from
NocFreeLink when another NocFree device has a newer version. The saved UF2
backup remains the rollback reference; updating the factory firmware only to
obtain a version number is unnecessary.

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

- `Fn+N`: move directly to the Nav layer
- `Fn+M`: move directly to the Numpad layer
- `Fn+W`: move directly to the Work layer

These are `To Layer` bindings, so selecting a destination clears the other
non-default layer states. Press `Esc` on any of the three editable layers to
return to Base. Keep each layer's `Esc` binding unchanged while experimenting
in Studio. `Fn+1` through `Fn+5` and `Fn+U` remain reserved for host-output
selection and should not be moved in Studio while the v0.3.3 position-event
output router is in use.

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
unchanged by the indicator itself. Brightness control is intentionally deferred: v0.5.0 first tests
whether the onboard LED is visible and comfortable in normal use.

## Left/right battery reporting in v0.7.0

The two keyboard halves now measure their verified battery dividers and expose
the result over the split BLE Battery Service. Both use `P0.04/AIN2`; the
active-high enable is `P0.05` on the left and `P0.31` on the right. The divider
is inactive at boot and between the default 60-second samples.

The factory firmware established the pinout, but its ADC scaling cannot be
transferred directly to ZMK's differently configured nRF SAADC. v0.7.3 local
probes measured approximately 2.79--2.82 V at AIN2 on both freshly charged
halves. v0.7.4 therefore uses the effective `3/2` full/output calibration ratio,
which produces approximately 4.18--4.23 V. The reduced integers are calibration
values, not a claim about the physical resistor values.

Peripheral battery fetching remains disabled on the XIAO. The pinned ZMK
revision can turn an invalid peripheral lookup into source index 234 and then
write outside its battery array. This is a dongle software/RAM safety issue,
not an electrical measurement issue. A safe low-battery consumer will be added
separately; Pad battery reporting also remains disabled until its exact factory
firmware/hardware revision is confirmed.

### Shared red LED probe in the v0.8 development stage

The factory-derived red charge/low-battery lines are P0.09 on the left and
P0.17 on the right. Because each line is shared with the charging circuit, the
normal firmware still leaves it untouched. The temporary
`nocfree_and_left_low_battery_led_probe.uf2` and
`nocfree_and_right_low_battery_led_probe.uf2` images configure only the
matching line as active-low open drain. They release the line while USB is
present. Probe hotfix 02 uses the nRF52833 hardware VBUS-detect bit and, after
USB removal, alternates three seconds pulled low with three seconds electrically
released. This deliberately slow cycle reveals whether the physical LED is on
in the low or released state.

This stage verifies pin, polarity, visible LED location, and the absence of
charging-circuit contention before any permanent percentage threshold is
enabled. See `LOW_BATTERY_LED_PROBE_NOTES.md` for the test sequence.

### Local low-battery warning in v0.8.1

Both hardware probes passed. The normal left and right images therefore monitor
their own cached ZMK battery level. At 15% or below, the matching red indicator
emits two short pulses once per minute while VBUS is absent. Every phase checks
the nRF52833 hardware VBUS-detect bit; USB power immediately releases the
open-drain line so the charging circuit retains control.

Healthy battery state is event-driven and does not keep an indicator timer
running. The warning does not depend on the XIAO: split-central battery fetching
remains disabled. See `LOW_BATTERY_INDICATOR_NOTES.md` for the exact policy and
first-flash checks.

The upstream XIAO board devicetree already contains its own `vbatt` node. It
therefore remains visible in compiled devicetree output, but this firmware keeps
`CONFIG_ZMK_BATTERY_REPORTING=n` on the dongle, so the node is not sampled or
reported. Artifact tests distinguish that stock XIAO node from the enabled
NocFree left/right circuits instead of incorrectly requiring it to disappear.

### Conservative first battery test

Do not flash until all three GitHub Actions jobs are green. Keep the v0.6.5 and
factory UF2 files available, and do not use a settings-reset image unless a
split device fails to reconnect.

1. Flash the normal v0.7 dongle image, then the normal v0.7 left image only.
2. Confirm left/right/Pad input and USB/Bluetooth output switching, then use the
   keyboard for at least ten minutes. Power the left half off immediately if it
   becomes warm, disconnects repeatedly, or drains unusually quickly.
3. If normal, flash the normal right image and repeat the checks.
4. Leave the Pad on v0.6.5; v0.7 contains no Pad battery node.

An inaccurate percentage is a calibration problem, not evidence of electrical
damage. Use only the local USB diagnostic images described below; the earlier
central diagnostic dongle is retained here for historical reference and must
not be flashed on the pinned ZMK revision.

## Temporary battery diagnostic dongle in v0.7.1

`nocfree_and_dongle_battery_diagnostic.uf2` is a temporary XIAO image. It keeps
the normal dongle behavior and Studio interface, but also enables the existing
USB CDC console and prints each received event in this form:

```text
NOCFREE_BATTERY peripheral=0 level=87%
```

The peripheral number is the dongle's stable split slot, not a hard-coded
left/right name. Open the logging COM port at 115200 baud, then power-cycle the
left and right halves one at a time. Each reconnect causes an initial Battery
Service read, allowing the two slot numbers to be identified. The Pad produces
no battery line in this version because its measurement remains disabled.

Windows may show two XIAO COM ports: one for Studio and one for logging. Opening
the wrong port produces no readable battery line; close it and try the other.
After recording both values, flash the normal `nocfree_and_dongle.uf2` back to
the XIAO. No settings-reset image is needed in either direction.

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

1. Create `v0.7.1-battery-diagnostic` from the all-green
   `v0.7-battery-monitor` branch and apply these files there.
2. Push to GitHub.
3. Confirm **Validate sources**, **Firmware**, and **Verify built artifacts**
   all pass.
4. Inspect the produced firmware ZIP for these ten images:
   - `nocfree_and_left_peripheral.uf2`
   - `nocfree_and_right_peripheral.uf2`
   - `nocfree_and_pad_peripheral.uf2`
   - `nocfree_and_dongle.uf2`
   - `nocfree_and_pad_usb_diagnostic.uf2`
   - `nocfree_and_dongle_battery_diagnostic.uf2`
   - the corresponding four `settings_reset` images

The source checks pass locally, but this environment does not contain the
ZMK/Zephyr build toolchain. GitHub Actions remains the authoritative compile,
link, devicetree and UF2-boundary test.

## First Pad test after CI passes

Preserve the already-working left/right bonds on the first attempt:

1. Keep v0.5.0 and all factory UF2 backups available.
2. Flash `nocfree_and_dongle.uf2` to the XIAO. Do not use its settings-reset
   image yet.
3. On the Pad, hold the physical top-left and top-right keys together for
   about five seconds to open its UF2 drive.
4. Flash `nocfree_and_pad_settings_reset.uf2` to the Pad.
5. The factory five-second chord is no longer active while the reset image is
   running. Use the same 1200-baud serial recovery already verified on the
   keyboard halves to reopen the Pad UF2 drive, then flash
   `nocfree_and_pad_peripheral.uf2`.
6. Power-cycle the Pad, then reconnect the XIAO. Leave the two keyboard halves
   unchanged.
7. Test all 21 Pad keys before opening Studio. The expected Base order is:
   Num Lock/F3/F4/F7; Esc/divide/multiply/minus; 7/8/9/plus; 4/5/6;
   1/2/3/Enter; 0/decimal.

If the Pad does not join, do not immediately erase all devices. First repeat
the Pad settings-reset and normal image. Resetting the XIAO erases its existing
left/right split bonds; if that becomes necessary, reset and reflash all three
peripherals together before testing again.

## Initial acceptance tests

Judge the first v0.6.0 test by stability and correct key mapping first:

- Every keyboard and Pad key produces exactly one press and one release.
- No repeated characters during sustained normal typing.
- No phantom key when pressing common 2/3/4-key combinations.
- Turn right half off/on: left remains usable and right reconnects.
- Turn left half off/on: right reconnects independently through dongle.
- Turn Pad off/on: both keyboard halves remain usable and Pad reconnects.
- Hold a keyboard modifier while pressing Pad keys to verify concurrent input.
- Sleep both halves, then test first-key wake repeatedly.
- Unplug/replug the USB dongle and reboot the PC.
- Run prolonged typing before assigning macros or advanced layers.

## Rollback

To return only the Pad to factory firmware while ZMK is running, use its
1200-baud serial recovery to enter the UF2 drive and copy the saved Pad
`CURRENT.UF2`. After the factory firmware is restored, its top-left +
top-right five-second chord becomes available again. The backup covers the
SoftDevice and application regions used for normal rollback; the preserved
UF2 bootloader is not overwritten by this ZMK build.

To return the complete keyboard to the original topology, retain the existing
v0.5.0 release and the previously saved factory left/right/dongle images. Avoid
using any settings-reset image unless its corresponding normal image and
rollback file are already available.
