"""
Bidirectional Iterative Deepening Search Module

This module implements the search algorithm for finding the shortest path
between two Wikipedia articles using bidirectional iterative deepening search.

The algorithm:
1. Initializes forward search from start and backward search from end
2. Alternates between expanding forward and backward frontiers
3. Increases depth limit with each iteration (0, 1, 2, 3)
4. Checks for intersection after each expansion
5. Reconstructs the path when frontiers meet
"""

from dataclasses import dataclass


@dataclass
class SearchResult:
    """Result of a path search between two articles."""
    path: list[str]
    depth: int
    pages_explored: int


def find_path(start: str, end: str, max_depth: int = 3) -> SearchResult:
    """
    Find the shortest path between two Wikipedia articles.

    Uses bidirectional iterative deepening search to find a path
    from the start article to the end article.

    Args:
        start: The starting article title
        end: The ending article title
        max_depth: Maximum depth per direction (default 3, max chain length 7)

    Returns:
        SearchResult containing the path, depth, and pages explored

    Raises:
        ArticleNotFoundError: If start or end article doesn't exist
        NoPathFoundError: If no path exists within the depth limit
    """
    pass


class NoPathFoundError(Exception):
    """Raised when no path can be found within the depth limit."""
    pass
