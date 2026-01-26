"""
Wikipedia API Client Module

This module provides functions for interacting with the Wikipedia API:
- Article title normalization
- Article existence validation
- Retrieving outgoing links from articles
- Handling redirects and pagination

All functions filter results to namespace 0 (main articles) only.
"""


def normalize_title(title: str) -> str:
    """
    Normalize a Wikipedia article title.

    - Replaces spaces with underscores
    - Handles first-character case insensitivity
    - URL encodes special characters as needed

    Args:
        title: The article title to normalize

    Returns:
        The normalized article title
    """
    pass


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
    pass


def get_article_links(title: str) -> list[str]:
    """
    Get all outgoing links from a Wikipedia article.

    Retrieves links from the article content, filtering to namespace 0 only.
    Handles pagination for articles with many links.

    Args:
        title: The article title to get links from

    Returns:
        A list of normalized article titles that the article links to
    """
    pass


class ArticleNotFoundError(Exception):
    """Raised when a Wikipedia article cannot be found."""
    pass
