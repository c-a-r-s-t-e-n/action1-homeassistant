"""Regression tests for the real anonymized Action1 response structures."""

import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "custom_components" / "action1_monitor" / "model.py"
spec = importlib.util.spec_from_file_location("action1_model", MODULE)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class ResultPageTests(unittest.TestCase):
    def test_total_from_paginated_action1_api(self):
        data = {"items": [{"cve_id": "CVE-TEST"}], "total_items": 79, "limit": 1}
        self.assertEqual(model.report_total(data), 79)
        self.assertEqual(len(model.report_items(data)), 1)

    def test_unknown_is_never_zero(self):
        self.assertIsNone(model.report_total(None))
        self.assertIsNone(model.report_total({"error": "unavailable"}))
        self.assertIsNone(model.report_total({"total_items": "invalid"}))

    def test_report_shape_with_no_items(self):
        self.assertEqual(model.report_total({"items": [], "total_items": 0}), 0)


class SecurityMetricsTests(unittest.TestCase):
    def test_explicit_cvss_and_cisa_kev(self):
        summary = model.severity_summary([
            {"cvss_score": 9.8, "cisa_kev": True},
            {"cvss_score": 8.1, "cisa_kev": "yes"},
            {"cvss_score": None, "cisa_kev": False},
            {"cvss_score": "99", "cisa_kev": None},
            {"cve_id": "CVE-TEST"},
        ])
        self.assertEqual(summary["critical_cves"], 1)
        self.assertEqual(summary["high_cves"], 1)
        self.assertEqual(summary["known_exploited"], 2)
        self.assertEqual(summary["unknown_severity"], 3)

    def test_ambiguous_online_value_not_offline(self):
        self.assertTrue(model.endpoint_health("online"))
        self.assertFalse(model.endpoint_health("offline"))
        self.assertIsNone(model.endpoint_health("unknown"))
        self.assertIsNone(model.endpoint_health(None))

    def test_non_scalar_inventory_not_written_to_entity(self):
        self.assertIsNone(model.simple_scalar({"size": 16}))
        self.assertIsNone(model.simple_scalar(["WiFi", "Ethernet"]))
        self.assertEqual(model.simple_scalar("Windows 11"), "Windows 11")

    def test_reboot_boolean_strict(self):
        self.assertTrue(model.conservative_bool("required"))
        self.assertFalse(model.conservative_bool("not_required"))
        self.assertIsNone(model.conservative_bool("waiting"))


if __name__ == "__main__":
    unittest.main()
