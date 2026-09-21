#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
#
# Run every automated check. No toolchain or hardware required unless
# NOCFREE_BUILD_DIR is provided.

set -euo pipefail

TESTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CC="${CC:-cc}"
OUT="$(mktemp -d)"
trap 'rm -rf "${OUT}"' EXIT

# Resolve and validate the optional built-artifact directory before unittest
# changes the working directory. Dongle mode requires all four build trees.
if [ -n "${NOCFREE_BUILD_DIR:-}" ]; then
    for role in left right pad dongle; do
        if [ ! -f "${NOCFREE_BUILD_DIR}/${role}/zephyr/.config" ]; then
            echo "NOCFREE_BUILD_DIR=${NOCFREE_BUILD_DIR} has no ${role}/zephyr/.config" >&2
            exit 1
        fi
    done
    NOCFREE_BUILD_DIR="$(cd "${NOCFREE_BUILD_DIR}" && pwd)"
    export NOCFREE_BUILD_DIR
fi

echo "== scanner logic (C) =="
"${CC}" -std=c11 -Wall -Wextra -Werror -O2 \
    -o "${OUT}/test_kscan_scan" "${TESTS}/test_kscan_scan.c"
"${OUT}/test_kscan_scan"

echo
echo "== board, keymap, metadata and hygiene (Python) =="
cd "${TESTS}"
python3 -m unittest discover -s "${TESTS}" -p "test_*.py" -v
