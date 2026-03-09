"""
Monte Carlo Tree Search (MCTS) AI for Ultimate Tic-Tac-Toe.

Uses UCB1 for tree descent and heuristic rollouts that prefer moves
which immediately win a small board.
"""

import math
import random

from game import GameState, X, O, DRAW, check_winner


class MCTSNode:
    def __init__(self, state, parent=None, move=None):
        self.state = state          # GameState
        self.parent = parent        # MCTSNode or None
        self.move = move            # (board_idx, cell_idx) that led here
        self.children = []
        self.visits = 0
        self.total_score = 0.0

        # Moves not yet expanded
        self._untried_moves = state.get_legal_moves()

    def is_fully_expanded(self):
        return len(self._untried_moves) == 0

    def is_terminal(self):
        return self.state.is_terminal()

    def ucb1(self, c=math.sqrt(2)):
        if self.visits == 0:
            return float("inf")
        exploitation = self.total_score / self.visits
        exploration = c * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

    def best_child(self, c=math.sqrt(2)):
        return max(self.children, key=lambda n: n.ucb1(c))

    def expand(self):
        """Add one child for a random untried move and return it."""
        move = self._untried_moves.pop(random.randrange(len(self._untried_moves)))
        child_state = self.state.apply_move(*move)
        child = MCTSNode(child_state, parent=self, move=move)
        self.children.append(child)
        return child

    def backpropagate(self, score):
        self.visits += 1
        self.total_score += score
        if self.parent:
            self.parent.backpropagate(-score)


def _wins_small_board(state, move):
    """Return True if playing move immediately wins the small board."""
    board_idx, cell_idx = move
    cells = state._small_board_cells(board_idx)[:]
    cells[cell_idx] = state.current_player
    return check_winner(cells) is not None


def rollout(state):
    """Play a heuristic game from state and return +1 (win), -1 (loss), or 0 (draw)
    from the perspective of the player whose turn it was at the *root* call site.

    Rollout policy: prefer moves that immediately win a small board; fall back
    to uniform random otherwise.
    """
    starting_player = state.current_player
    while not state.is_terminal():
        moves = state.get_legal_moves()
        winning = [m for m in moves if _wins_small_board(state, m)]
        state = state.apply_move(*random.choice(winning if winning else moves))

    winner = state.get_winner()
    if winner == DRAW:
        return 0.0
    return 1.0 if winner == starting_player else -1.0


def mcts(root_state, iterations=1000):
    """Run MCTS and return the best (board_idx, cell_idx) move."""
    root = MCTSNode(root_state)

    for _ in range(iterations):
        # 1. Selection
        node = root
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child()

        # 2. Expansion
        if not node.is_terminal() and not node.is_fully_expanded():
            node = node.expand()

        # 3. Rollout
        score = rollout(node.state)

        # 4. Backpropagation
        # Score was computed from node.state.current_player's perspective.
        # The node itself was just created for the player who *just moved*,
        # so we negate once to align with the node's parent perspective.
        node.backpropagate(-score)

    # Return the move leading to the child with the highest win rate (c=0 → pure exploitation)
    best = max(root.children, key=lambda n: n.visits)
    return best.move


if __name__ == "__main__":
    state = GameState()
    print("Running MCTS for 1000 iterations on the initial state...")
    move = mcts(state, iterations=1000)
    print(f"Best move: board {move[0]}, cell {move[1]}")
