# v0.6.1 Pad USB diagnostic patch

This patch adds one temporary firmware artifact:

`nocfree_and_pad_usb_diagnostic.uf2`

It runs the NocFree Pad as a standalone USB HID keyboard with BLE and split
operation disabled. The normal Pad image, dongle image, keyboard-half images
and every settings-reset image are unchanged.

Upload the patch files over the matching paths in the existing v0.6 branch,
then wait for all three GitHub Actions jobs to pass. The Firmware ZIP should
contain nine UF2 files. Do not flash the diagnostic image until its built UF2
has been inspected.

The source tests verify that the diagnostic build:

- enables USB HID;
- disables BLE and split operation;
- retains the PCA9555 scanner and 1200-baud recovery;
- remains inside the preserved nRF52833 application partition; and
- uses the nRF52833 UF2 family ID.

See `docs/pad_usb_diagnostic.md` for the eventual test and restoration steps.
