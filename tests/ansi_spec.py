# SPDX-License-Identifier: MIT
"""The single source of truth for the NocFree & ANSI key map.

Everything the tests assert about the devicetree, the keymap and the built
artifacts is derived from this file, so a change to the board has to be made
here as well as in the devicetree before the suite will pass.
"""

from __future__ import annotations

# The six logical scan rows, in the port order NocFree publishes:
#   0x20/P0, 0x20/P1, 0x22/P0, 0x22/P1, 0x24/P0, 0x24/P1
# Expander pins 0-7 are port 0 and pins 8-15 are port 1.
ROWS = [
    ("pca20", 0),
    ("pca20", 8),
    ("pca22", 0),
    ("pca22", 8),
    ("pca24", 0),
    ("pca24", 8),
]

EXPANDER_ADDRESSES = {"pca20": 0x20, "pca22": 0x22, "pca24": 0x24}

# Populated inputs per row. These are the key counts of a standard ANSI board
# split between T and Y; every other expander bit is an unpopulated position.
LEFT_COUNTS = [7, 7, 6, 6, 6, 5]
RIGHT_COUNTS = [8, 8, 8, 8, 8, 8]

LEFT_KEYS = sum(LEFT_COUNTS)    # 37
RIGHT_KEYS = sum(RIGHT_COUNTS)  # 48

# NocFree Pad rows from the NocFreeLink layout and factory scanner order.
PAD_COUNTS = [4, 4, 4, 3, 4, 2]
PAD_KEYS = sum(PAD_COUNTS)  # 21

KEYBOARD_KEYS = LEFT_KEYS + RIGHT_KEYS  # 85
TOTAL_KEYS = KEYBOARD_KEYS + PAD_KEYS  # 106

RIGHT_COL_OFFSET = LEFT_KEYS
PAD_COL_OFFSET = KEYBOARD_KEYS

# All sixteen pins of a PCA9555.
ALL_BITS = set(range(16))


def key_inputs(counts: list[int]) -> list[tuple[str, int]]:
    """(expander, bit) for each KSCAN column, in column order."""
    out: list[tuple[str, int]] = []
    for (label, base), count in zip(ROWS, counts):
        out.extend((label, base + i) for i in range(count))
    return out


LEFT_INPUTS = key_inputs(LEFT_COUNTS)
RIGHT_INPUTS = key_inputs(RIGHT_COUNTS)
PAD_INPUTS = key_inputs(PAD_COUNTS)


def unused_bits(counts: list[int]) -> dict[str, set[int]]:
    """Expander bits that must NOT appear in a half's key-inputs list."""
    used: dict[str, set[int]] = {label: set() for label, _ in ROWS}
    for label, bit in key_inputs(counts):
        used[label].add(bit)
    return {label: ALL_BITS - bits for label, bits in used.items()}


LEFT_UNUSED = unused_bits(LEFT_COUNTS)
RIGHT_UNUSED = unused_bits(RIGHT_COUNTS)
PAD_UNUSED = unused_bits(PAD_COUNTS)


def transform_positions() -> list[int]:
    """The transform map, in visual reading order: left row then right row."""
    out: list[int] = []
    left, right = 0, RIGHT_COL_OFFSET
    for lc, rc in zip(LEFT_COUNTS, RIGHT_COUNTS):
        out.extend(range(left, left + lc))
        out.extend(range(right, right + rc))
        left += lc
        right += rc
    return out


KEYBOARD_TRANSFORM = transform_positions()
TRANSFORM = KEYBOARD_TRANSFORM + list(range(PAD_COL_OFFSET, TOTAL_KEYS))

# The default layer, in the same visual order as TRANSFORM. Row boundaries
# follow LEFT_COUNTS/RIGHT_COUNTS.
DEFAULT_LAYER = [
    # Function row
    "kp ESC", "kp F1", "kp F2", "kp F3", "kp F4", "kp F5", "kp F6",
    "kp F7", "kp F8", "kp F9", "kp F10", "kp F11", "kp F12", "kp PSCRN", "kp HOME",

    # Number row
    "kp GRAVE", "kp N1", "kp N2", "kp N3", "kp N4", "kp N5", "kp N6",
    "kp N7", "kp N8", "kp N9", "kp N0", "kp MINUS", "kp EQUAL", "kp INT_YEN", "kp BSPC",

    # Tab row
    "kp TAB", "kp Q", "kp W", "kp E", "kp R", "kp T",
    "kp Y", "kp U", "kp I", "kp O", "kp P", "kp LBKT", "kp RBKT", "kp DEL",

    # Home row
    "kp CAPS", "kp A", "kp S", "kp D", "kp F", "kp G",
    "kp H", "kp J", "kp K", "kp L", "kp SEMI", "kp SQT", "kp BSLH", "kp RET",

    # Shift row
    "kp LSHFT", "kp Z", "kp X", "kp C", "kp V", "kp B",
    "kp N", "kp M", "kp COMMA", "kp DOT", "kp FSLH", "kp INT_RO", "kp RSHFT", "kp UP",

    # Bottom row
    "kp LCTRL", "kp LGUI", "kp LALT", "lt 1 INT_MUHENKAN", "kp SPACE",
    "kp SPACE", "kp INT_HENKAN", "kp RALT", "mo 1", "kp RCTRL", "kp LEFT", "kp DOWN", "kp RIGHT",

]

PAD_DEFAULT_LAYER = [
    "kp KP_NUMLOCK", "kp F3", "kp F4", "kp F7",
    "kp ESC", "kp KP_DIVIDE", "kp KP_MULTIPLY", "kp KP_MINUS",
    "kp KP_N7", "kp KP_N8", "kp KP_N9", "kp KP_PLUS",
    "kp KP_N4", "kp KP_N5", "kp KP_N6",
    "kp KP_N1", "kp KP_N2", "kp KP_N3", "kp KP_ENTER",
    "kp KP_N0", "kp KP_DOT",
]

# Flash geometry, from the two public Adafruit linker scripts. See
# docs/architecture.md for the citation.
PARTITIONS = {
    "sd_partition": (0x00000000, 0x00027000),
    "code_partition": (0x00027000, 0x0003E000),
    "storage_partition": (0x00065000, 0x00008000),
    "boot_partition": (0x00074000, 0x0000C000),
}
READ_ONLY_PARTITIONS = {"sd_partition", "boot_partition"}
FACTORY_FILESYSTEM = (0x0006D000, 0x00074000)
FLASH_END = 0x00080000
