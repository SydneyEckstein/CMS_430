"""
Unit tests for the Flask Backend API

Tests the REST API endpoints including:
- Health check
- Successful path finding
- Validation errors
- Article not found errors
- Error response format
- Cache statistics endpoint
- Cache clearing endpoint
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import json

# Isolate the cache database used during tests
import db as _db_module

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_app_cache.db")
_db_module.CACHE_DB_PATH = TEST_DB_PATH

from app import app
from search import SearchResult, NoPathFoundError
from wikipedia_client import ArticleNotFoundError
from db import init_db, cache_article_links, clear_cache as db_clear_cache


class TestHealthEndpoint(unittest.TestCase):
    """Tests for the /api/health endpoint."""

    def setUp(self):
        self.client = app.test_client()

    def test_health_returns_ok(self):
        """GET /api/health returns 200 with status ok."""
        response = self.client.get('/api/health')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')


class TestFindPathValidation(unittest.TestCase):
    """Tests for request validation on /api/find-path."""

    def setUp(self):
        self.client = app.test_client()

    def test_missing_json_body_returns_400(self):
        """Request without JSON body returns 400."""
        response = self.client.post('/api/find-path')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_missing_start_field_returns_400(self):
        """Missing 'start' field returns 400."""
        response = self.client.post(
            '/api/find-path',
            json={'end': 'Article'}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('start', data['error'].lower())

    def test_missing_end_field_returns_400(self):
        """Missing 'end' field returns 400."""
        response = self.client.post(
            '/api/find-path',
            json={'start': 'Article'}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('end', data['error'].lower())

    def test_empty_start_returns_400(self):
        """Empty 'start' field returns 400."""
        response = self.client.post(
            '/api/find-path',
            json={'start': '', 'end': 'Article'}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('start', data['error'].lower())
        self.assertIn('empty', data['error'].lower())

    def test_empty_end_returns_400(self):
        """Empty 'end' field returns 400."""
        response = self.client.post(
            '/api/find-path',
            json={'start': 'Article', 'end': ''}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('end', data['error'].lower())
        self.assertIn('empty', data['error'].lower())

    def test_whitespace_only_start_returns_400(self):
        """Whitespace-only 'start' field returns 400."""
        response = self.client.post(
            '/api/find-path',
            json={'start': '   ', 'end': 'Article'}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_non_string_start_returns_400(self):
        """Non-string 'start' field returns 400."""
        response = self.client.post(
            '/api/find-path',
            json={'start': 123, 'end': 'Article'}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])


class TestFindPathSuccess(unittest.TestCase):
    """Tests for successful path finding."""

    def setUp(self):
        self.client = app.test_client()

    @patch('app.search_find_path')
    def test_successful_search_returns_200(self, mock_search):
        """Successful search returns 200 with path data."""
        mock_search.return_value = SearchResult(
            path=['Article A', 'Article B', 'Article C'],
            depth=2,
            pages_explored=150
        )

        response = self.client.post(
            '/api/find-path',
            json={'start': 'Article A', 'end': 'Article C'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['path'], ['Article A', 'Article B', 'Article C'])
        self.assertEqual(data['depth'], 2)
        self.assertEqual(data['pages_explored'], 150)

    @patch('app.search_find_path')
    def test_same_start_end_returns_200(self, mock_search):
        """Same start and end returns 200 with single-element path."""
        mock_search.return_value = SearchResult(
            path=['Article A'],
            depth=0,
            pages_explored=1
        )

        response = self.client.post(
            '/api/find-path',
            json={'start': 'Article A', 'end': 'Article A'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['path'], ['Article A'])
        self.assertEqual(data['depth'], 0)

    @patch('app.search_find_path')
    def test_response_includes_required_fields(self, mock_search):
        """Successful response includes success, path, depth, pages_explored, cache stats."""
        mock_search.return_value = SearchResult(
            path=['A', 'B'],
            depth=1,
            pages_explored=100
        )

        response = self.client.post(
            '/api/find-path',
            json={'start': 'A', 'end': 'B'}
        )

        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('path', data)
        self.assertIn('depth', data)
        self.assertIn('pages_explored', data)
        self.assertIn('cache_hits', data)
        self.assertIn('cache_misses', data)


class TestFindPathErrors(unittest.TestCase):
    """Tests for error handling."""

    def setUp(self):
        self.client = app.test_client()

    @patch('app.search_find_path')
    def test_start_article_not_found_returns_404(self, mock_search):
        """Non-existent start article returns 404."""
        mock_search.side_effect = ArticleNotFoundError(
            "Article not found: NonExistent"
        )

        response = self.client.post(
            '/api/find-path',
            json={'start': 'NonExistent', 'end': 'Python'}
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('not found', data['error'].lower())

    @patch('app.search_find_path')
    def test_end_article_not_found_returns_404(self, mock_search):
        """Non-existent end article returns 404."""
        mock_search.side_effect = ArticleNotFoundError(
            "Article not found: NonExistent"
        )

        response = self.client.post(
            '/api/find-path',
            json={'start': 'Python', 'end': 'NonExistent'}
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('not found', data['error'].lower())

    @patch('app.search_find_path')
    def test_no_path_found_returns_404(self, mock_search):
        """No path within depth limit returns 404."""
        mock_search.side_effect = NoPathFoundError(
            "No path found between 'A' and 'B'"
        )

        response = self.client.post(
            '/api/find-path',
            json={'start': 'A', 'end': 'B'}
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('no path', data['error'].lower())

    @patch('app.search_find_path')
    def test_unexpected_error_returns_500(self, mock_search):
        """Unexpected error returns 500."""
        mock_search.side_effect = Exception("Unexpected error")

        response = self.client.post(
            '/api/find-path',
            json={'start': 'A', 'end': 'B'}
        )

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)


class TestCORS(unittest.TestCase):
    """Tests for CORS headers."""

    def setUp(self):
        self.client = app.test_client()

    def test_cors_headers_present(self):
        """CORS headers are present in responses."""
        response = self.client.options(
            '/api/find-path',
            headers={'Origin': 'http://localhost:3000'}
        )

        # Flask-CORS should handle the preflight request
        self.assertIn(response.status_code, [200, 204])


class TestErrorResponseFormat(unittest.TestCase):
    """Tests for consistent error response format."""

    def setUp(self):
        self.client = app.test_client()

    def test_error_response_has_success_false(self):
        """All error responses have success: false."""
        response = self.client.post(
            '/api/find-path',
            json={'start': '', 'end': 'B'}
        )

        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_error_response_has_error_message(self):
        """All error responses have an error message."""
        response = self.client.post(
            '/api/find-path',
            json={'start': '', 'end': 'B'}
        )

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertTrue(len(data['error']) > 0)


class TestCacheStatsEndpoint(unittest.TestCase):
    """Tests for GET /api/cache-stats."""

    def setUp(self):
        _db_module.CACHE_DB_PATH = TEST_DB_PATH
        init_db()
        db_clear_cache()
        self.client = app.test_client()

    def tearDown(self):
        db_clear_cache()

    def test_returns_200_with_stats(self):
        """GET /api/cache-stats returns 200 with valid stats structure."""
        response = self.client.get('/api/cache-stats')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('stats', data)

        stats = data['stats']
        self.assertIn('total_articles', stats)
        self.assertIn('total_links', stats)
        self.assertIn('oldest_entry', stats)
        self.assertIn('newest_entry', stats)
        self.assertIn('cache_size_bytes', stats)
        self.assertIn('expired_count', stats)

    def test_empty_cache_stats(self):
        """Empty cache returns zero counts."""
        response = self.client.get('/api/cache-stats')
        data = json.loads(response.data)
        stats = data['stats']

        self.assertEqual(stats['total_articles'], 0)
        self.assertEqual(stats['total_links'], 0)
        self.assertIsNone(stats['oldest_entry'])
        self.assertIsNone(stats['newest_entry'])

    def test_populated_cache_stats(self):
        """Stats reflect actual cached data."""
        cache_article_links("Article_A", ["Link1", "Link2", "Link3"])
        cache_article_links("Article_B", ["Link4"])

        response = self.client.get('/api/cache-stats')
        data = json.loads(response.data)
        stats = data['stats']

        self.assertEqual(stats['total_articles'], 2)
        self.assertEqual(stats['total_links'], 4)
        self.assertIsNotNone(stats['oldest_entry'])
        self.assertIsNotNone(stats['newest_entry'])
        self.assertGreater(stats['cache_size_bytes'], 0)


class TestCacheClearEndpoint(unittest.TestCase):
    """Tests for POST /api/cache-clear."""

    def setUp(self):
        _db_module.CACHE_DB_PATH = TEST_DB_PATH
        init_db()
        db_clear_cache()
        self.client = app.test_client()

    def tearDown(self):
        db_clear_cache()

    def test_clear_all_returns_200(self):
        """POST /api/cache-clear with no body clears entire cache."""
        cache_article_links("A", ["x"])
        cache_article_links("B", ["y"])

        response = self.client.post('/api/cache-clear')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entries_cleared'], 2)
        self.assertIn('message', data)

    def test_clear_specific_article(self):
        """POST /api/cache-clear with article param clears only that entry."""
        cache_article_links("Keep", ["a"])
        cache_article_links("Remove", ["b"])

        response = self.client.post(
            '/api/cache-clear',
            json={'article': 'Remove'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entries_cleared'], 1)

        # Verify "Keep" is still there
        stats_resp = self.client.get('/api/cache-stats')
        stats = json.loads(stats_resp.data)['stats']
        self.assertEqual(stats['total_articles'], 1)

    def test_clear_nonexistent_article_returns_zero(self):
        """Clearing a non-cached article returns entries_cleared=0."""
        response = self.client.post(
            '/api/cache-clear',
            json={'article': 'DoesNotExist'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entries_cleared'], 0)

    def test_empty_article_string_returns_400(self):
        """Empty article string returns 400."""
        response = self.client.post(
            '/api/cache-clear',
            json={'article': ''}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_clear_empty_cache_returns_zero(self):
        """Clearing an already-empty cache returns entries_cleared=0."""
        response = self.client.post('/api/cache-clear')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['entries_cleared'], 0)


if __name__ == '__main__':
    unittest.main()
