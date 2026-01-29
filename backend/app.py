"""
Wikipedia Chain Finder - Flask Application

This module provides the REST API for the Wikipedia Chain Finder:
- GET  /api/health      - Health check endpoint
- POST /api/find-path   - Find shortest path between two Wikipedia articles
- GET  /api/cache-stats - Return SQLite link-cache statistics
- POST /api/cache-clear - Clear cached links (all or specific article)

The frontend is served as static files from the frontend directory.
"""

import logging
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

from search import find_path as search_find_path, SearchResult, NoPathFoundError
from wikipedia_client import (
    ArticleNotFoundError,
    RateLimitError,
    get_cache_hit_stats,
    reset_cache_hit_stats,
)
from db import get_cache_stats, clear_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)


@app.route('/')
def index():
    """Serve the frontend application."""
    return app.send_static_file('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the server is running."""
    return jsonify({'status': 'ok'})


@app.route('/api/find-path', methods=['POST'])
def find_path():
    """
    Find the shortest path between two Wikipedia articles.

    Request body (JSON):
        {
            "start": "Article_Title",
            "end": "Article_Title"
        }

    Response (JSON):
        Success (200):
            {
                "success": true,
                "path": ["Article1", "Article2", ...],
                "depth": 3,
                "pages_explored": 150
            }
        Error (400/404/500):
            {
                "success": false,
                "error": "Descriptive error message"
            }
    """
    start_time = time.time()

    # Parse JSON body
    try:
        data = request.get_json()
        if data is None:
            logger.warning("Request missing JSON body")
            return jsonify({
                'success': False,
                'error': 'Request body must be JSON'
            }), 400
    except Exception as e:
        logger.warning(f"Invalid JSON in request: {e}")
        return jsonify({
            'success': False,
            'error': 'Invalid JSON in request body'
        }), 400

    # Validate required fields
    if 'start' not in data:
        logger.warning("Request missing 'start' field")
        return jsonify({
            'success': False,
            'error': "Missing required field: 'start'"
        }), 400

    if 'end' not in data:
        logger.warning("Request missing 'end' field")
        return jsonify({
            'success': False,
            'error': "Missing required field: 'end'"
        }), 400

    # Get and trim values
    start = data['start']
    end = data['end']

    # Validate types
    if not isinstance(start, str):
        logger.warning(f"'start' field is not a string: {type(start)}")
        return jsonify({
            'success': False,
            'error': "'start' must be a string"
        }), 400

    if not isinstance(end, str):
        logger.warning(f"'end' field is not a string: {type(end)}")
        return jsonify({
            'success': False,
            'error': "'end' must be a string"
        }), 400

    # Trim whitespace
    start = start.strip()
    end = end.strip()

    # Check for empty fields
    if not start:
        logger.warning("Empty 'start' field")
        return jsonify({
            'success': False,
            'error': "'start' article title cannot be empty"
        }), 400

    if not end:
        logger.warning("Empty 'end' field")
        return jsonify({
            'success': False,
            'error': "'end' article title cannot be empty"
        }), 400

    logger.info(f"Search request: '{start}' -> '{end}'")

    # Reset per-request cache counters
    reset_cache_hit_stats()

    # Perform the search
    try:
        result = search_find_path(start, end)

        elapsed_time = time.time() - start_time
        cache_stats = get_cache_hit_stats()
        logger.info(
            f"Search successful: '{start}' -> '{end}' | "
            f"Depth: {result.depth} | "
            f"Pages explored: {result.pages_explored} | "
            f"Cache hits: {cache_stats['cache_hits']} | "
            f"Cache misses: {cache_stats['cache_misses']} | "
            f"Time: {elapsed_time:.2f}s"
        )

        return jsonify({
            'success': True,
            'path': result.path,
            'depth': result.depth,
            'pages_explored': result.pages_explored,
            'cache_hits': cache_stats['cache_hits'],
            'cache_misses': cache_stats['cache_misses'],
        }), 200

    except ArticleNotFoundError as e:
        elapsed_time = time.time() - start_time
        error_message = str(e)

        # Determine which article wasn't found
        if start.lower() in error_message.lower():
            error_response = f"Start article not found: '{start}'"
        elif end.lower() in error_message.lower():
            error_response = f"End article not found: '{end}'"
        else:
            error_response = f"Article not found: {error_message}"

        logger.warning(f"Article not found: {error_message} | Time: {elapsed_time:.2f}s")

        return jsonify({
            'success': False,
            'error': error_response
        }), 404

    except NoPathFoundError as e:
        elapsed_time = time.time() - start_time
        logger.warning(f"No path found: {e} | Time: {elapsed_time:.2f}s")

        return jsonify({
            'success': False,
            'error': f"No path found between '{start}' and '{end}' within the search depth limit"
        }), 404

    except RateLimitError as e:
        elapsed_time = time.time() - start_time
        logger.warning(f"Rate limited by Wikipedia: {e} | Time: {elapsed_time:.2f}s")

        return jsonify({
            'success': False,
            'error': "Wikipedia rate limit reached. Please wait a minute and try again."
        }), 429

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Unexpected error: {e} | Time: {elapsed_time:.2f}s", exc_info=True)

        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500


@app.route('/api/cache-stats', methods=['GET'])
def cache_stats():
    """
    Return statistics about the link cache.

    Response (200):
        {
            "success": true,
            "stats": {
                "total_articles": 1234,
                "total_links": 567890,
                "oldest_entry": "2024-01-15T10:30:00+00:00",
                "newest_entry": "2024-02-14T15:45:00+00:00",
                "cache_size_bytes": 5242880,
                "expired_count": 12
            }
        }
    """
    try:
        stats = get_cache_stats()
        return jsonify({
            'success': True,
            'stats': stats,
        }), 200
    except Exception as e:
        logger.error(f"Failed to retrieve cache stats: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve cache statistics',
        }), 500


@app.route('/api/cache-clear', methods=['POST'])
def cache_clear():
    """
    Clear cached link data.

    Optional request body (JSON):
        {"article": "Article_Title"}   — clear only that article
        (empty or no body)             — clear entire cache

    Response (200):
        {
            "success": true,
            "entries_cleared": 1234,
            "message": "Cache cleared successfully"
        }
    """
    try:
        article = None
        data = request.get_json(silent=True)
        if data and 'article' in data:
            article = data['article']
            if not isinstance(article, str) or not article.strip():
                return jsonify({
                    'success': False,
                    'error': "'article' must be a non-empty string",
                }), 400
            article = article.strip()

        entries_cleared = clear_cache(article)

        if article:
            msg = f"Cache cleared for article: '{article}'"
        else:
            msg = "Cache cleared successfully"

        logger.info(f"{msg} | Entries cleared: {entries_cleared}")

        return jsonify({
            'success': True,
            'entries_cleared': entries_cleared,
            'message': msg,
        }), 200

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to clear cache',
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
