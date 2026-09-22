# v0.6.3 Pad two-expander wiring probe

The v0.6.2 live log established that the user's Pad differs from the candidate
public factory firmware previously analysed:

- PCA `0x20` responds and its input bits change with key presses;
- PCA `0x22` responds and its input bits change with key presses; and
- PCA `0x24` consistently returns Zephyr I/O error `-5`.

The production Pad definition is intentionally unchanged in this patch. Only
the temporary standalone USB diagnostic is changed. It now scans every input
bit on `0x20` and `0x22`, assigns each bit a unique printable identifier, and
omits the absent `0x24` device so one missing expander can no longer fail-close
the entire diagnostic scanner.

Identifier mapping:

- `0x20` bits 0-15: `A` through `P`
- `0x22` bits 0-9: `Q` through `Z`
- `0x22` bits 10-15: `1` through `6`

After flashing the diagnostic UF2, turn the Japanese IME off and press the 21
physical Pad keys once each in visual row order. The resulting 21-character
string is the evidence needed to build the final production key map.

The transform uses the literal single-row positions `0` through `31`. This
avoids a preprocessor name collision between ZMK's right-control `RC()` macro
and the matrix-transform coordinate macro when the keymap and extra overlay
are preprocessed together.
