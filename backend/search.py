"""
Bidirectional Iterative Deepening Search Module

This module implements the search algorithm for finding the shortest path
between two Wikipedia articles using bidirectional search.

The algorithm:
1. Validates both start and end articles exist
2. Initializes forward search from start and backward search from end
3. Alternates between expanding forward and backward frontiers
4. Checks for intersection after each expansion
5. Reconstructs the path when frontiers meet
"""

from dataclasses import dataclass
from wikipedia_client import validate_article, get_article_links, get_backlinks, ArticleNotFoundError


@dataclass
class SearchResult:
    """Result of a path search between two articles."""
    path: list[str]
    depth: int
    pages_explored: int


class NoPathFoundError(Exception):
    """Raised when no path can be found within the depth limit."""
    pass


def find_path(start: str, end: str, max_depth: int = 3) -> SearchResult:
    """
    Find the shortest path between two Wikipedia articles.

    Uses bidirectional search to find a path from the start article
    to the end article.

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
    # Validate both articles exist and get canonical titles
    start_canonical = validate_article(start)
    end_canonical = validate_article(end)

    # Handle edge case: start == end
    if start_canonical == end_canonical:
        return SearchResult(path=[start_canonical], depth=0, pages_explored=1)

    # Initialize data structures
    # forward_visited: maps page -> parent (page we came from)
    # backward_visited: maps page -> child (page we go to)
    forward_visited = {start_canonical: None}
    backward_visited = {end_canonical: None}

    # Current frontiers (pages to expand next)
    forward_frontier = {start_canonical}
    backward_frontier = {end_canonical}

    pages_explored = 2  # Start and end pages

    # Search up to max_depth in each direction
    for depth in range(1, max_depth + 1):
        # Expand forward frontier (using outgoing links)
        forward_frontier, new_explored = expand_frontier_forward(
            forward_frontier, forward_visited
        )
        pages_explored += new_explored

        # Check for intersection after forward expansion
        intersection = find_intersection(forward_visited, backward_visited)
        if intersection:
            path = reconstruct_path(intersection, forward_visited, backward_visited)
            return SearchResult(path=path, depth=len(path) - 1, pages_explored=pages_explored)

        # Expand backward frontier (using backlinks - pages that link TO the target)
        backward_frontier, new_explored = expand_frontier_backward(
            backward_frontier, backward_visited
        )
        pages_explored += new_explored

        # Check for intersection after backward expansion
        intersection = find_intersection(forward_visited, backward_visited)
        if intersection:
            path = reconstruct_path(intersection, forward_visited, backward_visited)
            return SearchResult(path=path, depth=len(path) - 1, pages_explored=pages_explored)

        # If both frontiers are empty, no path exists
        if not forward_frontier and not backward_frontier:
            break

    raise NoPathFoundError(
        f"No path found between '{start_canonical}' and '{end_canonical}' "
        f"within depth limit of {max_depth}"
    )


def expand_frontier_forward(
    frontier: set[str],
    visited: dict[str, str | None]
) -> tuple[set[str], int]:
    """
    Expand the forward frontier by one level using outgoing links.

    For each page in the frontier, fetch pages it links TO and add unvisited
    pages to the new frontier.

    Args:
        frontier: Current set of pages to expand
        visited: Dictionary tracking visited pages and their parents

    Returns:
        Tuple of (new frontier set, number of new pages explored)
    """
    new_frontier = set()
    new_explored = 0

    for page in frontier:
        links = get_article_links(page)

        for link in links:
            if link not in visited:
                visited[link] = page  # Record parent (page we came from)
                new_frontier.add(link)
                new_explored += 1

    return new_frontier, new_explored


def expand_frontier_backward(
    frontier: set[str],
    visited: dict[str, str | None]
) -> tuple[set[str], int]:
    """
    Expand the backward frontier by one level using backlinks.

    For each page in the frontier, fetch pages that link TO it and add unvisited
    pages to the new frontier. This finds pages that can reach the target.

    Args:
        frontier: Current set of pages to expand
        visited: Dictionary tracking visited pages and their next step toward end

    Returns:
        Tuple of (new frontier set, number of new pages explored)
    """
    new_frontier = set()
    new_explored = 0

    for page in frontier:
        # Get pages that link TO this page (backlinks)
        backlinks = get_backlinks(page)

        for backlink in backlinks:
            if backlink not in visited:
                visited[backlink] = page  # Record next step toward end
                new_frontier.add(backlink)
                new_explored += 1

    return new_frontier, new_explored


def find_intersection(
    forward_visited: dict[str, str | None],
    backward_visited: dict[str, str | None]
) -> str | None:
    """
    Find a meeting point between forward and backward searches.

    Args:
        forward_visited: Pages visited from start
        backward_visited: Pages visited from end

    Returns:
        A page title that exists in both visited sets, or None if no intersection
    """
    # Find intersection of the two visited sets
    intersection = set(forward_visited.keys()) & set(backward_visited.keys())

    if intersection:
        # Return any meeting point (they should all give valid paths)
        return next(iter(intersection))

    return None


def reconstruct_path(
    meeting_point: str,
    forward_visited: dict[str, str | None],
    backward_visited: dict[str, str | None]
) -> list[str]:
    """
    Reconstruct the full path from start to end through the meeting point.

    Args:
        meeting_point: The page where forward and backward searches met
        forward_visited: Maps each page to its parent in forward direction
        backward_visited: Maps each page to its parent in backward direction

    Returns:
        Complete path from start to end as a list of page titles
    """
    # Build path from start to meeting point (trace back through forward_visited)
    forward_path = []
    current = meeting_point
    while current is not None:
        forward_path.append(current)
        current = forward_visited.get(current)
    forward_path.reverse()  # Now goes from start to meeting point

    # Build path from meeting point to end (trace back through backward_visited)
    backward_path = []
    current = backward_visited.get(meeting_point)  # Start from next page after meeting point
    while current is not None:
        backward_path.append(current)
        current = backward_visited.get(current)

    # Combine paths (forward_path already includes meeting point)
    return forward_path + backward_path
