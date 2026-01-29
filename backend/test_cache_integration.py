"""
Phase 8 — Cache-Specific Integration Tests

Exercises the SQLite caching system end-to-end through the search pipeline
with a mocked Wikipedia API.  Each section maps to a plan step:

    8.1  Cache miss (first run)
    8.2  Cache hit  (second run with same search)
    8.3  Cache expiration (30-day limit)
    8.4  Manual cache clearing
    8.5  Partial cache hits
    8.6  Performance comparison (cached vs uncached)
    8.7  Database integrity
"""

import json
import os
import sqlite3
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, call

# ---------- isolate test database ----------
import db as _db_module

TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test_cache_integration.db"
)
_db_module.CACHE_DB_PATH = TEST_DB_PATH

from db import (
    CACHE_EXPIRATION_DAYS,
    TABLE_ARTICLE_LINKS,
    cache_article_links,
    clear_cache,
    get_cache_stats,
    get_cached_links,
    init_db,
)
from wikipedia_client import (
    get_article_links,
    get_backlinks,
    get_cache_hit_stats,
    reset_cache_hit_stats,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# A small mock graph:
#   Start --> Mid --> End
#   (backlinks: End <-- Mid <-- Start)
MOCK_LINKS = {
    "Start": ["Mid", "Other1", "Other2"],
    "Mid": ["End", "Other3"],
    "End": ["Unrelated"],
    "Other1": [],
    "Other2": [],
    "Other3": [],
    "Unrelated": [],
}

MOCK_BACKLINKS = {
    "End": ["Mid", "SomeOther"],
    "Mid": ["Start"],
    "Start": [],
    "SomeOther": [],
}


def _mock_make_request(params: dict) -> dict:
    """Simulate Wikipedia API responses for the mock graph."""
    params.setdefault("format", "json")

    # --- forward links (prop=links) ---
    if params.get("prop") == "links":
        title = params["titles"]
        links = MOCK_LINKS.get(title, [])
        return {
            "query": {
                "pages": {
                    "1": {
                        "pageid": 1,
                        "title": title,
                        "links": [{"ns": 0, "title": t} for t in links],
                    }
                }
            }
        }

    # --- backlinks (list=backlinks) ---
    if params.get("list") == "backlinks":
        title = params["bltitle"]
        bls = MOCK_BACKLINKS.get(title, [])
        return {
            "query": {
                "backlinks": [{"pageid": i, "title": t} for i, t in enumerate(bls)]
            }
        }

    # --- article validation (action=query, titles=X, redirects=1) ---
    if "titles" in params and "redirects" in params:
        title = params["titles"]
        return {
            "query": {
                "pages": {
                    "1": {"pageid": 1, "title": title}
                }
            }
        }

    return {}


class _CacheIntegrationBase(unittest.TestCase):
    """Fresh database + counters for every test."""

    def setUp(self):
        _db_module.CACHE_DB_PATH = TEST_DB_PATH
        init_db()
        clear_cache()
        reset_cache_hit_stats()

    def tearDown(self):
        clear_cache()
        reset_cache_hit_stats()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    # helpers
    def _insert_with_timestamp(self, title, links, cached_at):
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.execute(
            f"INSERT OR REPLACE INTO {TABLE_ARTICLE_LINKS} "
            f"(article_title, links, cached_at) VALUES (?, ?, ?)",
            (title, json.dumps(links), cached_at),
        )
        conn.commit()
        conn.close()

    def _db_file_size(self):
        return os.path.getsize(TEST_DB_PATH)


# ===================================================================
# 8.1  Cache miss (first run)
# ===================================================================
class TestCacheMissFirstRun(_CacheIntegrationBase):
    """First fetch for an article should hit the API and populate cache."""

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_all_misses_on_first_run(self, mock_req):
        """Every article queried for the first time is a cache miss."""
        reset_cache_hit_stats()

        get_article_links("Start")
        get_article_links("Mid")

        stats = get_cache_hit_stats()
        self.assertEqual(stats["cache_misses"], 2)
        self.assertEqual(stats["cache_hits"], 0)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_links_stored_after_fetch(self, mock_req):
        """After a miss the links are stored in the cache."""
        get_article_links("Start")

        cached = get_cached_links("Start")
        self.assertIsNotNone(cached)
        self.assertEqual(set(cached), {"Mid", "Other1", "Other2"})

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_db_rows_grow(self, mock_req):
        """cache.db row count should increase after caching new articles."""
        stats_before = get_cache_stats()
        self.assertEqual(stats_before["total_articles"], 0)

        get_article_links("Start")
        get_article_links("Mid")

        stats_after = get_cache_stats()
        self.assertEqual(stats_after["total_articles"], 2)
        self.assertGreater(stats_after["cache_size_bytes"], 0)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_cache_stats_reflect_new_entries(self, mock_req):
        """get_cache_stats() shows the newly cached articles."""
        get_article_links("Start")
        get_article_links("Mid")

        stats = get_cache_stats()
        self.assertEqual(stats["total_articles"], 2)
        self.assertGreater(stats["total_links"], 0)


# ===================================================================
# 8.2  Cache hit (second run with same search)
# ===================================================================
class TestCacheHitSecondRun(_CacheIntegrationBase):
    """Second fetch for the same article should use the cache."""

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_no_api_call_on_hit(self, mock_req):
        """Second call for same article should not call the API."""
        get_article_links("Start")
        mock_req.reset_mock()

        get_article_links("Start")
        mock_req.assert_not_called()

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_hit_counter_incremented(self, mock_req):
        """Hit counter reflects that second call was served from cache."""
        reset_cache_hit_stats()

        get_article_links("Start")  # miss
        get_article_links("Start")  # hit

        stats = get_cache_hit_stats()
        self.assertEqual(stats["cache_hits"], 1)
        self.assertEqual(stats["cache_misses"], 1)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_db_size_unchanged_on_hit(self, mock_req):
        """DB file should not grow when all fetches are cache hits."""
        get_article_links("Start")
        size_after_first = self._db_file_size()

        get_article_links("Start")
        size_after_second = self._db_file_size()

        self.assertEqual(size_after_first, size_after_second)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_cached_search_is_fast(self, mock_req):
        """Cached lookups should be near-instant (well under 5 seconds)."""
        get_article_links("Start")

        t0 = time.monotonic()
        for _ in range(100):
            get_article_links("Start")
        elapsed = time.monotonic() - t0

        # 100 cached lookups should take well under 1 second
        self.assertLess(elapsed, 1.0)


# ===================================================================
# 8.3  Cache expiration (30-day limit)
# ===================================================================
class TestCacheExpiration(_CacheIntegrationBase):
    """Entries older than 30 days must be treated as misses."""

    def test_expired_entry_returns_none(self):
        old = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 1)).isoformat()
        self._insert_with_timestamp("OldArticle", ["X", "Y"], old)

        result = get_cached_links("OldArticle")
        self.assertIsNone(result)

    def test_expired_entry_is_deleted_from_db(self):
        old = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 1)).isoformat()
        self._insert_with_timestamp("OldArticle", ["X"], old)

        get_cached_links("OldArticle")  # triggers delete

        conn = sqlite3.connect(TEST_DB_PATH)
        row = conn.execute(
            f"SELECT * FROM {TABLE_ARTICLE_LINKS} WHERE article_title = ?",
            ("OldArticle",),
        ).fetchone()
        conn.close()
        self.assertIsNone(row)

    def test_expired_count_in_stats(self):
        old = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 5)).isoformat()
        self._insert_with_timestamp("Old1", ["a"], old)
        self._insert_with_timestamp("Old2", ["b"], old)
        cache_article_links("Fresh", ["c"])

        stats = get_cache_stats()
        self.assertEqual(stats["expired_count"], 2)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_expired_entry_triggers_fresh_fetch(self, mock_req):
        """Expired entry causes a fresh API fetch and re-cache."""
        old = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 1)).isoformat()
        self._insert_with_timestamp("Start", ["StaleLink"], old)

        result = get_article_links("Start")

        # Should have fresh data, not the stale ["StaleLink"]
        self.assertIn("Mid", result)
        self.assertNotIn("StaleLink", result)

        # And the fresh data should now be cached
        cached = get_cached_links("Start")
        self.assertIn("Mid", cached)


# ===================================================================
# 8.4  Manual cache clearing
# ===================================================================
class TestManualCacheClearing(_CacheIntegrationBase):
    """Tests for clear_cache() with specific and full clear."""

    def test_clear_specific_article(self):
        cache_article_links("Python", ["L1"])
        cache_article_links("Java", ["L2"])

        deleted = clear_cache("Python")

        self.assertEqual(deleted, 1)
        self.assertIsNone(get_cached_links("Python"))
        self.assertEqual(get_cached_links("Java"), ["L2"])

    def test_clear_all_entries(self):
        cache_article_links("A", ["1"])
        cache_article_links("B", ["2"])
        cache_article_links("C", ["3"])

        deleted = clear_cache()

        self.assertEqual(deleted, 3)
        stats = get_cache_stats()
        self.assertEqual(stats["total_articles"], 0)
        self.assertEqual(stats["total_links"], 0)

    def test_db_file_exists_after_full_clear(self):
        cache_article_links("X", ["y"])
        clear_cache()

        self.assertTrue(os.path.exists(TEST_DB_PATH))

    def test_stats_zero_after_full_clear(self):
        cache_article_links("A", ["1", "2"])
        clear_cache()

        stats = get_cache_stats()
        self.assertEqual(stats["total_articles"], 0)
        self.assertEqual(stats["total_links"], 0)
        self.assertIsNone(stats["oldest_entry"])
        self.assertIsNone(stats["newest_entry"])


# ===================================================================
# 8.5  Partial cache hits
# ===================================================================
class TestPartialCacheHits(_CacheIntegrationBase):
    """When some articles are cached and others are not."""

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_mixed_hit_and_miss(self, mock_req):
        """Pre-cached article A is a hit; article B triggers an API call."""
        # Pre-populate cache for "Start" only
        cache_article_links("Start", ["Mid", "Other1", "Other2"])
        reset_cache_hit_stats()

        result_start = get_article_links("Start")  # hit
        result_mid = get_article_links("Mid")  # miss

        stats = get_cache_hit_stats()
        self.assertEqual(stats["cache_hits"], 1)
        self.assertEqual(stats["cache_misses"], 1)

        # Both should return correct data
        self.assertIn("Mid", result_start)
        self.assertIn("End", result_mid)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_missed_article_is_cached_for_next_time(self, mock_req):
        """Article that was a miss should be cached after the fetch."""
        cache_article_links("Start", ["Mid", "Other1", "Other2"])

        get_article_links("Mid")  # miss → fetches & caches

        cached = get_cached_links("Mid")
        self.assertIsNotNone(cached)
        self.assertIn("End", cached)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_partial_stats_accurate(self, mock_req):
        """Cache stats reflect the combined state after partial hits."""
        cache_article_links("Start", ["Mid", "Other1", "Other2"])
        reset_cache_hit_stats()

        get_article_links("Start")  # hit
        get_article_links("Mid")    # miss
        get_article_links("Mid")    # hit (now cached)

        stats = get_cache_hit_stats()
        self.assertEqual(stats["cache_hits"], 2)
        self.assertEqual(stats["cache_misses"], 1)

        db_stats = get_cache_stats()
        self.assertEqual(db_stats["total_articles"], 2)  # Start + Mid


# ===================================================================
# 8.6  Performance comparison (cached vs uncached)
# ===================================================================
class TestPerformanceComparison(_CacheIntegrationBase):
    """Cached lookups should be dramatically faster than uncached."""

    @patch("wikipedia_client._make_request")
    def test_cached_is_faster_than_uncached(self, mock_req):
        """Cache hits should be at least 10x faster than API-backed misses."""

        def slow_api(params):
            """Simulate API latency of 50ms per call."""
            time.sleep(0.05)
            return _mock_make_request(params)

        mock_req.side_effect = slow_api

        titles = ["Start", "Mid", "End"]

        # Uncached — each call pays API latency
        t0 = time.monotonic()
        for t in titles:
            get_article_links(t)
        uncached_time = time.monotonic() - t0

        # Cached — should be near-instant
        mock_req.reset_mock()
        t0 = time.monotonic()
        for t in titles:
            get_article_links(t)
        cached_time = time.monotonic() - t0

        # No API calls should have been made on the cached run
        mock_req.assert_not_called()

        # Cached must be at least 10x faster
        self.assertGreater(uncached_time, cached_time * 10,
                           f"Expected uncached ({uncached_time:.4f}s) > "
                           f"10 × cached ({cached_time:.4f}s)")

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_cached_lookup_under_5_seconds(self, mock_req):
        """Even 1000 cached lookups should finish well under 5 seconds."""
        get_article_links("Start")  # populate cache

        t0 = time.monotonic()
        for _ in range(1000):
            get_article_links("Start")
        elapsed = time.monotonic() - t0

        self.assertLess(elapsed, 5.0)


# ===================================================================
# 8.7  Database integrity
# ===================================================================
class TestDatabaseIntegrity(_CacheIntegrationBase):
    """Cache database should remain valid after various operations."""

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_all_entries_are_valid_json(self, mock_req):
        """Every links column value must be parseable JSON."""
        for title in ("Start", "Mid", "End"):
            get_article_links(title)

        conn = sqlite3.connect(TEST_DB_PATH)
        rows = conn.execute(
            f"SELECT article_title, links FROM {TABLE_ARTICLE_LINKS}"
        ).fetchall()
        conn.close()

        for title, links_json in rows:
            parsed = json.loads(links_json)
            self.assertIsInstance(parsed, list,
                                 f"Expected list for {title}, got {type(parsed)}")

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_db_exists_after_operations(self, mock_req):
        """DB file should exist after writes, clears, and re-writes."""
        get_article_links("Start")
        clear_cache()
        get_article_links("Mid")

        self.assertTrue(os.path.exists(TEST_DB_PATH))

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_timestamps_are_valid_iso(self, mock_req):
        """All cached_at timestamps must be valid ISO-8601."""
        get_article_links("Start")
        get_article_links("Mid")

        conn = sqlite3.connect(TEST_DB_PATH)
        rows = conn.execute(
            f"SELECT cached_at FROM {TABLE_ARTICLE_LINKS}"
        ).fetchall()
        conn.close()

        for (ts,) in rows:
            dt = datetime.fromisoformat(ts)
            self.assertIsNotNone(dt)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_no_duplicate_entries(self, mock_req):
        """Fetching the same article twice should not create duplicates."""
        get_article_links("Start")
        # Clear cache so second call is a fresh miss that re-inserts
        clear_cache("Start")
        get_article_links("Start")

        conn = sqlite3.connect(TEST_DB_PATH)
        count = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE_ARTICLE_LINKS} WHERE article_title = ?",
            ("Start",),
        ).fetchone()[0]
        conn.close()

        self.assertEqual(count, 1)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_backlinks_cached_separately(self, mock_req):
        """Forward links and backlinks use separate cache keys."""
        get_article_links("End")
        get_backlinks("End")

        forward_cached = get_cached_links("End")
        backward_cached = get_cached_links("backlinks::End")

        self.assertIsNotNone(forward_cached)
        self.assertIsNotNone(backward_cached)
        # They should contain different data
        self.assertNotEqual(set(forward_cached), set(backward_cached))


if __name__ == "__main__":
    unittest.main()
