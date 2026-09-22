# v0.6.5 verified Pad production wiring

The v0.6.2 I2C log and v0.6.3/v0.6.4 standalone USB wiring probe established
the exact 21-key circuit of the user's NocFree Pad.

Physical rows and electrical inputs:

| Row | Physical keys | Expander inputs |
| --- | --- | --- |
| 1 | Num Lock, F3, F4, F7 | `0x20` bits 0-3 |
| 2 | Esc, divide, multiply, minus | `0x20` bits 4-7 |
| 3 | 7, 8, 9, plus | `0x20` bits 8-11 |
| 4 | 4, 5, 6 | `0x20` bits 12-14 |
| 5 | 1, 2, 3, Enter | `0x22` bits 0-3 |
| 6 | 0, decimal | `0x22` bits 4-5 |

`0x20` bit 15 and `0x22` bits 6-15 are unpopulated. No device responds at
`0x24` on this Pad.

This patch applies that verified mapping to the normal BLE Pad peripheral.
The 106-position dongle keymap, Pad Base bindings, left/right images, dongle
image, flash layout, recovery path and diagnostic wiring probe are unchanged.
