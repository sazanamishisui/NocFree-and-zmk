# v0.6.2 Pad I2C logging diagnostic patch

The v0.6.1 standalone USB diagnostic enumerated successfully but produced no
key input. This patch keeps that USB-only diagnostic and adds a read-only log
of the Pad's three PCA9555-compatible I2C expanders.

Every two seconds the diagnostic reports, for addresses `0x20`, `0x22`, and
`0x24`:

- whether the I2C controller is ready;
- both input-port bytes;
- both polarity-register bytes;
- both configuration-register bytes; and
- the exact Zephyr error code if a register read fails.

The report uses the Pad's existing USB CDC recovery port. It does not write
additional expander registers, erase settings, or alter the normal left,
right, Pad-peripheral, dongle, or settings-reset images.

Upload this patch over the matching paths on a new branch based on the
v0.6.1 diagnostic branch. Wait for Validate sources, Firmware, and Verify
built artifacts to pass, then inspect the Firmware ZIP before flashing.

After flashing `nocfree_and_pad_usb_diagnostic.uf2`, open the Pad's COM port
at 115200 baud and capture at least one idle report followed by reports while
pressing several different Pad keys. The input words should change if the I2C
bus and key wiring are being read successfully.
