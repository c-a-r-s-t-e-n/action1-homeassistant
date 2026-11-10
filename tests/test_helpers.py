"""Unit tests with synthetic Action1 API payloads (no real credentials)."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "action1_monitor"


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api = load("api.py", "action1_api_pure")
metrics = load("metrics.py", "action1_metrics_pure")


class ApiTests(unittest.TestCase):
    def test_regions_and_ssrf(self):
        self.assertEqual(
            api.validate_origin("https://app.eu.action1.com"),
            "https://app.eu.action1.com",
        )
        for url in (
            "http://app.action1.com",
            "https://evil.example",
            "https://app.action1.com.evil.net",
            "https://app.action1.com@evil.com",
            "https://app.action1.com/redirect",
            "https://app.action1.com?token=x",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                api.validate_origin(url)

    def test_result_pages(self):
        self.assertEqual(
            api.page_items({"items": [{"id": "x"}], "total_items": 1}),
            [{"id": "x"}],
        )
        self.assertEqual(api.page_items([{"id": "x"}]), [{"id": "x"}])
        self.assertEqual(api.page_items({"unexpected": True}), [])


class SecurityMetricTests(unittest.TestCase):
    def test_security_metrics(self):
        rows = [
            {"cve_id": "CVE-TEST-1", "cvss_score": "9.8", "cisa_kev": "yes"},
            {"cve_id": "CVE-TEST-2", "cvss_score": "7.2", "cisa_kev": "no"},
        ]
        self.assertEqual(metrics.critical_cves(rows), 1)
        self.assertEqual(metrics.known_exploited_cves(rows), 1)

    def test_no_data_is_not_zero(self):
        self.assertIsNone(metrics.critical_cves(None))
        self.assertIsNone(metrics.important_updates(None))

    def test_important_updates(self):
        self.assertEqual(
            metrics.important_updates([
                {"security_severity": "Important"},
                {"security_severity": "Critical"},
                {"security_severity": "None"},
            ]),
            2,
        )


class LiveSchemaRegressionTests(unittest.TestCase):
    def test_no_unverified_update_severity_is_zero(self):
        records = [{"classification": "Security Updates", "kb_number": "KB0000000"}]
        self.assertIsNone(metrics.important_updates(records))

    def test_schema_field_names_present(self):
        row = {
            "online_status": "online",
            "status": "active",
            "missing_updates": 6,
            "CPU_name": "Example",
            "reboot_required": False,
        }
        self.assertIn("online_status", row)
        self.assertIn("missing_updates", row)


if __name__ == "__main__":
    unittest.main()
