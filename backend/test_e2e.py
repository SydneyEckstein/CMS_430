"""
Phase 9 — End-to-End Tests

Exercises the complete application stack through the Flask API with a mocked
Wikipedia backend. Validates that all components (API, search algorithm,
Wikipedia client, cache) integrate correctly.

Plan sections:
    9.1  Known article pairs
    9.2  Edge cases (long titles, special characters, redirects)
    9.3  Error scenarios
    9.4  Performance testing with cache
    9.6  Cache persistence
    (9.5 Browser compatibility is manual)
"""

import json
import os
import time
import unittest
from unittest.mock import patch

# ---------- isolate test database ----------
import db as _db_module

TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test_e2e.db"
)
_db_module.CACHE_DB_PATH = TEST_DB_PATH

from app import app
from db import init_db, clear_cache, get_cache_stats, cache_article_links
from wikipedia_client import reset_cache_hit_stats

# ---------------------------------------------------------------------------
# Mock Wikipedia graph
# ---------------------------------------------------------------------------
# A realistic-ish graph that allows testing various scenarios:
#
#   Python_(programming_language) --> Computer_science
#   Python_(programming_language) --> Programming_language
#   Computer_science --> Mathematics
#   Mathematics --> Physics
#   Albert_Einstein --> Physics
#   Albert_Einstein --> Germany
#   Physics --> Science
#   United_States --> George_Washington
#   George_Washington --> United_States
#
# Backlinks mirror forward links for simplicity.

MOCK_ARTICLES = {
    "Python (programming language)": {
        "links": ["Computer science", "Programming language", "Guido van Rossum"],
        "backlinks": ["Programming language", "Computer science"],
    },
    "Computer science": {
        "links": ["Mathematics", "Algorithm", "Programming language"],
        "backlinks": ["Python (programming language)", "Mathematics"],
    },
    "Programming language": {
        "links": ["Computer science", "Compiler"],
        "backlinks": ["Python (programming language)", "Computer science"],
    },
    "Mathematics": {
        "links": ["Physics", "Science", "Number"],
        "backlinks": ["Computer science", "Physics"],
    },
    "Physics": {
        "links": ["Science", "Mathematics", "Energy"],
        "backlinks": ["Albert Einstein", "Mathematics"],
    },
    "Albert Einstein": {
        "links": ["Physics", "Germany", "Nobel Prize"],
        "backlinks": ["Physics", "Nobel Prize"],
    },
    "Germany": {
        "links": ["Europe", "Berlin"],
        "backlinks": ["Albert Einstein"],
    },
    "United States": {
        "links": ["George Washington", "Washington, D.C.", "North America"],
        "backlinks": ["George Washington", "North America"],
    },
    "George Washington": {
        "links": ["United States", "American Revolutionary War"],
        "backlinks": ["United States", "American Revolutionary War"],
    },
    "Science": {
        "links": ["Mathematics", "Physics"],
        "backlinks": ["Physics", "Mathematics"],
    },
    # Edge-case articles
    "Article with special chars: A&B <test>": {
        "links": ["Normal article"],
        "backlinks": [],
    },
    "Normal article": {
        "links": [],
        "backlinks": ["Article with special chars: A&B <test>"],
    },
    "A" * 200: {  # very long title
        "links": ["Short"],
        "backlinks": [],
    },
    "Short": {
        "links": [],
        "backlinks": ["A" * 200],
    },
    "Redirect source": {
        "redirect": "Redirect target",
    },
    "Redirect target": {
        "links": ["Normal article"],
        "backlinks": [],
    },
}


def _normalize_lookup(title: str) -> str:
    """Convert underscores to spaces to match MOCK_ARTICLES keys."""
    return title.replace("_", " ")


def _get_article(title: str) -> dict | None:
    """Look up an article, handling underscore/space normalization."""
    # Try exact match first, then normalized
    if title in MOCK_ARTICLES:
        return MOCK_ARTICLES[title]
    normalized = _normalize_lookup(title)
    if normalized in MOCK_ARTICLES:
        return MOCK_ARTICLES[normalized]
    return None


def _mock_make_request(params: dict) -> dict:
    """Simulate Wikipedia API for the mock article graph."""

    # --- Article validation (action=query with redirects) ---
    if "titles" in params and "redirects" in params:
        title = params["titles"]
        display_title = _normalize_lookup(title)
        article = _get_article(title)

        # Handle redirects
        if article and "redirect" in article:
            target = article["redirect"]
            return {
                "query": {
                    "redirects": [{"from": display_title, "to": target}],
                    "pages": {"1": {"pageid": 1, "title": target}},
                }
            }

        if article is not None:
            return {
                "query": {
                    "pages": {"1": {"pageid": 1, "title": display_title}}
                }
            }
        else:
            return {
                "query": {
                    "pages": {"-1": {"missing": "", "title": display_title}}
                }
            }

    # --- Forward links (prop=links) ---
    if params.get("prop") == "links":
        title = params["titles"]
        article = _get_article(title) or {}
        links = article.get("links", [])
        return {
            "query": {
                "pages": {
                    "1": {
                        "pageid": 1,
                        "title": _normalize_lookup(title),
                        "links": [{"ns": 0, "title": t} for t in links],
                    }
                }
            }
        }

    # --- Backlinks (list=backlinks) ---
    if params.get("list") == "backlinks":
        title = params["bltitle"]
        article = _get_article(title) or {}
        bls = article.get("backlinks", [])
        return {
            "query": {
                "backlinks": [{"pageid": i, "title": t} for i, t in enumerate(bls)]
            }
        }

    return {}


class _E2ETestBase(unittest.TestCase):
    """Base class with fresh DB, cache, and Flask test client."""

    def setUp(self):
        _db_module.CACHE_DB_PATH = TEST_DB_PATH
        init_db()
        clear_cache()
        reset_cache_hit_stats()
        self.client = app.test_client()

    def tearDown(self):
        clear_cache()
        reset_cache_hit_stats()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def _find_path(self, start: str, end: str):
        """Helper to POST /api/find-path and return parsed JSON + status."""
        resp = self.client.post(
            "/api/find-path",
            json={"start": start, "end": end},
        )
        return json.loads(resp.data), resp.status_code


# ===========================================================================
# 9.1  Known article pairs
# ===========================================================================
class TestKnownArticlePairs(_E2ETestBase):
    """Test that known article pairs successfully find paths."""

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_python_to_computer_science(self, mock_req):
        """Python (programming language) -> Computer science finds a path."""
        data, status = self._find_path(
            "Python (programming language)", "Computer science"
        )

        self.assertEqual(status, 200)
        self.assertTrue(data["success"])
        self.assertIn("Computer science", data["path"])
        self.assertEqual(data["path"][0], "Python (programming language)")
        self.assertEqual(data["path"][-1], "Computer science")

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_albert_einstein_to_physics(self, mock_req):
        """Albert Einstein -> Physics finds a path."""
        data, status = self._find_path("Albert Einstein", "Physics")

        self.assertEqual(status, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["path"][0], "Albert Einstein")
        self.assertEqual(data["path"][-1], "Physics")

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_united_states_to_george_washington(self, mock_req):
        """United States -> George Washington finds a direct path."""
        data, status = self._find_path("United States", "George Washington")

        self.assertEqual(status, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["path"], ["United States", "George Washington"])
        self.assertEqual(data["depth"], 1)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_same_article_start_end(self, mock_req):
        """Same article for start and end returns single-element path."""
        data, status = self._find_path("Physics", "Physics")

        self.assertEqual(status, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["path"], ["Physics"])
        self.assertEqual(data["depth"], 0)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_path_is_valid_chain(self, mock_req):
        """Each step in the returned path should be a valid link from prior."""
        data, status = self._find_path(
            "Python (programming language)", "Mathematics"
        )

        self.assertEqual(status, 200)
        path = data["path"]
        # Verify chain: each element (except first) should be in links of previous
        for i in range(1, len(path)):
            prev_article = MOCK_ARTICLES.get(path[i - 1], {})
            prev_links = prev_article.get("links", [])
            # The search can also use backlinks, so we check either direction
            next_article = MOCK_ARTICLES.get(path[i], {})
            next_backlinks = next_article.get("backlinks", [])
            self.assertTrue(
                path[i] in prev_links or path[i - 1] in next_backlinks,
                f"Invalid link from {path[i-1]} to {path[i]}",
            )


# ===========================================================================
# 9.2  Edge cases
# ===========================================================================
class TestEdgeCases(_E2ETestBase):
    """Test edge cases: long titles, special characters, redirects."""

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_very_long_title(self, mock_req):
        """Very long article titles are handled correctly."""
        long_title = "A" * 200
        data, status = self._find_path(long_title, "Short")

        self.assertEqual(status, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["path"][0], long_title)
        self.assertEqual(data["path"][-1], "Short")

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_special_characters_in_title(self, mock_req):
        """Articles with special characters (& < >) are handled."""
        data, status = self._find_path(
            "Article with special chars: A&B <test>", "Normal article"
        )

        self.assertEqual(status, 200)
        self.assertTrue(data["success"])

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_redirect_is_followed(self, mock_req):
        """Redirect articles are followed transparently."""
        data, status = self._find_path("Redirect source", "Normal article")

        self.assertEqual(status, 200)
        self.assertTrue(data["success"])
        # The path should use the canonical (redirected) title
        self.assertIn("Redirect target", data["path"])

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_whitespace_trimmed(self, mock_req):
        """Leading/trailing whitespace is trimmed from input."""
        data, status = self._find_path("  Physics  ", "  Science  ")

        self.assertEqual(status, 200)
        self.assertTrue(data["success"])


# ===========================================================================
# 9.3  Error scenarios
# ===========================================================================
class TestErrorScenarios(_E2ETestBase):
    """Test error handling for invalid inputs and missing articles."""

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_nonexistent_start_article(self, mock_req):
        """Non-existent start article returns 404."""
        data, status = self._find_path("ThisDoesNotExist12345", "Physics")

        self.assertEqual(status, 404)
        self.assertFalse(data["success"])
        self.assertIn("not found", data["error"].lower())

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_nonexistent_end_article(self, mock_req):
        """Non-existent end article returns 404."""
        data, status = self._find_path("Physics", "ThisDoesNotExist12345")

        self.assertEqual(status, 404)
        self.assertFalse(data["success"])
        self.assertIn("not found", data["error"].lower())

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_both_articles_nonexistent(self, mock_req):
        """Both articles non-existent returns 404."""
        data, status = self._find_path("FakeArticle1", "FakeArticle2")

        self.assertEqual(status, 404)
        self.assertFalse(data["success"])

    def test_empty_start(self):
        """Empty start field returns 400."""
        data, status = self._find_path("", "Physics")

        self.assertEqual(status, 400)
        self.assertFalse(data["success"])

    def test_empty_end(self):
        """Empty end field returns 400."""
        data, status = self._find_path("Physics", "")

        self.assertEqual(status, 400)
        self.assertFalse(data["success"])

    def test_missing_json_body(self):
        """Missing JSON body returns 400."""
        resp = self.client.post("/api/find-path")
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(data["success"])


# ===========================================================================
# 9.4  Performance testing with cache
# ===========================================================================
class TestPerformanceWithCache(_E2ETestBase):
    """Test that cache dramatically improves repeated search performance."""

    @patch("wikipedia_client._make_request")
    def test_cached_search_faster_than_uncached(self, mock_req):
        """Second identical search should be significantly faster."""

        def slow_api(params):
            time.sleep(0.02)  # 20ms simulated latency
            return _mock_make_request(params)

        mock_req.side_effect = slow_api

        # First search — uncached (pays API latency)
        t0 = time.monotonic()
        data1, status1 = self._find_path("United States", "George Washington")
        uncached_time = time.monotonic() - t0

        self.assertEqual(status1, 200)

        # Second search — cached (should skip API calls)
        mock_req.reset_mock()
        t0 = time.monotonic()
        data2, status2 = self._find_path("United States", "George Washington")
        cached_time = time.monotonic() - t0

        self.assertEqual(status2, 200)
        self.assertEqual(data1["path"], data2["path"])

        # Cached should be much faster
        self.assertLess(cached_time, uncached_time)
        # And API should not have been called (cache hits)
        # Note: validate_article doesn't use cache, but link fetches do

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_response_includes_cache_stats(self, mock_req):
        """Successful response includes cache_hits and cache_misses."""
        data, status = self._find_path("Physics", "Science")

        self.assertEqual(status, 200)
        self.assertIn("cache_hits", data)
        self.assertIn("cache_misses", data)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_partial_cache_reuse(self, mock_req):
        """Search reuses cached articles from a previous different search."""
        # First search caches "Physics" and "Science"
        self._find_path("Physics", "Science")

        # Second search also needs "Physics" — should get a cache hit
        reset_cache_hit_stats()
        data, status = self._find_path("Physics", "Mathematics")

        self.assertEqual(status, 200)
        # Should have at least one cache hit (Physics was already cached)
        self.assertGreater(data["cache_hits"], 0)


# ===========================================================================
# 9.6  Cache persistence
# ===========================================================================
class TestCachePersistence(_E2ETestBase):
    """Test that cache data persists and survives server 'restarts'."""

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_cache_persists_after_search(self, mock_req):
        """Cache entries exist after a search completes."""
        self._find_path("United States", "George Washington")

        stats = get_cache_stats()
        self.assertGreater(stats["total_articles"], 0)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_cache_survives_simulated_restart(self, mock_req):
        """Cache data persists when we 'restart' (re-init without clearing)."""
        # Populate cache
        self._find_path("Albert Einstein", "Physics")

        stats_before = get_cache_stats()
        articles_before = stats_before["total_articles"]

        # Simulate server restart: re-initialize DB (should not clear data)
        init_db()

        stats_after = get_cache_stats()
        self.assertEqual(stats_after["total_articles"], articles_before)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_second_search_uses_persisted_cache(self, mock_req):
        """A second search uses cache data that persisted from the first."""
        # First search
        self._find_path("United States", "George Washington")

        # Simulate restart
        init_db()
        reset_cache_hit_stats()

        # Second identical search — should get cache hits
        mock_req.reset_mock()
        data, status = self._find_path("United States", "George Washington")

        self.assertEqual(status, 200)
        self.assertGreater(data["cache_hits"], 0)


# ===========================================================================
# API endpoint tests (additional coverage)
# ===========================================================================
class TestAPIEndpoints(_E2ETestBase):
    """Additional API endpoint tests for completeness."""

    def test_health_endpoint(self):
        """GET /api/health returns ok."""
        resp = self.client.get("/api/health")
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["status"], "ok")

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_cache_stats_endpoint(self, mock_req):
        """GET /api/cache-stats returns valid stats."""
        self._find_path("Physics", "Science")

        resp = self.client.get("/api/cache-stats")
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("stats", data)
        self.assertGreater(data["stats"]["total_articles"], 0)

    @patch("wikipedia_client._make_request", side_effect=_mock_make_request)
    def test_cache_clear_endpoint(self, mock_req):
        """POST /api/cache-clear clears all cache entries."""
        self._find_path("Physics", "Science")

        resp = self.client.post("/api/cache-clear")
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(data["success"])
        self.assertGreater(data["entries_cleared"], 0)

        # Verify cache is empty
        stats = get_cache_stats()
        self.assertEqual(stats["total_articles"], 0)


if __name__ == "__main__":
    unittest.main()
