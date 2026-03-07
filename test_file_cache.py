import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from file_cache import clean_expired, file_cached, get, set


class FileCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_set_then_get_hit(self) -> None:
        result = {"success": True, "data": {"x": 1}}
        set(self.cache_dir, "tool_a", ("arg",), {"k": "v"}, 10, result)
        cached = get(self.cache_dir, "tool_a", ("arg",), {"k": "v"}, 10)
        self.assertEqual(cached, result)

    def test_get_expired_file_returns_none_and_deletes_file(self) -> None:
        result = {"success": True, "value": 123}
        with patch("file_cache.time.time", return_value=1000.0):
            set(self.cache_dir, "tool_b", tuple(), {}, 1, result)

        tool_dir = self.cache_dir / "tool_b"
        files = list(tool_dir.glob("*.json"))
        self.assertEqual(len(files), 1)
        cache_file = files[0]
        self.assertTrue(cache_file.exists())

        with patch("file_cache.time.time", return_value=1002.0):
            cached = get(self.cache_dir, "tool_b", tuple(), {}, 1)
        self.assertIsNone(cached)
        self.assertFalse(cache_file.exists())

    def test_get_malformed_expires_at_is_treated_as_miss(self) -> None:
        tool_dir = self.cache_dir / "tool_c"
        tool_dir.mkdir(parents=True, exist_ok=True)
        cache_file = tool_dir / "bad.json"
        cache_file.write_text(
            json.dumps({"expires_at": "invalid", "result": {"success": True}}),
            encoding="utf-8",
        )

        with patch("file_cache._cache_key", return_value="bad"):
            cached = get(self.cache_dir, "tool_c", tuple(), {}, 60)
        self.assertIsNone(cached)
        self.assertFalse(cache_file.exists())

    def test_get_invalid_result_type_is_treated_as_miss(self) -> None:
        tool_dir = self.cache_dir / "tool_d"
        tool_dir.mkdir(parents=True, exist_ok=True)
        cache_file = tool_dir / "bad.json"
        cache_file.write_text(
            json.dumps({"expires_at": 9999999999, "result": ["not", "dict"]}),
            encoding="utf-8",
        )

        with patch("file_cache._cache_key", return_value="bad"):
            cached = get(self.cache_dir, "tool_d", tuple(), {}, 60)
        self.assertIsNone(cached)
        self.assertFalse(cache_file.exists())

    def test_get_miss_does_not_create_directory(self) -> None:
        self.assertFalse((self.cache_dir / "tool_e").exists())
        cached = get(self.cache_dir, "tool_e", tuple(), {}, 60)
        self.assertIsNone(cached)
        self.assertFalse((self.cache_dir / "tool_e").exists())

    def test_decorator_caches_only_success_result(self) -> None:
        call_counter = {"ok": 0, "bad": 0}

        @file_cached(ttl_seconds=60, cache_dir=self.cache_dir)
        def good_tool(symbol: str) -> dict:
            call_counter["ok"] += 1
            return {"success": True, "symbol": symbol}

        @file_cached(ttl_seconds=60, cache_dir=self.cache_dir)
        def bad_tool(symbol: str) -> dict:
            call_counter["bad"] += 1
            return {"success": False, "symbol": symbol}

        self.assertTrue(good_tool("000001")["success"])
        self.assertTrue(good_tool("000001")["success"])
        self.assertEqual(call_counter["ok"], 1)

        self.assertFalse(bad_tool("000002")["success"])
        self.assertFalse(bad_tool("000002")["success"])
        self.assertEqual(call_counter["bad"], 2)

    def test_clean_expired_removes_expired_invalid_and_keeps_valid(self) -> None:
        tool_dir = self.cache_dir / "tool_f"
        tool_dir.mkdir(parents=True, exist_ok=True)

        expired = tool_dir / "expired.json"
        invalid = tool_dir / "invalid.json"
        valid = tool_dir / "valid.json"

        expired.write_text(
            json.dumps({"expires_at": 1, "result": {"success": True}}),
            encoding="utf-8",
        )
        invalid.write_text(
            json.dumps({"expires_at": "oops", "result": {"success": True}}),
            encoding="utf-8",
        )
        valid.write_text(
            json.dumps({"expires_at": 9999999999, "result": {"success": True}}),
            encoding="utf-8",
        )

        with patch("file_cache.time.time", return_value=100.0):
            removed = clean_expired(self.cache_dir)

        self.assertEqual(removed, 2)
        self.assertFalse(expired.exists())
        self.assertFalse(invalid.exists())
        self.assertTrue(valid.exists())


if __name__ == "__main__":
    unittest.main()
