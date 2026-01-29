"""
Wikipedia API Client Module

This module provides functions for interacting with the Wikipedia API:
- Article title normalization
- Article existence validation
- Retrieving outgoing links from articles (with SQLite cache)
- Handling redirects and pagination

All functions filter results to namespace 0 (main articles) only.
Link retrieval functions use a SQLite cache (see db.py) to avoid
redundant API calls.  Cache hits/misses are tracked via module-level
counters accessible through get_cache_hit_stats() and reset_cache_hit_stats().
"""

import requests
import time
from urllib.parse import quote, unquote

from db import init_db, cache_article_links, get_cached_links

# Wikipedia API configuration
API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "WikipediaChainFinder/1.0 (Educational Project)"

# Rate limiting configuration
API_RATE_LIMIT_DELAY = 0.2  # 200ms delay between API calls (max 5 requests/second)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

# Cache hit/miss tracking
_cache_hits = 0
_cache_misses = 0

# Initialise the cache database on import
init_db()


class ArticleNotFoundError(Exception):
    """Raised when a Wikipedia article cannot be found."""
    pass


class RateLimitError(Exception):
    """Raised when Wikipedia rate limits our requests."""
    pass


def get_cache_hit_stats() -> dict:
    """Return the current cache hit/miss counters.

    Returns:
        Dictionary with keys ``cache_hits`` and ``cache_misses``.
    """
    return {"cache_hits": _cache_hits, "cache_misses": _cache_misses}


def reset_cache_hit_stats() -> None:
    """Reset the cache hit/miss counters to zero."""
    global _cache_hits, _cache_misses
    _cache_hits = 0
    _cache_misses = 0


def _make_request(params: dict, retries: int = MAX_RETRIES) -> dict:
    """
    Make a request to the Wikipedia API with retry logic.

    Args:
        params: API parameters
        retries: Number of retries remaining

    Returns:
        JSON response from the API

    Raises:
        requests.RequestException: If all retries fail
        RateLimitError: If rate limited by Wikipedia
    """
    params["format"] = "json"
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(retries):
        try:
            response = requests.get(API_URL, params=params, headers=headers, timeout=30)

            # Handle rate limiting specifically
            if response.status_code == 429:
                if attempt < retries - 1:
                    # Wait longer for rate limit errors
                    wait_time = RETRY_DELAY * (attempt + 1) * 2
                    time.sleep(wait_time)
                    continue
                else:
                    raise RateLimitError(
                        "Wikipedia rate limit reached. Please wait a moment and try again."
                    )

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise e


def normalize_title(title: str) -> str:
    """
    Normalize a Wikipedia article title.

    - Replaces spaces with underscores
    - Handles first-character case insensitivity (capitalizes first char)
    - Trims whitespace

    Args:
        title: The article title to normalize

    Returns:
        The normalized article title
    """
    if not title:
        return ""

    # Trim whitespace
    title = title.strip()

    if not title:
        return ""

    # Replace spaces with underscores
    title = title.replace(" ", "_")

    # Capitalize first character (Wikipedia convention)
    title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()

    return title


def validate_article(title: str) -> str:
    """
    Validate that a Wikipedia article exists.

    Checks if the article exists and follows redirects transparently.

    Args:
        title: The article title to validate

    Returns:
        The canonical (normalized) article title

    Raises:
        ArticleNotFoundError: If the article does not exist
    """
    if not title or not title.strip():
        raise ArticleNotFoundError("Empty article title")

    normalized = normalize_title(title)

    params = {
        "action": "query",
        "titles": normalized,
        "redirects": 1,  # Follow redirects
    }

    print(f"Fetching {normalized} from Wikipedia API...")
    data = _make_request(params)

    # Polite rate limiting: delay after API call
    time.sleep(API_RATE_LIMIT_DELAY)

    pages = data.get("query", {}).get("pages", {})

    # Check for missing page (indicated by negative page ID or "missing" key)
    for page_id, page_info in pages.items():
        if "missing" in page_info:
            raise ArticleNotFoundError(f"Article not found: {title}")

        # Return the canonical title (may differ due to redirects or normalization)
        return page_info.get("title", normalized)

    raise ArticleNotFoundError(f"Article not found: {title}")


def get_article_links(title: str) -> list[str]:
    """
    Get all outgoing links from a Wikipedia article.

    Checks the SQLite cache first.  On a cache hit the stored links are
    returned immediately without any API call.  On a miss the links are
    fetched from the Wikipedia API, stored in the cache, and returned.

    Args:
        title: The article title to get links from

    Returns:
        A list of normalized article titles that the article links to
    """
    global _cache_hits, _cache_misses

    normalized = normalize_title(title)

    # --- cache lookup ---
    cached = get_cached_links(normalized)
    if cached is not None:
        _cache_hits += 1
        print(f"Using cached data for {normalized}")
        return cached

    _cache_misses += 1

    # --- API fetch ---
    print(f"Fetching {normalized} from Wikipedia API...")
    links = _fetch_article_links(normalized)

    # Polite rate limiting: delay after API call
    time.sleep(API_RATE_LIMIT_DELAY)

    # Store result in cache (even an empty list is valid to cache)
    cache_article_links(normalized, links)

    return links


def _fetch_article_links(normalized_title: str) -> list[str]:
    """Fetch outgoing links for *normalized_title* from the Wikipedia API.

    This is the uncached, raw API call extracted so the public function
    can layer caching on top.
    """
    links = []

    params = {
        "action": "query",
        "titles": normalized_title,
        "prop": "links",
        "pllimit": "max",  # Get maximum links per request (500 for anonymous users)
        "plnamespace": 0,  # Only namespace 0 (main articles)
    }

    while True:
        data = _make_request(params)

        pages = data.get("query", {}).get("pages", {})

        for page_id, page_info in pages.items():
            if "missing" in page_info:
                return []

            page_links = page_info.get("links", [])
            for link in page_links:
                link_title = link.get("title", "")
                if link_title:
                    # Filter out any non-main namespace articles that might slip through
                    if ":" not in link_title or link_title.startswith("Wikipedia:"):
                        # Additional filter: exclude Wikipedia: namespace
                        if not link_title.startswith(("Wikipedia:", "Category:", "File:",
                                                       "Template:", "Help:", "Portal:",
                                                       "Talk:", "User:", "Special:",
                                                       "MediaWiki:", "Module:", "Draft:")):
                            links.append(link_title)

        # Check for continuation
        if "continue" in data:
            params["plcontinue"] = data["continue"]["plcontinue"]
        else:
            break

    return links


def get_backlinks(title: str, limit: int = 500) -> list[str]:
    """
    Get articles that link TO the specified article (backlinks).

    Uses the SQLite cache with the key prefix ``backlinks::`` to
    distinguish from forward-link cache entries.

    Args:
        title: The article title to get backlinks for
        limit: Maximum number of backlinks to retrieve (default 500)

    Returns:
        A list of article titles that link to this article
    """
    global _cache_hits, _cache_misses

    normalized = normalize_title(title)
    cache_key = f"backlinks::{normalized}"

    # --- cache lookup ---
    cached = get_cached_links(cache_key)
    if cached is not None:
        _cache_hits += 1
        print(f"Using cached data for {cache_key}")
        return cached[:limit]

    _cache_misses += 1

    # --- API fetch ---
    print(f"Fetching {cache_key} from Wikipedia API...")
    backlinks = _fetch_backlinks(normalized, limit)

    # Polite rate limiting: delay after API call
    time.sleep(API_RATE_LIMIT_DELAY)

    cache_article_links(cache_key, backlinks)

    return backlinks


def _fetch_backlinks(normalized_title: str, limit: int) -> list[str]:
    """Fetch backlinks for *normalized_title* from the Wikipedia API."""
    backlinks = []

    params = {
        "action": "query",
        "list": "backlinks",
        "bltitle": normalized_title,
        "bllimit": "max",  # Get maximum per request
        "blnamespace": 0,  # Only namespace 0 (main articles)
    }

    while len(backlinks) < limit:
        data = _make_request(params)

        bl_list = data.get("query", {}).get("backlinks", [])

        for bl in bl_list:
            bl_title = bl.get("title", "")
            if bl_title:
                backlinks.append(bl_title)
                if len(backlinks) >= limit:
                    break

        # Check for continuation
        if "continue" in data and len(backlinks) < limit:
            params["blcontinue"] = data["continue"]["blcontinue"]
        else:
            break

    return backlinks
