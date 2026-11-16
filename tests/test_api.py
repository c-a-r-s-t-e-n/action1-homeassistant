"""Action1 read-only client behaviour with synthetic, untrusted API pages."""

import importlib.util
from pathlib import Path
from types import MethodType
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "action1_monitor"
spec = importlib.util.spec_from_file_location("action1_api", ROOT / "api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class PaginationTests(unittest.IsolatedAsyncioTestCase):
    async def test_paginated_endpoint_collection(self):
        client = api.Action1Client(None, "https://app.eu.action1.com", "test", "redacted")
        calls = []

        async def fake_get(self, path, params=None):
            calls.append((path, dict(params or {})))
            start = params["from"]
            return {
                "items": [{"id": x} for x in range(start, min(start + 100, 207))],
                "total_items": 207,
                "next_page": "https://untrusted.example/never-follow",
            }
        client.get = MethodType(fake_get, client)
        result = await client.pages("/organizations", max_records=500)
        self.assertEqual(len(result), 207)
        self.assertEqual([c[1]["from"] for c in calls], [0, 100, 200])
        self.assertTrue(all(c[0] == "/organizations" for c in calls))

    async def test_record_cap_is_enforced(self):
        client = api.Action1Client(None, "https://app.eu.action1.com", "test", "redacted")
        async def fake_get(self, path, params=None):
            return {"items": [{"id": x} for x in range(100)], "total_items": 20000}
        client.get = MethodType(fake_get, client)
        results = await client.pages("/organizations", max_records=125)
        self.assertEqual(len(results), 125)

    async def test_empty_collection_is_not_an_error(self):
        client = api.Action1Client(None, "https://app.eu.action1.com", "test", "redacted")
        async def fake_get(self, path, params=None):
            return {"items": [], "total_items": 0}
        client.get = MethodType(fake_get, client)
        self.assertEqual(await client.pages("/organizations"), [])


if __name__ == "__main__":
    unittest.main()
