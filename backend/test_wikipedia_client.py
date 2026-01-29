"""
Unit tests for the Wikipedia Client Module

Tests title normalization, article validation, redirect handling,
link retrieval functionality, and SQLite cache integration.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Point the cache DB to an isolated test file before importing the client
# (import triggers init_db via module-level call)
import db as _db_module

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_client_cache.db")
_db_module.CACHE_DB_PATH = TEST_DB_PATH

from wikipedia_client import (
    normalize_title,
    validate_article,
    get_article_links,
    get_backlinks,
    get_cache_hit_stats,
    reset_cache_hit_stats,
    ArticleNotFoundError,
)
from db import init_db, clear_cache, get_cached_links


class TestNormalizeTitle(unittest.TestCase):
    """Tests for the normalize_title function."""

    def test_replaces_spaces_with_underscores(self):
        result = normalize_title("python programming")
        self.assertEqual(result, "Python_programming")

    def test_capitalizes_first_character(self):
        result = normalize_title("python")
        self.assertEqual(result, "Python")

    def test_preserves_existing_capitalization_after_first_char(self):
        result = normalize_title("PYTHON")
        self.assertEqual(result, "PYTHON")

    def test_handles_single_character(self):
        result = normalize_title("a")
        self.assertEqual(result, "A")

    def test_handles_empty_string(self):
        result = normalize_title("")
        self.assertEqual(result, "")

    def test_trims_whitespace(self):
        result = normalize_title("  python  ")
        self.assertEqual(result, "Python")

    def test_handles_underscores(self):
        result = normalize_title("python_programming")
        self.assertEqual(result, "Python_programming")

    def test_handles_special_characters(self):
        result = normalize_title("C++")
        self.assertEqual(result, "C++")

    def test_handles_parentheses(self):
        result = normalize_title("python (programming language)")
        self.assertEqual(result, "Python_(programming_language)")


class TestValidateArticle(unittest.TestCase):
    """Tests for the validate_article function."""

    @patch("wikipedia_client._make_request")
    def test_returns_canonical_title_for_valid_article(self, mock_request):
        mock_request.return_value = {
            "query": {
                "pages": {
                    "12345": {
                        "pageid": 12345,
                        "title": "Python (programming language)",
                    }
                }
            }
        }

        result = validate_article("Python_(programming_language)")
        self.assertEqual(result, "Python (programming language)")

    @patch("wikipedia_client._make_request")
    def test_raises_error_for_nonexistent_article(self, mock_request):
        mock_request.return_value = {
            "query": {
                "pages": {
                    "-1": {
                        "missing": "",
                        "title": "ThisArticleDoesNotExist12345",
                    }
                }
            }
        }

        with self.assertRaises(ArticleNotFoundError):
            validate_article("ThisArticleDoesNotExist12345")

    @patch("wikipedia_client._make_request")
    def test_follows_redirect(self, mock_request):
        # Simulating redirect from "Python" to "Python (programming language)"
        mock_request.return_value = {
            "query": {
                "redirects": [
                    {"from": "Python", "to": "Python (programming language)"}
                ],
                "pages": {
                    "12345": {
                        "pageid": 12345,
                        "title": "Python (programming language)",
                    }
                }
            }
        }

        result = validate_article("Python")
        self.assertEqual(result, "Python (programming language)")

    def test_raises_error_for_empty_title(self):
        with self.assertRaises(ArticleNotFoundError):
            validate_article("")

    def test_raises_error_for_whitespace_only_title(self):
        with self.assertRaises(ArticleNotFoundError):
            validate_article("   ")


class TestGetArticleLinks(unittest.TestCase):
    """Tests for the get_article_links function."""

    def setUp(self):
        """Ensure the test DB exists and clear any cached data."""
        _db_module.CACHE_DB_PATH = TEST_DB_PATH
        init_db()
        clear_cache()

    @patch("wikipedia_client._make_request")
    def test_returns_list_of_links(self, mock_request):
        mock_request.return_value = {
            "query": {
                "pages": {
                    "12345": {
                        "pageid": 12345,
                        "title": "Python (programming language)",
                        "links": [
                            {"ns": 0, "title": "Computer science"},
                            {"ns": 0, "title": "Programming language"},
                            {"ns": 0, "title": "Object-oriented programming"},
                        ]
                    }
                }
            }
        }

        result = get_article_links("Python (programming language)")
        self.assertEqual(len(result), 3)
        self.assertIn("Computer science", result)
        self.assertIn("Programming language", result)
        self.assertIn("Object-oriented programming", result)

    @patch("wikipedia_client._make_request")
    def test_filters_namespace_0_only(self, mock_request):
        mock_request.return_value = {
            "query": {
                "pages": {
                    "12345": {
                        "pageid": 12345,
                        "title": "Test",
                        "links": [
                            {"ns": 0, "title": "Valid Article"},
                            {"ns": 0, "title": "Category:Programming"},  # Should be filtered
                            {"ns": 0, "title": "File:Example.png"},  # Should be filtered
                        ]
                    }
                }
            }
        }

        result = get_article_links("Test")
        self.assertEqual(len(result), 1)
        self.assertIn("Valid Article", result)
        self.assertNotIn("Category:Programming", result)
        self.assertNotIn("File:Example.png", result)

    @patch("wikipedia_client._make_request")
    def test_handles_pagination(self, mock_request):
        # First call returns partial results with continuation
        mock_request.side_effect = [
            {
                "query": {
                    "pages": {
                        "12345": {
                            "pageid": 12345,
                            "title": "Test",
                            "links": [
                                {"ns": 0, "title": "Article 1"},
                                {"ns": 0, "title": "Article 2"},
                            ]
                        }
                    }
                },
                "continue": {
                    "plcontinue": "12345|0|Article_3"
                }
            },
            {
                "query": {
                    "pages": {
                        "12345": {
                            "pageid": 12345,
                            "title": "Test",
                            "links": [
                                {"ns": 0, "title": "Article 3"},
                                {"ns": 0, "title": "Article 4"},
                            ]
                        }
                    }
                }
            }
        ]

        result = get_article_links("Test")
        self.assertEqual(len(result), 4)
        self.assertIn("Article 1", result)
        self.assertIn("Article 4", result)

    @patch("wikipedia_client._make_request")
    def test_returns_empty_list_for_missing_article(self, mock_request):
        mock_request.return_value = {
            "query": {
                "pages": {
                    "-1": {
                        "missing": "",
                        "title": "NonexistentArticle",
                    }
                }
            }
        }

        result = get_article_links("NonexistentArticle")
        self.assertEqual(result, [])

    @patch("wikipedia_client._make_request")
    def test_excludes_special_namespaces(self, mock_request):
        mock_request.return_value = {
            "query": {
                "pages": {
                    "12345": {
                        "pageid": 12345,
                        "title": "Test",
                        "links": [
                            {"ns": 0, "title": "Valid Article"},
                            {"ns": 0, "title": "Wikipedia:Manual of Style"},
                            {"ns": 0, "title": "Template:Infobox"},
                            {"ns": 0, "title": "Help:Contents"},
                            {"ns": 0, "title": "Portal:Science"},
                        ]
                    }
                }
            }
        }

        result = get_article_links("Test")
        self.assertEqual(len(result), 1)
        self.assertIn("Valid Article", result)


class _CacheTestBase(unittest.TestCase):
    """Base class that resets cache state between tests."""

    def setUp(self):
        _db_module.CACHE_DB_PATH = TEST_DB_PATH
        init_db()
        clear_cache()
        reset_cache_hit_stats()

    def tearDown(self):
        clear_cache()
        reset_cache_hit_stats()


class TestGetArticleLinksCacheIntegration(_CacheTestBase):
    """Tests that get_article_links uses the SQLite cache correctly."""

    _API_RESPONSE = {
        "query": {
            "pages": {
                "1": {
                    "pageid": 1,
                    "title": "TestArticle",
                    "links": [
                        {"ns": 0, "title": "Link_A"},
                        {"ns": 0, "title": "Link_B"},
                    ],
                }
            }
        }
    }

    @patch("wikipedia_client._make_request")
    def test_cache_miss_calls_api_and_stores(self, mock_request):
        """First call should hit the API and store in cache."""
        mock_request.return_value = self._API_RESPONSE

        result = get_article_links("TestArticle")

        self.assertEqual(result, ["Link_A", "Link_B"])
        mock_request.assert_called_once()
        # Verify data is now in the cache
        cached = get_cached_links("TestArticle")
        self.assertEqual(cached, ["Link_A", "Link_B"])

    @patch("wikipedia_client._make_request")
    def test_cache_hit_skips_api(self, mock_request):
        """Second call should return cached data without API call."""
        mock_request.return_value = self._API_RESPONSE

        # First call — populates cache
        get_article_links("TestArticle")
        mock_request.reset_mock()

        # Second call — should NOT call the API
        result = get_article_links("TestArticle")
        self.assertEqual(result, ["Link_A", "Link_B"])
        mock_request.assert_not_called()

    @patch("wikipedia_client._make_request")
    def test_cache_miss_counter(self, mock_request):
        mock_request.return_value = self._API_RESPONSE
        reset_cache_hit_stats()

        get_article_links("TestArticle")

        stats = get_cache_hit_stats()
        self.assertEqual(stats["cache_misses"], 1)
        self.assertEqual(stats["cache_hits"], 0)

    @patch("wikipedia_client._make_request")
    def test_cache_hit_counter(self, mock_request):
        mock_request.return_value = self._API_RESPONSE
        reset_cache_hit_stats()

        get_article_links("TestArticle")  # miss
        get_article_links("TestArticle")  # hit

        stats = get_cache_hit_stats()
        self.assertEqual(stats["cache_misses"], 1)
        self.assertEqual(stats["cache_hits"], 1)

    @patch("wikipedia_client._make_request")
    def test_empty_result_is_cached(self, mock_request):
        """Even an empty link list should be cached to avoid repeated API calls."""
        mock_request.return_value = {
            "query": {
                "pages": {
                    "-1": {"missing": "", "title": "NoLinks"}
                }
            }
        }

        get_article_links("NoLinks")
        mock_request.reset_mock()

        result = get_article_links("NoLinks")
        self.assertEqual(result, [])
        mock_request.assert_not_called()


class TestGetBacklinksCacheIntegration(_CacheTestBase):
    """Tests that get_backlinks uses the SQLite cache correctly."""

    _BL_RESPONSE = {
        "query": {
            "backlinks": [
                {"pageid": 10, "title": "Page_X"},
                {"pageid": 11, "title": "Page_Y"},
            ]
        }
    }

    @patch("wikipedia_client._make_request")
    def test_cache_miss_calls_api_and_stores(self, mock_request):
        mock_request.return_value = self._BL_RESPONSE

        result = get_backlinks("Target")

        self.assertEqual(result, ["Page_X", "Page_Y"])
        mock_request.assert_called_once()
        cached = get_cached_links("backlinks::Target")
        self.assertEqual(cached, ["Page_X", "Page_Y"])

    @patch("wikipedia_client._make_request")
    def test_cache_hit_skips_api(self, mock_request):
        mock_request.return_value = self._BL_RESPONSE

        get_backlinks("Target")
        mock_request.reset_mock()

        result = get_backlinks("Target")
        self.assertEqual(result, ["Page_X", "Page_Y"])
        mock_request.assert_not_called()

    @patch("wikipedia_client._make_request")
    def test_backlinks_counters(self, mock_request):
        mock_request.return_value = self._BL_RESPONSE
        reset_cache_hit_stats()

        get_backlinks("Target")  # miss
        get_backlinks("Target")  # hit

        stats = get_cache_hit_stats()
        self.assertEqual(stats["cache_misses"], 1)
        self.assertEqual(stats["cache_hits"], 1)


class TestResetCacheHitStats(_CacheTestBase):
    """reset_cache_hit_stats should zero out counters."""

    @patch("wikipedia_client._make_request")
    def test_reset(self, mock_request):
        mock_request.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "pageid": 1,
                        "title": "X",
                        "links": [{"ns": 0, "title": "Y"}],
                    }
                }
            }
        }

        get_article_links("X")
        get_article_links("X")
        reset_cache_hit_stats()

        stats = get_cache_hit_stats()
        self.assertEqual(stats["cache_hits"], 0)
        self.assertEqual(stats["cache_misses"], 0)


class TestIntegration(unittest.TestCase):
    """Integration tests using real Wikipedia API (marked for optional execution)."""

    @unittest.skipUnless(
        False,  # Set to True to run integration tests
        "Integration tests disabled by default"
    )
    def test_real_validate_article(self):
        result = validate_article("Python_(programming_language)")
        self.assertEqual(result, "Python (programming language)")

    @unittest.skipUnless(
        False,  # Set to True to run integration tests
        "Integration tests disabled by default"
    )
    def test_real_get_article_links(self):
        result = get_article_links("Python_(programming_language)")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
