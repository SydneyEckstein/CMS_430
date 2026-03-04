"""
Ultimate Tic-Tac-Toe game logic.

Board representation:
  - cells: list of 81 values (0=empty, 1=X, 2=O), indexed [small_board * 9 + cell]
  - small_board_winners: list of 9 values (0=active, 1=X won, 2=O won, 3=draw)
  - active_board: index 0-8 of the required small board, or None for free choice
  - current_player: 1 (X) or 2 (O)
"""

EMPTY = 0
X = 1
O = 2
DRAW = 3

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6),              # diagonals
]


def check_winner(cells):
    """Return winner (X or O) if any win line is complete, else None."""
    for a, b, c in WIN_LINES:
        if cells[a] != EMPTY and cells[a] == cells[b] == cells[c]:
            return cells[a]
    return None


def is_full(cells):
    return all(c != EMPTY for c in cells)


class GameState:
    def __init__(self):
        self.cells = [EMPTY] * 81
        self.small_board_winners = [EMPTY] * 9  # EMPTY=active, X=X won, O=O won, DRAW=draw
        self.active_board = None  # None means free choice
        self.current_player = X

    def copy(self):
        s = GameState.__new__(GameState)
        s.cells = self.cells[:]
        s.small_board_winners = self.small_board_winners[:]
        s.active_board = self.active_board
        s.current_player = self.current_player
        return s

    def _small_board_cells(self, board_idx):
        start = board_idx * 9
        return self.cells[start:start + 9]

    def _update_small_board(self, board_idx):
        """Recompute winner for a small board after a move."""
        cells = self._small_board_cells(board_idx)
        winner = check_winner(cells)
        if winner:
            self.small_board_winners[board_idx] = winner
        elif is_full(cells):
            self.small_board_winners[board_idx] = DRAW

    def get_legal_moves(self):
        """Return list of (board_idx, cell_idx) tuples for all legal moves."""
        if self.active_board is not None:
            boards = [self.active_board]
        else:
            boards = [i for i in range(9) if self.small_board_winners[i] == EMPTY]

        moves = []
        for b in boards:
            start = b * 9
            for c in range(9):
                if self.cells[start + c] == EMPTY:
                    moves.append((b, c))
        return moves

    def apply_move(self, board_idx, cell_idx):
        """Return a new GameState after applying the move."""
        s = self.copy()
        s.cells[board_idx * 9 + cell_idx] = s.current_player
        s._update_small_board(board_idx)

        # The next active board is determined by the cell chosen
        if s.small_board_winners[cell_idx] == EMPTY:
            s.active_board = cell_idx
        else:
            s.active_board = None  # free choice

        s.current_player = O if s.current_player == X else X
        return s

    def get_large_board_winner(self):
        """Check if someone has won the large board."""
        return check_winner(self.small_board_winners)

    def is_terminal(self):
        if self.get_large_board_winner():
            return True
        if not self.get_legal_moves():
            return True
        return False

    def get_winner(self):
        """Return X, O, DRAW, or None if game is not over."""
        winner = self.get_large_board_winner()
        if winner:
            return winner
        if not self.get_legal_moves():
            return DRAW
        return None


def display(state):
    """Print a text representation of the board."""
    symbols = {EMPTY: ".", X: "X", O: "O"}

    def small_row(board_idx, row):
        start = board_idx * 9 + row * 3
        return " ".join(symbols[state.cells[start + i]] for i in range(3))

    lines = []
    for big_row in range(3):
        for small_row_idx in range(3):
            row_parts = []
            for big_col in range(3):
                board_idx = big_row * 3 + big_col
                row_parts.append(small_row(board_idx, small_row_idx))
            lines.append(" | ".join(row_parts))
        if big_row < 2:
            lines.append("------+-------+------")

    print("\n".join(lines))
    winner_syms = [symbols.get(w, "?") for w in state.small_board_winners]
    print(f"\nSmall board winners: {winner_syms}")
    ab = state.active_board if state.active_board is not None else "free"
    print(f"Active board: {ab}  |  Current player: {symbols[state.current_player]}")


if __name__ == "__main__":
    # Quick smoke test
    state = GameState()
    moves = state.get_legal_moves()
    print(f"Initial legal moves: {len(moves)} (expected 81)")
    display(state)

    # Apply a few moves
    state = state.apply_move(4, 0)  # X plays center board, top-left cell
    state = state.apply_move(0, 4)  # O must play board 0, plays center
    print("\nAfter 2 moves:")
    display(state)
