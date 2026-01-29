"""
Unit tests for the Bidirectional Search Module

Tests the search algorithm with mocked Wikipedia client to verify:
- Trivial case (start == end)
- Direct link (depth 1)
- Two-step path (depth 2)
- Path reconstruction
- Maximum depth limit
- No path found handling
"""

import unittest
from unittest.mock import patch, MagicMock
from search import (
    find_path,
    expand_frontier_forward,
    expand_frontier_backward,
    find_intersection,
    reconstruct_path,
    SearchResult,
    NoPathFoundError,
)
from wikipedia_client import ArticleNotFoundError


class TestFindPathTrivialCases(unittest.TestCase):
    """Tests for trivial search cases."""

    @patch("search.validate_article")
    @patch("search.get_article_links")
    @patch("search.get_backlinks")
    def test_same_start_and_end_returns_single_element(self, mock_backlinks, mock_links, mock_validate):
        """find_path("A", "A") returns ["A"] immediately."""
        mock_validate.return_value = "A"

        result = find_path("A", "A")

        self.assertEqual(result.path, ["A"])
        self.assertEqual(result.depth, 0)
        self.assertEqual(result.pages_explored, 1)
        # get_article_links should not be called for same start/end
        mock_links.assert_not_called()
        mock_backlinks.assert_not_called()

    @patch("search.validate_article")
    def test_nonexistent_start_article_raises_error(self, mock_validate):
        """Nonexistent start article raises ArticleNotFoundError."""
        mock_validate.side_effect = ArticleNotFoundError("Article not found: NonExistent")

        with self.assertRaises(ArticleNotFoundError):
            find_path("NonExistent", "B")

    @patch("search.validate_article")
    def test_nonexistent_end_article_raises_error(self, mock_validate):
        """Nonexistent end article raises ArticleNotFoundError."""
        def validate_side_effect(title):
            if title == "A":
                return "A"
            raise ArticleNotFoundError("Article not found: NonExistent")

        mock_validate.side_effect = validate_side_effect

        with self.assertRaises(ArticleNotFoundError):
            find_path("A", "NonExistent")


class TestFindPathDirectLink(unittest.TestCase):
    """Tests for direct link (depth 1) searches."""

    @patch("search.validate_article")
    @patch("search.get_article_links")
    @patch("search.get_backlinks")
    def test_direct_link_forward(self, mock_backlinks, mock_links, mock_validate):
        """A -> B: search from A to B returns ["A", "B"]."""
        mock_validate.side_effect = lambda x: x

        def links_side_effect(page):
            if page == "A":
                return ["B", "C", "D"]
            elif page == "B":
                return ["E", "F"]
            return []

        def backlinks_side_effect(page):
            if page == "B":
                return ["A", "X", "Y"]
            return []

        mock_links.side_effect = links_side_effect
        mock_backlinks.side_effect = backlinks_side_effect

        result = find_path("A", "B")

        self.assertEqual(result.path, ["A", "B"])
        self.assertEqual(result.depth, 1)

    @patch("search.validate_article")
    @patch("search.get_article_links")
    @patch("search.get_backlinks")
    def test_direct_link_via_backlinks(self, mock_backlinks, mock_links, mock_validate):
        """A -> B where B has A in its backlinks."""
        mock_validate.side_effect = lambda x: x

        def links_side_effect(page):
            if page == "A":
                return ["B"]
            return []

        def backlinks_side_effect(page):
            if page == "B":
                return ["A"]
            return []

        mock_links.side_effect = links_side_effect
        mock_backlinks.side_effect = backlinks_side_effect

        result = find_path("A", "B")

        self.assertEqual(result.path, ["A", "B"])
        self.assertEqual(result.depth, 1)


class TestFindPathMultiStep(unittest.TestCase):
    """Tests for multi-step path searches."""

    @patch("search.validate_article")
    @patch("search.get_article_links")
    @patch("search.get_backlinks")
    def test_two_step_path(self, mock_backlinks, mock_links, mock_validate):
        """A -> B -> C: search from A to C returns ["A", "B", "C"]."""
        mock_validate.side_effect = lambda x: x

        def links_side_effect(page):
            if page == "A":
                return ["B"]
            elif page == "B":
                return ["C"]
            elif page == "C":
                return ["D"]
            return []

        def backlinks_side_effect(page):
            if page == "C":
                return ["B"]
            elif page == "B":
                return ["A"]
            return []

        mock_links.side_effect = links_side_effect
        mock_backlinks.side_effect = backlinks_side_effect

        result = find_path("A", "C")

        self.assertEqual(result.path, ["A", "B", "C"])
        self.assertEqual(result.depth, 2)

    @patch("search.validate_article")
    @patch("search.get_article_links")
    @patch("search.get_backlinks")
    def test_three_step_path(self, mock_backlinks, mock_links, mock_validate):
        """A -> B -> C -> D: search from A to D."""
        mock_validate.side_effect = lambda x: x

        def links_side_effect(page):
            if page == "A":
                return ["B"]
            elif page == "B":
                return ["C"]
            elif page == "C":
                return ["D"]
            elif page == "D":
                return ["E"]
            return []

        def backlinks_side_effect(page):
            if page == "D":
                return ["C"]
            elif page == "C":
                return ["B"]
            elif page == "B":
                return ["A"]
            return []

        mock_links.side_effect = links_side_effect
        mock_backlinks.side_effect = backlinks_side_effect

        result = find_path("A", "D")

        # Path could be found via forward or backward search
        self.assertIn("A", result.path)
        self.assertIn("D", result.path)
        self.assertEqual(result.path[0], "A")
        self.assertEqual(result.path[-1], "D")


class TestFindPathNoPath(unittest.TestCase):
    """Tests for cases where no path exists."""

    @patch("search.validate_article")
    @patch("search.get_article_links")
    @patch("search.get_backlinks")
    def test_no_path_within_limit(self, mock_backlinks, mock_links, mock_validate):
        """No path within depth limit raises NoPathFoundError."""
        mock_validate.side_effect = lambda x: x

        # Create disconnected graph
        def links_side_effect(page):
            if page == "A":
                return ["B"]
            elif page == "B":
                return ["A"]  # Cycle back
            return []

        def backlinks_side_effect(page):
            if page == "Z":
                return ["Y"]
            elif page == "Y":
                return ["Z"]
            return []

        mock_links.side_effect = links_side_effect
        mock_backlinks.side_effect = backlinks_side_effect

        with self.assertRaises(NoPathFoundError):
            find_path("A", "Z", max_depth=2)

    @patch("search.validate_article")
    @patch("search.get_article_links")
    @patch("search.get_backlinks")
    def test_empty_links(self, mock_backlinks, mock_links, mock_validate):
        """Articles with no links raise NoPathFoundError."""
        mock_validate.side_effect = lambda x: x
        mock_links.return_value = []
        mock_backlinks.return_value = []

        with self.assertRaises(NoPathFoundError):
            find_path("A", "B", max_depth=2)


class TestPathReconstruction(unittest.TestCase):
    """Tests for path reconstruction logic."""

    def test_reconstruct_simple_path(self):
        """Test reconstruction with simple forward and backward paths."""
        forward_visited = {"A": None, "B": "A", "C": "B"}
        backward_visited = {"E": None, "D": "E", "C": "D"}

        path = reconstruct_path("C", forward_visited, backward_visited)

        self.assertEqual(path, ["A", "B", "C", "D", "E"])

    def test_reconstruct_path_meeting_at_start(self):
        """Test reconstruction when meeting point is near start."""
        forward_visited = {"A": None, "B": "A"}
        backward_visited = {"C": None, "B": "C"}

        path = reconstruct_path("B", forward_visited, backward_visited)

        self.assertEqual(path, ["A", "B", "C"])

    def test_reconstruct_single_step(self):
        """Test reconstruction for single step path."""
        forward_visited = {"A": None, "B": "A"}
        backward_visited = {"B": None}

        path = reconstruct_path("B", forward_visited, backward_visited)

        self.assertEqual(path, ["A", "B"])


class TestFindIntersection(unittest.TestCase):
    """Tests for intersection detection."""

    def test_finds_intersection(self):
        """Test that intersection is found when sets overlap."""
        forward_visited = {"A": None, "B": "A", "C": "B"}
        backward_visited = {"E": None, "D": "E", "C": "D"}

        result = find_intersection(forward_visited, backward_visited)

        self.assertEqual(result, "C")

    def test_no_intersection(self):
        """Test that None is returned when no intersection."""
        forward_visited = {"A": None, "B": "A"}
        backward_visited = {"E": None, "D": "E"}

        result = find_intersection(forward_visited, backward_visited)

        self.assertIsNone(result)


class TestExpandFrontierForward(unittest.TestCase):
    """Tests for forward frontier expansion."""

    @patch("search.get_article_links")
    def test_expands_frontier(self, mock_links):
        """Test frontier expansion adds new pages."""
        mock_links.return_value = ["B", "C", "D"]

        frontier = {"A"}
        visited = {"A": None}

        new_frontier, count = expand_frontier_forward(frontier, visited)

        self.assertEqual(new_frontier, {"B", "C", "D"})
        self.assertEqual(count, 3)
        self.assertIn("B", visited)
        self.assertIn("C", visited)
        self.assertIn("D", visited)

    @patch("search.get_article_links")
    def test_skips_already_visited(self, mock_links):
        """Test that already visited pages are skipped."""
        mock_links.return_value = ["B", "C"]

        frontier = {"A"}
        visited = {"A": None, "B": "X"}  # B already visited

        new_frontier, count = expand_frontier_forward(frontier, visited)

        self.assertEqual(new_frontier, {"C"})
        self.assertEqual(count, 1)


class TestExpandFrontierBackward(unittest.TestCase):
    """Tests for backward frontier expansion using backlinks."""

    @patch("search.get_backlinks")
    def test_expands_frontier_with_backlinks(self, mock_backlinks):
        """Test backward frontier expansion uses backlinks."""
        mock_backlinks.return_value = ["X", "Y", "Z"]

        frontier = {"A"}
        visited = {"A": None}

        new_frontier, count = expand_frontier_backward(frontier, visited)

        self.assertEqual(new_frontier, {"X", "Y", "Z"})
        self.assertEqual(count, 3)
        # Each backlink should point to A (the page they link to)
        self.assertEqual(visited["X"], "A")
        self.assertEqual(visited["Y"], "A")
        self.assertEqual(visited["Z"], "A")

    @patch("search.get_backlinks")
    def test_skips_already_visited(self, mock_backlinks):
        """Test that already visited pages are skipped."""
        mock_backlinks.return_value = ["X", "Y"]

        frontier = {"A"}
        visited = {"A": None, "X": "B"}  # X already visited

        new_frontier, count = expand_frontier_backward(frontier, visited)

        self.assertEqual(new_frontier, {"Y"})
        self.assertEqual(count, 1)


class TestPagesExploredCount(unittest.TestCase):
    """Tests for accurate pages_explored counting."""

    @patch("search.validate_article")
    @patch("search.get_article_links")
    @patch("search.get_backlinks")
    def test_pages_explored_accurate(self, mock_backlinks, mock_links, mock_validate):
        """Test that pages_explored count is accurate."""
        mock_validate.side_effect = lambda x: x

        def links_side_effect(page):
            if page == "A":
                return ["B", "C"]
            elif page == "B":
                return ["D"]
            elif page == "C":
                return ["D"]
            return []

        def backlinks_side_effect(page):
            if page == "D":
                return ["B", "C"]
            elif page == "B":
                return ["A"]
            elif page == "C":
                return ["A"]
            return []

        mock_links.side_effect = links_side_effect
        mock_backlinks.side_effect = backlinks_side_effect

        result = find_path("A", "D")

        # A and D are initial (2), then pages are explored
        self.assertGreaterEqual(result.pages_explored, 2)
        self.assertIn("D", result.path)


if __name__ == "__main__":
    unittest.main()
