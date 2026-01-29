"""
N-queens problem using iterative deepening search

DSM and Claude, 2026
"""

def is_safe(state: tuple, row: int, col: int) -> bool:
    """
    Check if placing a queen at (row, col) is safe given the current state.
    """
    for r, c in enumerate(state):
        # Check column conflict
        if c == col:
            return False
        # Check diagonal conflict
        if abs(r - row) == abs(c - col):
            return False
    return True


def get_successors(state: tuple, n: int) -> list:
    """
    Generate all valid successor states by placing a queen in the next row.
    """
    successors = []
    row = len(state)

    if row >= n:
        return successors

    for col in range(n):
        if is_safe(state, row, col):
            successors.append(state + (col,))

    return successors


def is_goal(state: tuple, n: int) -> bool:
    return len(state) == n


def depth_limited_search(state: tuple, n: int, depth_limit: int, stats: dict) -> tuple:
    """
    Perform depth-limited DFS from the given state.

    Args:
        state: Current board state
        n: Board size
        depth_limit: Maximum depth to search
        stats: Dictionary to track nodes created/expanded

    Returns:
        Solution tuple if found, None otherwise
    """
    current_depth = len(state)

    # Expand this node
    stats['expanded'] += 1

    # Check if this is a goal state
    if is_goal(state, n):
        return state

    # If at depth limit, don't generate successors
    if current_depth >= depth_limit:
        return None

    # Generate and explore successors
    successors = get_successors(state, n)

    for successor in successors:
        stats['created'] += 1
        result = depth_limited_search(successor, n, depth_limit, stats)
        if result is not None:
            return result

    return None


def solve_n_queens_ids(n: int) -> dict:
    """
    Solve the N-Queens problem using Iterative Deepening Search.

    Args:
        n: Size of the board (number of queens)

    Returns:
        A dict with 'solution', 'nodes_created', and 'nodes_expanded'
    """
    if n <= 0:
        return {'solution': None, 'nodes_created': 0, 'nodes_expanded': 0}

    total_created = 0
    total_expanded = 0

    # Iteratively increase depth limit from 0 to n
    for depth_limit in range(n + 1):
        # Stats for this iteration
        stats = {'created': 1, 'expanded': 0}  # Count initial state as created

        initial_state = ()
        result = depth_limited_search(initial_state, n, depth_limit, stats)

        total_created += stats['created']
        total_expanded += stats['expanded']

        if result is not None:
            return {
                'solution': result,
                'nodes_created': total_created,
                'nodes_expanded': total_expanded
            }

    return {
        'solution': None,
        'nodes_created': total_created,
        'nodes_expanded': total_expanded
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
print("Iterative Deepening Search Results")
print(f"{'n':<4} {'Created':<12} {'Expanded':<12} {'Solution Found'}")
print("-" * 45)

for n in range(1, 10):
    result = solve_n_queens_ids(n)
    solution = result['solution']
    created = result['nodes_created']
    expanded = result['nodes_expanded']
    found = "Yes" if solution else "No"
    print(f"{n:<4} {created:<12} {expanded:<12} {found}")
