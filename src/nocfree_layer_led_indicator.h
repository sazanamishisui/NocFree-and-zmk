/*
 * Copyright (c) 2026 The NocFree ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

/*
 * Temporarily replace the normal layer colour with a left/right battery
 * sequence. The layer colour is restored automatically when the sequence
 * finishes.
 */
void nocfree_layer_led_show_battery(uint8_t left_level, bool left_valid,
                                    uint8_t right_level, bool right_valid);
