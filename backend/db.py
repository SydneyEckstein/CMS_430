"""
Database Module - SQLite Cache for Wikipedia Article Links

This module provides a SQLite-backed caching layer for storing Wikipedia
article links. Cached links avoid redundant API calls, dramatically
speeding up repeated searches.

Functions:
    init_db        - Create the database and tables
    cache_article_links - Store an article's outgoing links
    get_cached_links    - Retrieve cached links (respects 30-day expiry)
    clear_cache         - Remove specific or all cached entries
    get_cache_stats     - Return cache statistics
    cleanup_expired     - Remove all expired entries
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

# Cache configuration
CACHE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.db")
CACHE_EXPIRATION_DAYS = 30
TABLE_ARTICLE_LINKS = "article_links"


def _get_connection() -> sqlite3.Connection:
    """Open a connection to the cache database with row-factory enabled."""
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create the cache database and tables if they do not already exist.

    Creates the article_links table with columns:
        article_title (TEXT PRIMARY KEY)
        links         (TEXT, JSON-serialized list)
        cached_at     (TEXT, ISO-8601 timestamp in UTC)
    """
    conn = _get_connection()
    try:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_ARTICLE_LINKS} (
                article_title TEXT PRIMARY KEY,
                links         TEXT NOT NULL,
                cached_at     TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def cache_article_links(article_title: str, links: list[str]) -> None:
    """
    Store an article's outgoing links in the cache.

    If an entry already exists for the article, it is replaced.

    Args:
        article_title: Normalized Wikipedia article title.
        links: List of outgoing link titles.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {TABLE_ARTICLE_LINKS}
                (article_title, links, cached_at)
            VALUES (?, ?, ?)
            """,
            (article_title, json.dumps(links), now),
        )
        conn.commit()
    finally:
        conn.close()


def get_cached_links(article_title: str) -> list[str] | None:
    """
    Retrieve cached links for an article.

    Returns None if the article is not cached or the entry has expired
    (older than CACHE_EXPIRATION_DAYS). Expired entries are deleted on
    access.

    Args:
        article_title: Normalized Wikipedia article title.

    Returns:
        List of link titles, or None on miss / expiry.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            f"SELECT links, cached_at FROM {TABLE_ARTICLE_LINKS} WHERE article_title = ?",
            (article_title,),
        ).fetchone()

        if row is None:
            return None

        cached_at = datetime.fromisoformat(row["cached_at"])
        # Ensure timezone-aware comparison
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)

        expiry = datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS)

        if cached_at < expiry:
            # Entry expired — delete it
            conn.execute(
                f"DELETE FROM {TABLE_ARTICLE_LINKS} WHERE article_title = ?",
                (article_title,),
            )
            conn.commit()
            return None

        return json.loads(row["links"])
    finally:
        conn.close()


def clear_cache(article_title: str | None = None) -> int:
    """
    Clear cached entries.

    Args:
        article_title: If provided, clear only this article's cache.
                       If None, clear the entire cache.

    Returns:
        Number of entries deleted.
    """
    conn = _get_connection()
    try:
        if article_title is not None:
            cursor = conn.execute(
                f"DELETE FROM {TABLE_ARTICLE_LINKS} WHERE article_title = ?",
                (article_title,),
            )
        else:
            cursor = conn.execute(f"DELETE FROM {TABLE_ARTICLE_LINKS}")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def get_cache_stats() -> dict:
    """
    Return statistics about the current cache state.

    Returns:
        Dictionary with keys:
            total_articles   - Number of cached articles
            total_links      - Total link count across all articles
            oldest_entry     - ISO timestamp of oldest entry (or None)
            newest_entry     - ISO timestamp of newest entry (or None)
            cache_size_bytes - Size of the database file on disk
            expired_count    - Number of entries older than 30 days
    """
    conn = _get_connection()
    try:
        total_articles = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE_ARTICLE_LINKS}"
        ).fetchone()[0]

        # Total links requires reading the JSON arrays
        rows = conn.execute(
            f"SELECT links FROM {TABLE_ARTICLE_LINKS}"
        ).fetchall()
        total_links = sum(len(json.loads(r["links"])) for r in rows)

        oldest = conn.execute(
            f"SELECT MIN(cached_at) FROM {TABLE_ARTICLE_LINKS}"
        ).fetchone()[0]

        newest = conn.execute(
            f"SELECT MAX(cached_at) FROM {TABLE_ARTICLE_LINKS}"
        ).fetchone()[0]

        expiry = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS)).isoformat()
        expired_count = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE_ARTICLE_LINKS} WHERE cached_at < ?",
            (expiry,),
        ).fetchone()[0]

        cache_size_bytes = os.path.getsize(CACHE_DB_PATH) if os.path.exists(CACHE_DB_PATH) else 0

        return {
            "total_articles": total_articles,
            "total_links": total_links,
            "oldest_entry": oldest,
            "newest_entry": newest,
            "cache_size_bytes": cache_size_bytes,
            "expired_count": expired_count,
        }
    finally:
        conn.close()


def cleanup_expired() -> int:
    """
    Delete all cache entries older than CACHE_EXPIRATION_DAYS.

    Returns:
        Number of entries deleted.
    """
    expiry = (datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRATION_DAYS)).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.execute(
            f"DELETE FROM {TABLE_ARTICLE_LINKS} WHERE cached_at < ?",
            (expiry,),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
