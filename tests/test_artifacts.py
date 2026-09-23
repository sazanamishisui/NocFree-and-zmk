#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Inspect built firmware for three NocFree peripherals and USB dongle.

Point NOCFREE_BUILD_DIR at a directory containing `left/`, `right/`, `pad/`
and `dongle/` build trees, or accept the default used by GitHub Actions.
"""

from __future__ import annotations

import os
import re
import struct
import unittest
from pathlib import Path

import ansi_spec as spec

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD = ROOT.parent / "nocfree-and-zmk-build" / "build"
BUILD = Path(os.environ.get("NOCFREE_BUILD_DIR", DEFAULT_BUILD))

UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
UF2_FLAG_FAMILY_ID = 0x00002000
UF2_BLOCK = 512

CODE_START, CODE_SIZE = spec.PARTITIONS["code_partition"]
CODE_END = CODE_START + CODE_SIZE

KEYMAP = ROOT / "boards" / "shields" / "nocfree_and" / "nocfree_and_dongle.keymap"
BUILD_MATRIX = ROOT / "build.yaml"
WORKFLOW = ROOT / ".github" / "workflows" / "build.yml"
PAD_DTS = ROOT / "boards" / "nocfree" / "nocfree_and" / "nocfree_and_pad_nrf52833_zmk.dts"
PAD_KEYMAP = ROOT / "boards" / "nocfree" / "nocfree_and" / "nocfree_and_pad.keymap"
PAD_DIAG_KEYMAP = (
    ROOT
    / "boards"
    / "nocfree"
    / "nocfree_and"
    / "pad_usb_diag.keymap"
)
PAD_DIAG_OVERLAY = (
    ROOT / "boards" / "nocfree" / "nocfree_and" / "pad_usb_diag.overlay"
)
PAD_DIAG_SOURCE = ROOT / "src" / "pad_i2c_diagnostic.c"
BATTERY_ADC_PROBE_SOURCE = ROOT / "src" / "battery_adc_probe.c"
BATTERY_DIAG_OVERLAY = (
    ROOT / "boards" / "nocfree" / "nocfree_and" / "battery_diag.overlay"
)
LED_PROBE_SOURCE = ROOT / "src" / "low_battery_led_probe.c"
LOW_BATTERY_INDICATOR_SOURCE = ROOT / "src" / "low_battery_indicator.c"
LED_PROBE_OVERLAY = (
    ROOT
    / "boards"
    / "nocfree"
    / "nocfree_and"
    / "led_probe.overlay"
)


class SourceConfigurationTest(unittest.TestCase):
    def test_pad_sources_and_build_entries_exist(self):
        self.assertTrue(PAD_DTS.is_file())
        self.assertTrue(PAD_KEYMAP.is_file())
        self.assertTrue(PAD_DIAG_KEYMAP.is_file())
        self.assertTrue(PAD_DIAG_OVERLAY.is_file())
        self.assertTrue(PAD_DIAG_SOURCE.is_file())

        matrix = BUILD_MATRIX.read_text()
        for artifact in (
            "nocfree_and_left_peripheral",
            "nocfree_and_right_peripheral",
            "nocfree_and_pad_peripheral",
            "nocfree_and_pad_usb_diagnostic",
            "nocfree_and_dongle",
            "nocfree_and_left_battery_adc_probe",
            "nocfree_and_right_battery_adc_probe",
            "nocfree_and_left_low_battery_led_probe",
            "nocfree_and_right_low_battery_led_probe",
            "nocfree_and_left_settings_reset",
            "nocfree_and_right_settings_reset",
            "nocfree_and_pad_settings_reset",
            "nocfree_and_dongle_settings_reset",
        ):
            with self.subTest(artifact):
                self.assertIn(f"artifact-name: {artifact}", matrix)

        pad = PAD_DTS.read_text()
        self.assertIn("col-offset = <85>", pad)
        self.assertEqual(len(re.findall(r"<&pca(?:20|22|24)\s+\d+>", pad)), 21)
        self.assertIn("expanders = <&pca20>, <&pca22>;", pad)
        self.assertNotRegex(pad, r"<&pca24\s+\d+>")

        keymap = PAD_KEYMAP.read_text()
        bindings = re.search(r"bindings\s*=\s*<(.*?)>;", keymap, re.S)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(re.findall(r"&\w+", bindings.group(1))), 106)

        diagnostic = PAD_DIAG_KEYMAP.read_text()
        diagnostic_bindings = re.search(r"bindings\s*=\s*<(.*?)>;", diagnostic, re.S)
        self.assertIsNotNone(diagnostic_bindings)
        self.assertEqual(len(re.findall(r"&kp\s+\w+", diagnostic_bindings.group(1))), 32)
        self.assertIn("&kp A", diagnostic_bindings.group(1))
        self.assertIn("&kp N6", diagnostic_bindings.group(1))

        overlay = PAD_DIAG_OVERLAY.read_text()
        self.assertIn("zephyr,console = &cdc_acm_uart0", overlay)

        source = PAD_DIAG_SOURCE.read_text()
        for required in (
            "PCA_SPEC(pca20)",
            "PCA_SPEC(pca22)",
            "PCA9555_INPUT_PORT0",
            "PCA9555_POLARITY_PORT0",
            "PCA9555_CONFIGURATION_PORT0",
            "K_SECONDS(2)",
        ):
            with self.subTest(required):
                self.assertIn(required, source)

        cmake = (ROOT / "CMakeLists.txt").read_text()
        self.assertIn("CONFIG_NOCFREE_PAD_I2C_DIAGNOSTIC", cmake)
        self.assertIn("src/pad_i2c_diagnostic.c", cmake)

    def test_ble_profile_keys_use_stock_bindings_and_event_router(self):
        text = KEYMAP.read_text()
        self.assertIn(
            "&trans &bt BT_SEL 0 &bt BT_SEL 1 &bt BT_SEL 2 "
            "&bt BT_SEL 3 &bt BT_SEL 4 &studio_unlock",
            text,
        )
        self.assertIn("&trans &out OUT_USB", text)
        self.assertNotIn("&bt_out", text)

        source = (ROOT / "src" / "behavior_bt_output.c").read_text()
        self.assertIn("zmk_position_state_changed", source)
        self.assertIn("zmk_keymap_layer_active(FN_LAYER)", source)
        self.assertIn("POSITION_FN_1 16", source)
        self.assertIn("POSITION_FN_5 20", source)
        self.assertIn("POSITION_FN_U 37", source)
        self.assertIn("K_WORK_DELAYABLE_DEFINE", source)
        self.assertIn("k_work_reschedule", source)
        self.assertIn("BLE_OUTPUT_SWITCH_DELAY_MS 750", source)
        self.assertIn("cancel_pending_ble_output", source)
        self.assertIn("ZMK_TRANSPORT_BLE", source)
        self.assertIn("ZMK_TRANSPORT_USB", source)
        self.assertIn("ZMK_LISTENER", source)
        self.assertIn("ZMK_SUBSCRIPTION", source)

        cmake = (ROOT / "CMakeLists.txt").read_text()
        self.assertIn("if(CONFIG_SHIELD_NOCFREE_AND_DONGLE)", cmake)
        self.assertIn("${APPLICATION_SOURCE_DIR}/include", cmake)
        self.assertIn("src/behavior_bt_output.c", cmake)

    def test_low_battery_led_probes_are_open_drain_and_usb_gated(self):
        self.assertTrue(LED_PROBE_SOURCE.is_file())
        self.assertTrue(LED_PROBE_OVERLAY.is_file())

        source = LED_PROBE_SOURCE.read_text()
        self.assertIn("GPIO_OUTPUT_INACTIVE", source)
        self.assertIn("NRF_POWER->USBREGSTATUS", source)
        self.assertIn("POWER_USBREGSTATUS_VBUSDETECT_Msk", source)
        self.assertNotIn("zmk_usb_get_conn_state()", source)
        self.assertIn("gpio_pin_set_dt(&indicator, 1)", source)
        self.assertIn("gpio_pin_set_dt(&indicator, 0)", source)
        self.assertNotIn("GPIO_OUTPUT_ACTIVE", source)
        self.assertIn("PHASE_TICKS 12", source)
        self.assertIn("PROBE_TICK_MS 250", source)

        overlay = LED_PROBE_OVERLAY.read_text()
        self.assertIn("zephyr,console = &cdc_acm_uart0", overlay)
        self.assertRegex(overlay, r"&vbatt\s*\{\s*status = \"disabled\";")

        matrix = BUILD_MATRIX.read_text()
        workflow = WORKFLOW.read_text()
        for side in ("left", "right"):
            artifact = f"nocfree_and_{side}_low_battery_led_probe"
            build_dir = f"/tmp/ws/build/{side}_low_battery_led_probe"
            self.assertIn(f"artifact-name: {artifact}", matrix)
            self.assertIn(build_dir, workflow)
        self.assertEqual(
            matrix.count("CONFIG_NOCFREE_LOW_BATTERY_LED_PROBE=y"), 2
        )
        self.assertEqual(
            workflow.count("CONFIG_NOCFREE_LOW_BATTERY_LED_PROBE=y"), 2
        )

        cmake = (ROOT / "CMakeLists.txt").read_text()
        self.assertIn("CONFIG_NOCFREE_LOW_BATTERY_LED_PROBE", cmake)
        self.assertIn("src/low_battery_led_probe.c", cmake)

    def test_normal_halves_use_local_low_battery_events(self):
        self.assertTrue(LOW_BATTERY_INDICATOR_SOURCE.is_file())
        source = LOW_BATTERY_INDICATOR_SOURCE.read_text()

        for required in (
            "LOW_BATTERY_THRESHOLD 15",
            "WARNING_REPEAT_DELAY K_MINUTES(1)",
            "WARNING_ON_TIME K_MSEC(180)",
            "WARNING_GAP_TIME K_MSEC(220)",
            "NRF_POWER->USBREGSTATUS",
            "POWER_USBREGSTATUS_VBUSDETECT_Msk",
            "zmk_battery_state_of_charge()",
            "as_zmk_battery_state_changed",
            "ZMK_SUBSCRIPTION",
            "GPIO_OUTPUT_INACTIVE",
            "gpio_pin_set_dt(&indicator, 1)",
            "gpio_pin_set_dt(&indicator, 0)",
        ):
            with self.subTest(required):
                self.assertIn(required, source)

        self.assertNotIn("GPIO_OUTPUT_ACTIVE", source)
        self.assertNotIn("zmk_peripheral_battery_state_changed", source)

        kconfig = (ROOT / "Kconfig").read_text()
        block = re.search(
            r"config NOCFREE_LOW_BATTERY_INDICATOR(.*?)(?=\nconfig |\Z)",
            kconfig,
            re.S,
        )
        self.assertIsNotNone(block)
        self.assertIn("depends on ZMK_BATTERY_REPORTING", block.group(1))
        self.assertIn(
            "depends on DT_HAS_NOCFREE_OPEN_DRAIN_INDICATOR_ENABLED",
            block.group(1),
        )

        cmake = (ROOT / "CMakeLists.txt").read_text()
        indicator_block = re.search(
            r"if\(CONFIG_NOCFREE_LOW_BATTERY_INDICATOR\)(.*?)endif\(\)",
            cmake,
            re.S,
        )
        self.assertIsNotNone(indicator_block)
        self.assertIn(
            "${APPLICATION_SOURCE_DIR}/include", indicator_block.group(1)
        )
        self.assertIn(
            "src/low_battery_indicator.c", indicator_block.group(1)
        )

    def test_xiao_rgb_layer_indicator_is_dongle_only(self):
        source = (ROOT / "src" / "layer_led_indicator.c").read_text()
        self.assertIn("GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios)", source)
        self.assertIn("GPIO_DT_SPEC_GET(DT_ALIAS(led1), gpios)", source)
        self.assertIn("GPIO_DT_SPEC_GET(DT_ALIAS(led2), gpios)", source)
        self.assertIn("zmk_keymap_highest_layer_active()", source)
        self.assertIn("zmk_keymap_layer_index_to_id(highest)", source)
        self.assertIn("as_zmk_layer_state_changed", source)
        self.assertIn("ZMK_SUBSCRIPTION", source)
        self.assertIn("case FN_LAYER", source)
        self.assertIn("case NAV_LAYER", source)
        self.assertIn("case NUMPAD_LAYER", source)
        self.assertIn("case WORK_LAYER", source)

        cmake = (ROOT / "CMakeLists.txt").read_text()
        dongle_block = re.search(
            r"if\(CONFIG_SHIELD_NOCFREE_AND_DONGLE\)(.*?)endif\(\)",
            cmake,
            re.S,
        )
        self.assertIsNotNone(dongle_block)
        self.assertIn("src/layer_led_indicator.c", dongle_block.group(1))

    def test_dongle_defines_the_missing_peripheral_battery_event(self):
        source = (ROOT / "src" / "peripheral_battery_event_compat.c").read_text()
        self.assertIn(
            "ZMK_EVENT_IMPL(zmk_peripheral_battery_state_changed)", source
        )
        self.assertIn(
            "CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING", source
        )
        self.assertIn("!IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING)", source)

        cmake = (ROOT / "CMakeLists.txt").read_text()
        dongle_block = re.search(
            r"if\(CONFIG_SHIELD_NOCFREE_AND_DONGLE\)(.*?)endif\(\)",
            cmake,
            re.S,
        )
        self.assertIsNotNone(dongle_block)
        self.assertIn(
            "src/peripheral_battery_event_compat.c", dongle_block.group(1)
        )

    def test_battery_adc_probes_compare_divider_off_and_on(self):
        source = BATTERY_ADC_PROBE_SOURCE.read_text()
        self.assertIn("adc_read", source)
        self.assertIn("gpio_pin_set_dt(&divider_enable, 0)", source)
        self.assertIn("gpio_pin_set_dt(&divider_enable, 1)", source)
        self.assertIn("off_raw=%d off_pin_mv=%d", source)
        self.assertIn("on_raw=%d on_pin_mv=%d", source)
        self.assertIn("previous_mv=%d calibrated_mv=%d", source)
        self.assertIn("on_pin_mv * 3) / 2", source)
        self.assertIn("K_SECONDS(5)", source)

        kconfig = (ROOT / "Kconfig").read_text()
        self.assertIn("config NOCFREE_BATTERY_ADC_PROBE", kconfig)
        self.assertIn("depends on ADC", kconfig)
        self.assertIn("depends on GPIO", kconfig)

        cmake = (ROOT / "CMakeLists.txt").read_text()
        self.assertIn("CONFIG_NOCFREE_BATTERY_ADC_PROBE", cmake)
        self.assertIn("src/battery_adc_probe.c", cmake)

        matrix = BUILD_MATRIX.read_text()
        for side in ("left", "right"):
            self.assertIn(
                f"artifact-name: nocfree_and_{side}_battery_adc_probe", matrix
            )
        self.assertEqual(
            matrix.count("CONFIG_NOCFREE_BATTERY_ADC_PROBE=y"), 2
        )
        self.assertEqual(matrix.count("CONFIG_ZMK_BATTERY_REPORTING=n"), 4)
        self.assertEqual(matrix.count("CONFIG_ADC=y"), 2)
        self.assertNotIn("artifact-name: nocfree_and_dongle_battery_diagnostic", matrix)
        self.assertTrue(BATTERY_DIAG_OVERLAY.is_file())
        overlay = BATTERY_DIAG_OVERLAY.read_text()
        self.assertIn("zephyr,console = &cdc_acm_uart0", overlay)
        self.assertRegex(overlay, r"&vbatt\s*\{\s*status = \"disabled\";")

        workflow = WORKFLOW.read_text()
        self.assertIn("/tmp/ws/build/left_battery_adc_probe", workflow)
        self.assertIn("/tmp/ws/build/right_battery_adc_probe", workflow)
        self.assertNotIn("/tmp/ws/build/dongle_battery_diagnostic", workflow)
        self.assertEqual(
            workflow.count("CONFIG_NOCFREE_BATTERY_ADC_PROBE=y"), 2
        )

    def test_editable_studio_layers_and_toggle_keys_exist(self):
        text = KEYMAP.read_text()
        for layer in ("navigation_layer", "numpad_layer", "work_layer"):
            with self.subTest(layer=layer):
                node = re.search(rf"{layer}\s*\{{(.*?)\n\s*\}};", text, re.S)
                self.assertIsNotNone(node)
                self.assertNotIn('status = "reserved";', node.group(1))

        reserved = re.search(r"reserved_layer\s*\{(.*?)\n\s*\};", text, re.S)
        self.assertIsNotNone(reserved)
        self.assertIn('status = "reserved";', reserved.group(1))
        self.assertIn("&trans &trans &tog 4 &trans &trans &trans", text)
        self.assertIn("&tog 2 &tog 3 &trans &trans", text)
        self.assertGreaterEqual(text.count("&to 0 &trans"), 3)

    def test_dongle_build_explicitly_selects_its_keymap(self):
        expected = (
            "-DKEYMAP_FILE=${GITHUB_WORKSPACE}/boards/shields/"
            "nocfree_and/nocfree_and_dongle.keymap"
        )
        self.assertIn(expected, BUILD_MATRIX.read_text())
        workflow = WORKFLOW.read_text()
        self.assertIn(
            'dongle_keymap="${GITHUB_WORKSPACE}/boards/shields/nocfree_and/"',
            workflow,
        )
        self.assertIn(
            'dongle_keymap="${dongle_keymap}nocfree_and_dongle.keymap"',
            workflow,
        )
        self.assertIn('-DKEYMAP_FILE="${dongle_keymap}"', workflow)

    def test_pad_build_explicitly_selects_its_keymap(self):
        expected = (
            "-DKEYMAP_FILE=${GITHUB_WORKSPACE}/boards/nocfree/nocfree_and/"
            "nocfree_and_pad.keymap"
        )
        self.assertGreaterEqual(BUILD_MATRIX.read_text().count(expected), 2)
        workflow = WORKFLOW.read_text()
        self.assertIn(
            'pad_keymap="${GITHUB_WORKSPACE}/boards/nocfree/nocfree_and/"',
            workflow,
        )
        self.assertIn('pad_keymap="${pad_keymap}nocfree_and_pad.keymap"', workflow)
        self.assertIn('-DKEYMAP_FILE="${pad_keymap}"', workflow)
        self.assertIn(
            "pad_usb_diag.keymap", BUILD_MATRIX.read_text()
        )
        self.assertIn(
            'pad_diag_keymap="${pad_diag_keymap}pad_usb_diag.keymap"',
            workflow,
        )
        self.assertIn('-DKEYMAP_FILE="${pad_diag_keymap}"', workflow)
        self.assertIn("CONFIG_ZMK_USB_LOGGING=y", BUILD_MATRIX.read_text())
        self.assertIn(
            "-DCONFIG_USB_DEVICE_INITIALIZE_AT_BOOT=n", BUILD_MATRIX.read_text()
        )
        self.assertIn(
            "CONFIG_NOCFREE_PAD_I2C_DIAGNOSTIC=y", BUILD_MATRIX.read_text()
        )
        self.assertIn("pad_usb_diag.overlay", BUILD_MATRIX.read_text())
        self.assertIn("CONFIG_ZMK_USB_LOGGING=y", workflow)
        self.assertIn("-DCONFIG_USB_DEVICE_INITIALIZE_AT_BOOT=n", workflow)
        self.assertIn("CONFIG_NOCFREE_PAD_I2C_DIAGNOSTIC=y", workflow)
        self.assertIn('-DEXTRA_DTC_OVERLAY_FILE="${pad_diag_overlay}"', workflow)

    def test_usb_wiring_probe_scans_two_live_expanders_and_all_bits(self):
        overlay = PAD_DIAG_OVERLAY.read_text()
        self.assertNotIn("RC(", overlay)
        diagnostic = re.search(r"&kscan0\s*\{(.*?)\n\};", overlay, re.S)
        self.assertIsNotNone(diagnostic)
        self.assertIn("expanders = <&pca20>, <&pca22>;", diagnostic.group(1))
        self.assertNotIn("pca24", diagnostic.group(1))
        inputs = re.findall(r"<&pca(?:20|22)\s+\d+>", diagnostic.group(1))
        self.assertEqual(len(inputs), 32)

        keymap = PAD_DIAG_KEYMAP.read_text()
        bindings = re.search(r"bindings\s*=\s*<(.*?)>;", keymap, re.S)
        self.assertIsNotNone(bindings)
        self.assertEqual(len(re.findall(r"&kp\s+\w+", bindings.group(1))), 32)

        source = PAD_DIAG_SOURCE.read_text()
        reporters = re.search(r"expanders\[\]\s*=\s*\{(.*?)\};", source, re.S)
        self.assertIsNotNone(reporters)
        self.assertIn("PCA_SPEC(pca20)", reporters.group(1))
        self.assertIn("PCA_SPEC(pca22)", reporters.group(1))
        self.assertNotIn("PCA_SPEC(pca24)", reporters.group(1))


def role_dir(role: str) -> Path:
    return BUILD / role / "zephyr"


def available() -> bool:
    return all(
        (role_dir(role) / ".config").is_file()
        for role in ("left", "right", "pad", "dongle")
    )


def diagnostic_available() -> bool:
    return (role_dir("pad_usb_diagnostic") / ".config").is_file()


def battery_adc_probes_available() -> bool:
    return all(
        (role_dir(f"{side}_battery_adc_probe") / ".config").is_file()
        for side in ("left", "right")
    )


def low_battery_led_probes_available() -> bool:
    return all(
        (role_dir(f"{side}_low_battery_led_probe") / ".config").is_file()
        for side in ("left", "right")
    )


def kconfig(role: str) -> dict[str, str]:
    out = {}
    for line in (role_dir(role) / ".config").read_text().splitlines():
        match = re.match(r"(CONFIG_\w+)=(.*)", line)
        if match:
            out[match.group(1)] = match.group(2)
    return out


def uf2_blocks(path: Path):
    raw = path.read_bytes()
    assert len(raw) % UF2_BLOCK == 0, f"{path} is not a whole number of UF2 blocks"
    for offset in range(0, len(raw), UF2_BLOCK):
        block = raw[offset : offset + UF2_BLOCK]
        start0, start1, flags, address, payload, _index, _total, family = struct.unpack(
            "<IIIIIIII", block[:32]
        )
        (end,) = struct.unpack("<I", block[508:512])
        yield {
            "start0": start0,
            "start1": start1,
            "flags": flags,
            "address": address,
            "payload": payload,
            "family": family,
            "end": end,
        }


@unittest.skipUnless(available(), f"no complete dongle build output under {BUILD}")
class ArtifactTest(unittest.TestCase):
    PERIPHERALS = ("left", "right", "pad")
    ROLES = ("left", "right", "pad", "dongle")

    def test_scanner_is_compiled_into_all_peripherals(self):
        for role in self.PERIPHERALS:
            config = kconfig(role)
            with self.subTest(role):
                self.assertEqual(config.get("CONFIG_NOCFREE_KSCAN_PCA9555"), "y")
                self.assertEqual(config.get("CONFIG_ZMK_KSCAN"), "y")
                self.assertEqual(config.get("CONFIG_I2C"), "y")

    def test_split_roles_are_correct(self):
        left, right, pad, dongle = (kconfig(r) for r in self.ROLES)
        for config in (left, right, pad, dongle):
            self.assertEqual(config.get("CONFIG_ZMK_SPLIT"), "y")
        self.assertNotEqual(left.get("CONFIG_ZMK_SPLIT_ROLE_CENTRAL"), "y")
        self.assertNotEqual(right.get("CONFIG_ZMK_SPLIT_ROLE_CENTRAL"), "y")
        self.assertNotEqual(pad.get("CONFIG_ZMK_SPLIT_ROLE_CENTRAL"), "y")
        self.assertEqual(dongle.get("CONFIG_ZMK_SPLIT_ROLE_CENTRAL"), "y")
        self.assertEqual(dongle.get("CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS"), "3")
        self.assertEqual(dongle.get("CONFIG_BT_MAX_CONN"), "8")
        self.assertEqual(dongle.get("CONFIG_BT_MAX_PAIRED"), "8")

    def test_only_the_dongle_has_usb_hid(self):
        self.assertNotEqual(kconfig("left").get("CONFIG_ZMK_USB"), "y")
        self.assertNotEqual(kconfig("right").get("CONFIG_ZMK_USB"), "y")
        self.assertNotEqual(kconfig("pad").get("CONFIG_ZMK_USB"), "y")
        self.assertEqual(kconfig("dongle").get("CONFIG_ZMK_USB"), "y")

    def test_all_peripherals_have_bluetooth_and_cdc_recovery(self):
        for role in self.PERIPHERALS:
            config = kconfig(role)
            with self.subTest(role):
                self.assertEqual(config.get("CONFIG_ZMK_BLE"), "y")
                self.assertEqual(config.get("CONFIG_USB_CDC_ACM"), "y")
                self.assertEqual(config.get("CONFIG_NOCFREE_RECOVERY_CDC_1200_TOUCH"), "y")
                self.assertEqual(config.get("CONFIG_RETENTION_BOOT_MODE"), "y")
                self.assertEqual(config.get("CONFIG_USB_DEVICE_STACK"), "y")
                self.assertEqual(config.get("CONFIG_USB_DEVICE_INITIALIZE_AT_BOOT"), "y")

    def test_halves_keep_the_conservative_lf_clock(self):
        for role in self.PERIPHERALS:
            config = kconfig(role)
            with self.subTest(role):
                self.assertEqual(config.get("CONFIG_CLOCK_CONTROL_NRF_K32SRC_RC"), "y")
                self.assertNotEqual(config.get("CONFIG_CLOCK_CONTROL_NRF_K32SRC_XTAL"), "y")

    def test_split_link_uses_1m_phy_and_deep_tx_pipeline(self):
        for role in self.ROLES:
            config = kconfig(role)
            with self.subTest(role):
                self.assertEqual(config.get("CONFIG_ZMK_BLE"), "y")
                self.assertEqual(config.get("CONFIG_ZMK_BLE_EXPERIMENTAL_CONN"), "y")
                self.assertNotEqual(config.get("CONFIG_BT_CTLR_PHY_2M"), "y")
                self.assertEqual(config.get("CONFIG_BT_BUF_ACL_TX_COUNT"), "8")
                self.assertEqual(config.get("CONFIG_BT_L2CAP_TX_BUF_COUNT"), "8")
                self.assertEqual(config.get("CONFIG_BT_CONN_TX_MAX"), "8")
        self.assertEqual(
            kconfig("left").get("CONFIG_ZMK_SPLIT_BLE_PERIPHERAL_POSITION_QUEUE_SIZE"), "32"
        )
        self.assertEqual(
            kconfig("right").get("CONFIG_ZMK_SPLIT_BLE_PERIPHERAL_POSITION_QUEUE_SIZE"), "32"
        )
        self.assertEqual(
            kconfig("pad").get("CONFIG_ZMK_SPLIT_BLE_PERIPHERAL_POSITION_QUEUE_SIZE"), "32"
        )
        self.assertEqual(
            kconfig("dongle").get("CONFIG_ZMK_SPLIT_BLE_CENTRAL_POSITION_QUEUE_SIZE"), "32"
        )

    def test_studio_exists_only_on_the_dongle(self):
        self.assertNotEqual(kconfig("left").get("CONFIG_ZMK_STUDIO"), "y")
        self.assertNotEqual(kconfig("right").get("CONFIG_ZMK_STUDIO"), "y")
        self.assertNotEqual(kconfig("pad").get("CONFIG_ZMK_STUDIO"), "y")
        self.assertEqual(kconfig("dongle").get("CONFIG_ZMK_STUDIO"), "y")

    def test_battery_monitoring_is_enabled_only_for_verified_halves(self):
        self.assertEqual(kconfig("left").get("CONFIG_ZMK_BATTERY_REPORTING"), "y")
        self.assertEqual(kconfig("right").get("CONFIG_ZMK_BATTERY_REPORTING"), "y")
        self.assertNotEqual(kconfig("pad").get("CONFIG_ZMK_BATTERY_REPORTING"), "y")
        self.assertNotEqual(kconfig("dongle").get("CONFIG_ZMK_BATTERY_REPORTING"), "y")
        self.assertNotEqual(
            kconfig("dongle").get("CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING"),
            "y",
        )

        for role in ("left", "right"):
            config = kconfig(role)
            with self.subTest(role):
                self.assertEqual(config.get("CONFIG_ZMK_BATTERY_VOLTAGE_DIVIDER"), "y")
                self.assertEqual(config.get("CONFIG_ADC"), "y")
                self.assertEqual(config.get("CONFIG_BT_BAS"), "y")
                self.assertEqual(
                    config.get("CONFIG_NOCFREE_LOW_BATTERY_INDICATOR"), "y"
                )

        for role in ("pad", "dongle"):
            self.assertNotEqual(
                kconfig(role).get("CONFIG_NOCFREE_LOW_BATTERY_INDICATOR"), "y"
            )

        dongle_map = (role_dir("dongle") / "zmk.map").read_text(errors="replace")
        self.assertNotIn("peripheral_battery_event_compat.c.obj", dongle_map)
        self.assertNotIn("(battery_diagnostic.c.obj)", dongle_map)

    def test_compiled_battery_nodes_keep_verified_pinout_and_calibration(self):
        for role, enable_pin in (("left", 5), ("right", 31)):
            text = (role_dir(role) / "zephyr.dts").read_text()
            node = re.search(r"vbatt: vbatt \{(.*?)\n\s*\};", text, re.S)
            with self.subTest(role):
                self.assertIsNotNone(node)
                values = node.group(1)
                self.assertIn('compatible = "zmk,battery-voltage-divider"', values)
                self.assertRegex(values, r"io-channels = < &adc 0x2 >")
                self.assertRegex(values, r"output-ohms = < 0x2 >")
                self.assertRegex(values, r"full-ohms = < 0x3 >")
                self.assertRegex(
                    values,
                    rf"power-gpios = < &gpio0 0x{enable_pin:x} 0x0 >",
                )

        pad_text = (role_dir("pad") / "zephyr.dts").read_text()
        self.assertNotIn('compatible = "zmk,battery-voltage-divider"', pad_text)

        # XIAO's upstream board DTS always contains its own VBAT divider even
        # when CONFIG_ZMK_BATTERY_REPORTING=n. Keep that known node exact so it
        # cannot be confused with either NocFree half's newly enabled circuit.
        dongle_text = (role_dir("dongle") / "zephyr.dts").read_text()
        dongle_node = re.search(
            r"vbatt: vbatt \{(.*?)\n\s*\};", dongle_text, re.S
        )
        self.assertIsNotNone(dongle_node)
        values = dongle_node.group(1)
        self.assertIn('compatible = "zmk,battery-voltage-divider"', values)
        self.assertRegex(values, r"io-channels = < &adc 0x7 >")
        self.assertRegex(values, r"power-gpios = < &gpio0 0xe 0x7 >")
        self.assertRegex(values, r"output-ohms = < 0x7c830 >")
        self.assertRegex(values, r"full-ohms = < 0x170a70 >")

    def test_excluded_features_are_absent(self):
        for role in self.ROLES:
            config = kconfig(role)
            for symbol in (
                "CONFIG_ZMK_BACKLIGHT",
                "CONFIG_ZMK_RGB_UNDERGLOW",
            ):
                with self.subTest(f"{role} {symbol}"):
                    self.assertNotEqual(config.get(symbol), "y")

    def test_halves_link_into_the_preserved_code_partition(self):
        for role in self.PERIPHERALS:
            config = kconfig(role)
            with self.subTest(role):
                self.assertEqual(config.get("CONFIG_USE_DT_CODE_PARTITION"), "y")
                self.assertEqual(int(config["CONFIG_FLASH_LOAD_OFFSET"], 0), CODE_START)
                self.assertEqual(int(config["CONFIG_FLASH_LOAD_SIZE"], 0), CODE_SIZE)

    def test_half_uf2_writes_only_inside_the_code_partition(self):
        for role in self.PERIPHERALS:
            uf2 = role_dir(role) / "zmk.uf2"
            with self.subTest(role):
                self.assertTrue(uf2.is_file(), f"missing {uf2}")
                blocks = list(uf2_blocks(uf2))
                self.assertGreater(len(blocks), 0)
                for block in blocks:
                    self.assertEqual(block["start0"], UF2_MAGIC_START0)
                    self.assertEqual(block["start1"], UF2_MAGIC_START1)
                    self.assertEqual(block["end"], UF2_MAGIC_END)
                    self.assertGreaterEqual(block["address"], CODE_START)
                    self.assertLessEqual(block["address"] + block["payload"], CODE_END)
                lowest = min(b["address"] for b in blocks)
                highest = max(b["address"] + b["payload"] for b in blocks)
                self.assertEqual(lowest, CODE_START)
                self.assertLessEqual(highest, CODE_END)

    def test_half_uf2_never_targets_bootloader_or_factory_data(self):
        fs_start, fs_end = spec.FACTORY_FILESYSTEM
        boot_start = spec.PARTITIONS["boot_partition"][0]
        storage_start = spec.PARTITIONS["storage_partition"][0]
        for role in self.PERIPHERALS:
            for block in uf2_blocks(role_dir(role) / "zmk.uf2"):
                first, last = block["address"], block["address"] + block["payload"]
                with self.subTest(f"{role} 0x{first:x}"):
                    self.assertLessEqual(last, storage_start)
                    self.assertFalse(fs_start <= first < fs_end)
                    self.assertLess(first, boot_start)

    def compiled_key_inputs(self, role: str) -> list[tuple[str, int]]:
        text = (role_dir(role) / "zephyr.dts").read_text()
        body = re.search(r"key-inputs = (.*?);$", text, re.M)
        assert body, f"no key-inputs in the {role} devicetree"
        return [
            (label, int(bit, 0))
            for label, bit in re.findall(r"<\s*&(\w+)\s+(0x[0-9a-f]+)\s*>", body.group(1))
        ]

    def test_compiled_devicetree_has_the_exact_key_map(self):
        self.assertEqual(self.compiled_key_inputs("left"), spec.LEFT_INPUTS)
        self.assertEqual(self.compiled_key_inputs("right"), spec.RIGHT_INPUTS)
        self.assertEqual(self.compiled_key_inputs("pad"), spec.PAD_INPUTS)

    def test_dongle_compiles_all_studio_editable_layers(self):
        text = (role_dir("dongle") / "zephyr.dts").read_text()
        for display_name in ("Base", "Fn", "Nav", "Numpad", "Work"):
            with self.subTest(display_name):
                self.assertIn(f'display-name = "{display_name}";', text)

    def test_compiled_devicetree_excludes_unpopulated_bits(self):
        for role, unused in (
            ("left", spec.LEFT_UNUSED),
            ("right", spec.RIGHT_UNUSED),
            ("pad", spec.PAD_UNUSED),
        ):
            declared = set(self.compiled_key_inputs(role))
            for label, bits in unused.items():
                for bit in bits:
                    with self.subTest(f"{role} {label} bit {bit}"):
                        self.assertNotIn((label, bit), declared)

    def test_right_and_pad_have_the_expected_column_offsets(self):
        left = (role_dir("left") / "zephyr.dts").read_text()
        right = (role_dir("right") / "zephyr.dts").read_text()
        pad = (role_dir("pad") / "zephyr.dts").read_text()
        dongle = (role_dir("dongle") / "zephyr.dts").read_text()
        offset = re.search(r"col-offset = <\s*(0x[0-9a-f]+|\d+)\s*>", right)
        self.assertIsNotNone(offset)
        self.assertEqual(int(offset.group(1), 0), spec.RIGHT_COL_OFFSET)
        pad_offset = re.search(r"col-offset = <\s*(0x[0-9a-f]+|\d+)\s*>", pad)
        self.assertIsNotNone(pad_offset)
        self.assertEqual(int(pad_offset.group(1), 0), spec.PAD_COL_OFFSET)
        self.assertNotIn("col-offset", left)
        self.assertNotIn("col-offset", dongle)

    def test_compiled_transform_covers_every_position(self):
        for role in self.ROLES:
            text = (role_dir(role) / "zephyr.dts").read_text()
            # Match only an exact `map` property. Studio/macros add properties
            # such as `bindings-map`; an unanchored search would mistake those
            # for the keyboard matrix transform.
            body = re.search(r"^\s*map\s*=\s*<(.*?)>;", text, re.S | re.M)
            with self.subTest(role):
                self.assertIsNotNone(body)
                values = [int(v, 0) for v in re.findall(r"0x[0-9a-f]+|\b\d+\b", body.group(1))]
                expected = (
                    spec.KEYBOARD_TRANSFORM
                    if role in ("left", "right")
                    else spec.TRANSFORM
                )
                self.assertEqual(sorted(values), sorted(expected))

    def test_scanner_and_recovery_code_are_linked_into_halves(self):
        for role in self.PERIPHERALS:
            mapfile = (role_dir(role) / "zmk.map").read_text(errors="replace")
            for obj in ("kscan_pca9555.c.obj", "cdc_1200_touch.c.obj"):
                with self.subTest(f"{role} {obj}"):
                    self.assertIn(obj, mapfile)

    def test_layer_indicator_is_linked_only_into_dongle(self):
        dongle_map = (role_dir("dongle") / "zmk.map").read_text(errors="replace")
        self.assertIn("layer_led_indicator.c.obj", dongle_map)
        for role in self.PERIPHERALS:
            half_map = (role_dir(role) / "zmk.map").read_text(errors="replace")
            with self.subTest(role):
                self.assertNotIn("layer_led_indicator.c.obj", half_map)

    def test_low_battery_indicator_is_linked_only_into_keyboard_halves(self):
        for role in ("left", "right"):
            mapfile = (role_dir(role) / "zmk.map").read_text(errors="replace")
            with self.subTest(role):
                self.assertIn("low_battery_indicator.c.obj", mapfile)

        for role in ("pad", "dongle"):
            mapfile = (role_dir(role) / "zmk.map").read_text(errors="replace")
            with self.subTest(role):
                self.assertNotIn("low_battery_indicator.c.obj", mapfile)

    def test_half_uf2_targets_the_nrf52833_family(self):
        NRF52833_FAMILY = 0x621E937A
        for role in self.PERIPHERALS:
            for block in uf2_blocks(role_dir(role) / "zmk.uf2"):
                with self.subTest(role):
                    self.assertTrue(block["flags"] & UF2_FLAG_FAMILY_ID)
                    self.assertEqual(block["family"], NRF52833_FAMILY)
                break

    def test_expanders_are_at_the_published_addresses(self):
        for role in self.PERIPHERALS:
            text = (role_dir(role) / "zephyr.dts").read_text()
            found = sorted(int(a, 16) for a in re.findall(r"keys@(\w+) \{", text))
            with self.subTest(role):
                self.assertEqual(found, sorted(spec.EXPANDER_ADDRESSES.values()))

    def test_half_images_leave_headroom_in_the_slot(self):
        for role in self.PERIPHERALS:
            size = (role_dir(role) / "zmk.bin").stat().st_size
            with self.subTest(role):
                self.assertLess(size, CODE_SIZE)
                print(f"\n  {role}: {size} bytes of {CODE_SIZE} "
                      f"({100 * size / CODE_SIZE:.1f}%)")

    def test_dongle_outputs_uf2(self):
        self.assertTrue((role_dir("dongle") / "zmk.uf2").is_file())


@unittest.skipUnless(
    battery_adc_probes_available(),
    f"no complete battery ADC probe build output under {BUILD}",
)
class BatteryAdcProbeArtifactTest(unittest.TestCase):
    ROLES = ("left_battery_adc_probe", "right_battery_adc_probe")

    def test_probes_are_local_usb_only_measurements(self):
        for role in self.ROLES:
            config = kconfig(role)
            with self.subTest(role):
                self.assertEqual(
                    config.get("CONFIG_NOCFREE_BATTERY_ADC_PROBE"), "y"
                )
                self.assertEqual(config.get("CONFIG_ZMK_USB_LOGGING"), "y")
                self.assertEqual(config.get("CONFIG_ZMK_LOGGING_MINIMAL"), "y")
                self.assertEqual(config.get("CONFIG_ZMK_USB"), "y")
                self.assertNotEqual(config.get("CONFIG_ZMK_BLE"), "y")
                self.assertNotEqual(config.get("CONFIG_ZMK_SPLIT"), "y")
                self.assertNotEqual(config.get("CONFIG_ZMK_BATTERY_REPORTING"), "y")
                self.assertNotEqual(
                    config.get("CONFIG_ZMK_BATTERY_VOLTAGE_DIVIDER"), "y"
                )
                self.assertEqual(config.get("CONFIG_ADC"), "y")

    def test_probes_link_only_the_raw_adc_reporter(self):
        for role in self.ROLES:
            mapfile = (role_dir(role) / "zmk.map").read_text(errors="replace")
            with self.subTest(role):
                self.assertIn("battery_adc_probe.c.obj", mapfile)
                self.assertNotIn("local_battery_diagnostic.c.obj", mapfile)
                self.assertNotIn("(battery_diagnostic.c.obj)", mapfile)
                self.assertNotIn("peripheral_battery_event_compat.c.obj", mapfile)
                self.assertNotIn("low_battery_indicator.c.obj", mapfile)

    def test_diagnostic_uf2s_stay_inside_application_partition(self):
        for role in self.ROLES:
            uf2 = role_dir(role) / "zmk.uf2"
            with self.subTest(role):
                self.assertTrue(uf2.is_file())
                for block in uf2_blocks(uf2):
                    self.assertGreaterEqual(block["address"], CODE_START)
                    self.assertLessEqual(block["address"] + block["payload"], CODE_END)
                    self.assertEqual(block["family"], 0x621E937A)


@unittest.skipUnless(
    low_battery_led_probes_available(),
    f"no complete low-battery LED probe build output under {BUILD}",
)
class LowBatteryLedProbeArtifactTest(unittest.TestCase):
    ROLES = (
        "left_low_battery_led_probe",
        "right_low_battery_led_probe",
    )

    def test_probes_are_local_usb_only_and_do_not_sample_battery(self):
        for role in self.ROLES:
            config = kconfig(role)
            with self.subTest(role):
                self.assertEqual(
                    config.get("CONFIG_NOCFREE_LOW_BATTERY_LED_PROBE"), "y"
                )
                self.assertEqual(config.get("CONFIG_ZMK_USB_LOGGING"), "y")
                self.assertEqual(config.get("CONFIG_ZMK_USB"), "y")
                self.assertNotEqual(config.get("CONFIG_ZMK_BLE"), "y")
                self.assertNotEqual(config.get("CONFIG_ZMK_SPLIT"), "y")
                self.assertNotEqual(config.get("CONFIG_ZMK_BATTERY_REPORTING"), "y")
                self.assertNotEqual(
                    config.get("CONFIG_ZMK_BATTERY_VOLTAGE_DIVIDER"), "y"
                )

    def test_probes_link_only_the_led_reporter(self):
        for role in self.ROLES:
            mapfile = (role_dir(role) / "zmk.map").read_text(errors="replace")
            with self.subTest(role):
                self.assertIn("low_battery_led_probe.c.obj", mapfile)
                self.assertNotIn("battery_adc_probe.c.obj", mapfile)
                self.assertNotIn("local_battery_diagnostic.c.obj", mapfile)
                self.assertNotIn("peripheral_battery_event_compat.c.obj", mapfile)
                self.assertNotIn("low_battery_indicator.c.obj", mapfile)

    def test_probe_uf2s_stay_inside_application_partition(self):
        for role in self.ROLES:
            uf2 = role_dir(role) / "zmk.uf2"
            with self.subTest(role):
                self.assertTrue(uf2.is_file())
                for block in uf2_blocks(uf2):
                    self.assertGreaterEqual(block["address"], CODE_START)
                    self.assertLessEqual(block["address"] + block["payload"], CODE_END)
                    self.assertEqual(block["family"], 0x621E937A)


@unittest.skipUnless(
    diagnostic_available(), f"no Pad USB diagnostic build output under {BUILD}"
)
class PadUsbDiagnosticArtifactTest(unittest.TestCase):
    def test_diagnostic_is_usb_only_and_keeps_recovery(self):
        config = kconfig("pad_usb_diagnostic")
        self.assertNotEqual(config.get("CONFIG_ZMK_SPLIT"), "y")
        self.assertEqual(config.get("CONFIG_ZMK_USB"), "y")
        self.assertNotEqual(config.get("CONFIG_ZMK_BLE"), "y")
        self.assertNotEqual(
            config.get("CONFIG_USB_DEVICE_INITIALIZE_AT_BOOT"), "y"
        )
        self.assertEqual(config.get("CONFIG_USB_CDC_ACM"), "y")
        self.assertEqual(config.get("CONFIG_NOCFREE_RECOVERY_CDC_1200_TOUCH"), "y")
        self.assertEqual(config.get("CONFIG_NOCFREE_KSCAN_PCA9555"), "y")
        self.assertEqual(config.get("CONFIG_ZMK_USB_LOGGING"), "y")
        self.assertEqual(config.get("CONFIG_NOCFREE_PAD_I2C_DIAGNOSTIC"), "y")

    def test_diagnostic_uf2_stays_inside_the_application_partition(self):
        uf2 = role_dir("pad_usb_diagnostic") / "zmk.uf2"
        self.assertTrue(uf2.is_file())
        blocks = list(uf2_blocks(uf2))
        self.assertGreater(len(blocks), 0)
        for block in blocks:
            self.assertGreaterEqual(block["address"], CODE_START)
            self.assertLessEqual(block["address"] + block["payload"], CODE_END)
            self.assertEqual(block["family"], 0x621E937A)

    def test_diagnostic_links_scanner_and_recovery(self):
        mapfile = (role_dir("pad_usb_diagnostic") / "zmk.map").read_text(
            errors="replace"
        )
        self.assertIn("kscan_pca9555.c.obj", mapfile)
        self.assertIn("cdc_1200_touch.c.obj", mapfile)
        self.assertIn("pad_i2c_diagnostic.c.obj", mapfile)

    def test_diagnostic_uses_the_existing_recovery_cdc_as_console(self):
        devicetree = (role_dir("pad_usb_diagnostic") / "zephyr.dts").read_text()
        chosen = re.search(r"chosen \{(.*?)\n\s*\};", devicetree, re.S)
        self.assertIsNotNone(chosen)
        self.assertIn("zephyr,console = &cdc_acm_uart0", chosen.group(1))


if __name__ == "__main__":
    unittest.main()
