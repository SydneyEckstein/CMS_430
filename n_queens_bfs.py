"""
N-queens problem using breadth-first search

DSM and Claude, 2026
"""

from collections import deque
import time

def is_safe(state: tuple, row: int, col: int) -> bool:
    """
    Check if placing a queen at (row, col) is safe given the current state.

    Args:
        state: Current partial solution (tuple of column positions)
        row: Row to place the new queen
        col: Column to place the new queen

    Returns:
        True if placement is safe, False otherwise
    """

    # The built-in enumerate function generates (index, value) pairs for the items
    # in the tuple
    for r, c in enumerate(state):

        # Check column conflict (row conflict is impossible by construction)
        if c == col:
            return False

        # Check diagonal conflict
        if abs(r - row) == abs(c - col):
            return False

    # No conflict was found, so this placement is valid
    return True


def get_successors(state: tuple, n: int) -> list:
    """
    Generate all valid successor states by placing a queen in the next row.
    """

    successors = []
    row = len(state)  # Next row to place a queen

    if row >= n:
        return successors

    for col in range(n):

        # If (row, col) is a safe position, create a successor by appending
        # col to the current state tuple
        if is_safe(state, row, col):
            successors.append(state + (col,))

    return successors


def is_goal(state: tuple, n: int) -> bool:
    return len(state) == n


def solve_n_queens_bfs(n: int) -> dict:
    """
    Solve the N-Queens problem using Breadth-First Search.

    Args:
        n: Size of the board (number of queens)

    Returns:
        A dictionary containing:
            - 'solution': A tuple representing a valid solution, or None if no solution exists
            - 'nodes_created': Number of nodes added to the frontier
            - 'nodes_expanded': Number of nodes removed from frontier and expanded
    """
    if n <= 0:
        return {'solution': None, 'nodes_created': 0, 'nodes_expanded': 0}

    # Track statistics
    nodes_created = 0
    nodes_expanded = 0

    # Initialize empty frontier structure (deque for efficient BFS)
    frontier = deque()

    # Begin with the starting state (empty board)
    initial_state = ()
    frontier.append(initial_state)
    nodes_created += 1

    while len(frontier) > 0:
        # Pop from the front of the queue
        x = frontier.popleft()
        nodes_expanded += 1

        # If x is the goal state, we're done
        if is_goal(x, n):
            return {
                'solution': x,
                'nodes_created': nodes_created,
                'nodes_expanded': nodes_expanded
            }

        # Generate successors of x
        s = get_successors(x, n)

        # Insert new unvisited successor states into frontier
        for i in s:
            frontier.append(i)
            nodes_created += 1

    # No solution was found
    return {
        'solution': None,
        'nodes_created': nodes_created,
        'nodes_expanded': nodes_expanded
    }


def print_board(solution: tuple) -> None:
    """
    Print the chessboard with queens placed.
    """
    if solution is None:
        print("No solution found")
        return

    n = len(solution)
    print(f"\n{n}-Queens Solution:")
    print("+" + "---+" * n)

    for row in range(n):
        line = "|"
        for col in range(n):
            if solution[row] == col:
                line += " Q |"
            else:
                line += "   |"
        print(line)
        print("+" + "---+" * n)


### Main
if __name__ == "__main__":
    print("N-Queens BFS Solver - Performance Analysis")
    print("=" * 70)
    print(f"{'N':>4} | {'Solution Found':^14} | {'Nodes Created':>14} | {'Nodes Expanded':>14} | {'Time (s)':>10}")
    print("-" * 70)

    results = []

    for n in range(1, 20):
        start_time = time.time()
        result = solve_n_queens_bfs(n)
        elapsed_time = time.time() - start_time

        solution = result['solution']
        nodes_created = result['nodes_created']
        nodes_expanded = result['nodes_expanded']

        found = "Yes" if solution is not None else "No"
        print(f"{n:>4} | {found:^14} | {nodes_created:>14,} | {nodes_expanded:>14,} | {elapsed_time:>10.3f}")

        results.append({
            'n': n,
            'solution': solution,
            'nodes_created': nodes_created,
            'nodes_expanded': nodes_expanded,
            'time': elapsed_time
        })

        # Stop if the solve time exceeds ~1 minute
        if elapsed_time > 60:
            print(f"\nStopping: N={n} took {elapsed_time:.1f} seconds (> 1 minute)")
            break

    print("=" * 70)

    # Print a sample solution for visualization
    print("\nSample board visualization for largest solved N:")
    for r in reversed(results):
        if r['solution'] is not None:
            print_board(r['solution'])
            break
