"""
Unit tests for the database caching module (db.py).

Covers:
    - Database initialization
    - Storing and retrieving links
    - Cache expiration (30-day limit)
    - Clearing specific and all entries
    - Cache statistics accuracy
    - Expired-entry cleanup
"""

import json
import os
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone

# Override the DB path BEFORE importing db so tests use an isolated file
import db as _db_module

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cache.db")
_db_module.CACHE_DB_PATH = TEST_DB_PATH

from db import (
    CACHE_EXPIRATION_DAYS,
    TABLE_ARTICLE_LINKS,
    cache_article_links,
    cleanup_expired,
    clear_cache,
    get_cache_stats,
    get_cached_links,
    init_db,
)


class _BaseDBTest(unittest.TestCase):
    """Base class that creates a fresh database for every test."""

    def setUp(self):
        _db_module.CACHE_DB_PATH = TEST_DB_PATH
        self._remove_db()
        init_db()

    def tearDown(self):
        self._remove_db()

    def _remove_db(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    # ---- helpers ----
    def _insert_with_timestamp(self, title: str, links: list[str], cached_at: str):
        """Insert a row with an explicit cached_at timestamp."""
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.execute(
            f"INSERT OR REPLACE INTO {TABLE_ARTICLE_LINKS} (article_title, links, cached_at) VALUES (?, ?, ?)",
            (title, json.dumps(links), cached_at),
        )
        conn.commit()
        conn.close()


class TestInitDB(_BaseDBTest):
    """init_db should create the database file and table."""

    def test_creates_file(self):
        self.assertTrue(os.path.exists(TEST_DB_PATH))

    def test_creates_table(self):
        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (TABLE_ARTICLE_LINKS,),
        )
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_idempotent(self):
        # Calling init_db twice should not error or lose data
        cache_article_links("Test", ["A"])
        init_db()
        self.assertEqual(get_cached_links("Test"), ["A"])


class TestCacheArticleLinks(_BaseDBTest):
    """cache_article_links should store and overwrite entries."""

    def test_store_and_retrieve(self):
        cache_article_links("Python", ["Link1", "Link2"])
        result = get_cached_links("Python")
        self.assertEqual(result, ["Link1", "Link2"])

    def test_overwrite_existing(self):
        cache_article_links("Python", ["Old"])
        cache_article_links("Python", ["New1", "New2"])
        self.assertEqual(get_cached_links("Python"), ["New1", "New2"])

    def test_empty_links_list(self):
        cache_article_links("Empty", [])
        self.assertEqual(get_cached_links("Empty"), [])

    def test_large_link_list(self):
        big = [f"Link_{i}" for i in range(2000)]
        cache_article_links("Big", big)
        self.assertEqual(get_cached_links("Big"), big)


class TestGetCachedLinks(_BaseDBTest):
    """get_cached_links should return None on miss / expiry."""

    def test_miss_returns_none(self):
        self.assertIsNone(get_cached_links("NonExistent"))

    def test_hit_returns_links(self):
        cache_article_links("Python", ["A", "B"])
        self.assertEqual(get_cached_links("Python"), ["A", "B"])

    def test_expired_returns_none(self):
        old_time = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 1)).isoformat()
        self._insert_with_timestamp("OldArticle", ["X"], old_time)
        self.assertIsNone(get_cached_links("OldArticle"))

    def test_expired_entry_is_deleted(self):
        old_time = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 1)).isoformat()
        self._insert_with_timestamp("OldArticle", ["X"], old_time)
        get_cached_links("OldArticle")  # triggers delete
        # Verify row is gone
        conn = sqlite3.connect(TEST_DB_PATH)
        row = conn.execute(
            f"SELECT * FROM {TABLE_ARTICLE_LINKS} WHERE article_title = ?",
            ("OldArticle",),
        ).fetchone()
        conn.close()
        self.assertIsNone(row)

    def test_not_yet_expired_returns_links(self):
        recent = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS - 1)).isoformat()
        self._insert_with_timestamp("Recent", ["Y"], recent)
        self.assertEqual(get_cached_links("Recent"), ["Y"])


class TestClearCache(_BaseDBTest):
    """clear_cache should remove specific or all entries."""

    def test_clear_specific(self):
        cache_article_links("A", ["1"])
        cache_article_links("B", ["2"])
        deleted = clear_cache("A")
        self.assertEqual(deleted, 1)
        self.assertIsNone(get_cached_links("A"))
        self.assertEqual(get_cached_links("B"), ["2"])

    def test_clear_all(self):
        cache_article_links("A", ["1"])
        cache_article_links("B", ["2"])
        cache_article_links("C", ["3"])
        deleted = clear_cache()
        self.assertEqual(deleted, 3)
        self.assertIsNone(get_cached_links("A"))
        self.assertIsNone(get_cached_links("B"))
        self.assertIsNone(get_cached_links("C"))

    def test_clear_nonexistent_returns_zero(self):
        self.assertEqual(clear_cache("Ghost"), 0)

    def test_clear_all_empty_returns_zero(self):
        self.assertEqual(clear_cache(), 0)


class TestGetCacheStats(_BaseDBTest):
    """get_cache_stats should return accurate statistics."""

    def test_empty_cache(self):
        stats = get_cache_stats()
        self.assertEqual(stats["total_articles"], 0)
        self.assertEqual(stats["total_links"], 0)
        self.assertIsNone(stats["oldest_entry"])
        self.assertIsNone(stats["newest_entry"])
        self.assertEqual(stats["expired_count"], 0)
        self.assertGreater(stats["cache_size_bytes"], 0)  # file exists

    def test_populated_cache(self):
        cache_article_links("A", ["L1", "L2"])
        cache_article_links("B", ["L3"])
        stats = get_cache_stats()
        self.assertEqual(stats["total_articles"], 2)
        self.assertEqual(stats["total_links"], 3)
        self.assertIsNotNone(stats["oldest_entry"])
        self.assertIsNotNone(stats["newest_entry"])

    def test_expired_count(self):
        old_time = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 5)).isoformat()
        self._insert_with_timestamp("Expired1", ["a"], old_time)
        self._insert_with_timestamp("Expired2", ["b"], old_time)
        cache_article_links("Fresh", ["c"])
        stats = get_cache_stats()
        self.assertEqual(stats["expired_count"], 2)
        self.assertEqual(stats["total_articles"], 3)


class TestCleanupExpired(_BaseDBTest):
    """cleanup_expired should remove only entries older than 30 days."""

    def test_removes_expired(self):
        old = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 1)).isoformat()
        self._insert_with_timestamp("Old", ["x"], old)
        cache_article_links("New", ["y"])
        deleted = cleanup_expired()
        self.assertEqual(deleted, 1)
        self.assertIsNone(get_cached_links("Old"))
        self.assertEqual(get_cached_links("New"), ["y"])

    def test_nothing_to_clean(self):
        cache_article_links("Fresh", ["a"])
        self.assertEqual(cleanup_expired(), 0)

    def test_all_expired(self):
        old = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS + 1)).isoformat()
        self._insert_with_timestamp("A", ["1"], old)
        self._insert_with_timestamp("B", ["2"], old)
        self.assertEqual(cleanup_expired(), 2)


if __name__ == "__main__":
    unittest.main()
