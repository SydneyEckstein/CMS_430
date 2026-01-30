"""
Lights Out puzzle using iterative deepening depth-first search (IDDFS)

The Lights Out puzzle consists of an N x N grid of lights, all initially ON.
Pressing a button toggles its state and the states of its four neighbors
(up, down, left, right). The goal is to turn all lights OFF.

This implementation uses iterative deepening, which combines the space
efficiency of DFS with the optimality of BFS.

DSM and Claude, 2026
"""


def create_initial_state(n: int) -> tuple:
    """
    Create the initial state with all lights ON.

    Args:
        n: Size of the grid (n x n)

    Returns:
        A tuple of n*n values, all set to 1 (ON)
    """
    return tuple([1] * (n * n))


def create_goal_state(n: int) -> tuple:
    """
    Create the goal state with all lights OFF.

    Args:
        n: Size of the grid (n x n)

    Returns:
        A tuple of n*n values, all set to 0 (OFF)
    """
    return tuple([0] * (n * n))


def get_index(row: int, col: int, n: int) -> int:
    """
    Convert 2D coordinates to 1D index.

    Args:
        row: Row position
        col: Column position
        n: Grid size

    Returns:
        The 1D index corresponding to (row, col)
    """
    return row * n + col


def get_coords(index: int, n: int) -> tuple:
    """
    Convert 1D index to 2D coordinates.

    Args:
        index: 1D position in the flattened grid
        n: Grid size

    Returns:
        A tuple (row, col) corresponding to the index
    """
    return (index // n, index % n)


def toggle_light(state: tuple, row: int, col: int, n: int) -> tuple:
    """
    Toggle a single light at position (row, col).

    Args:
        state: Current board state
        row: Row of the light to toggle
        col: Column of the light to toggle
        n: Grid size

    Returns:
        New state with the specified light toggled
    """
    # Check bounds
    if row < 0 or row >= n or col < 0 or col >= n:
        return state

    index = get_index(row, col, n)
    state_list = list(state)

    # Toggle: 1 becomes 0, 0 becomes 1
    state_list[index] = 1 - state_list[index]

    return tuple(state_list)


def press_button(state: tuple, row: int, col: int, n: int) -> tuple:
    """
    Press a button at position (row, col), toggling it and its neighbors.

    Args:
        state: Current board state
        row: Row of the button to press
        col: Column of the button to press
        n: Grid size

    Returns:
        New state after pressing the button
    """
    # Toggle the button itself
    new_state = toggle_light(state, row, col, n)

    # Toggle the four neighbors (up, down, left, right)
    new_state = toggle_light(new_state, row - 1, col, n)  # Up
    new_state = toggle_light(new_state, row + 1, col, n)  # Down
    new_state = toggle_light(new_state, row, col - 1, n)  # Left
    new_state = toggle_light(new_state, row, col + 1, n)  # Right

    return new_state


def get_successors(state: tuple, n: int) -> list:
    """
    Generate all successor states by pressing each button once.

    Args:
        state: Current board state (tuple of 0s and 1s)
        n: Grid size

    Returns:
        List of (new_state, button_pressed) tuples representing valid successors
    """
    successors = []

    for row in range(n):
        for col in range(n):
            new_state = press_button(state, row, col, n)
            button_index = get_index(row, col, n)
            successors.append((new_state, button_index))

    return successors


def is_goal(state: tuple, n: int) -> bool:
    """
    Check if all lights are OFF.

    Args:
        state: Current board state
        n: Grid size

    Returns:
        True if all lights are OFF, False otherwise
    """
    return state == create_goal_state(n)


def depth_limited_dfs(state: tuple, moves: list, depth_limit: int, n: int,
                      visited_at_depth: dict, stats: dict, timeout: float,
                      start_time: float) -> tuple:
    """
    Perform depth-limited DFS from the given state.

    Args:
        state: Current board state
        moves: List of moves taken to reach this state
        depth_limit: Maximum depth to explore
        n: Grid size
        visited_at_depth: Dict mapping states to the depth at which they were visited
        stats: Dictionary to track nodes_created and nodes_expanded
        timeout: Maximum time allowed
        start_time: When the search started

    Returns:
        (solution, found, cutoff_occurred) where:
            - solution: tuple of button presses if found, None otherwise
            - found: True if solution was found
            - cutoff_occurred: True if search was cut off due to depth limit
    """
    import time

    # Check timeout periodically
    if stats['nodes_expanded'] % 1000 == 0:
        if timeout and time.time() - start_time > timeout:
            stats['timed_out'] = True
            return (None, False, False)

    # Check if we've reached the goal (check BEFORE depth limit!)
    if is_goal(state, n):
        return (tuple(moves), True, False)

    # Check if we've hit the depth limit
    if len(moves) >= depth_limit:
        return (None, False, True)  # Cutoff occurred

    # Check if we've seen this state at a shallower or equal depth
    current_depth = len(moves)
    if state in visited_at_depth and visited_at_depth[state] <= current_depth:
        return (None, False, False)

    # Mark this state as visited at current depth
    visited_at_depth[state] = current_depth

    # Expand this node
    stats['nodes_expanded'] += 1

    cutoff_occurred = False
    successors = get_successors(state, n)

    for new_state, button in successors:
        stats['nodes_created'] += 1

        if stats.get('timed_out', False):
            return (None, False, False)

        new_moves = moves + [button]
        result, found, cutoff = depth_limited_dfs(
            new_state, new_moves, depth_limit, n,
            visited_at_depth, stats, timeout, start_time
        )

        if found:
            return (result, True, False)
        if cutoff:
            cutoff_occurred = True

    return (None, False, cutoff_occurred)


def solve_lights_out_iddfs(n: int, timeout: float = None) -> dict:
    """
    Solve the Lights Out puzzle using Iterative Deepening DFS.

    The algorithm repeatedly runs depth-limited DFS with increasing depth
    limits until a solution is found. This combines the space efficiency
    of DFS with the optimality of BFS.

    Args:
        n: Size of the grid (n x n)
        timeout: Maximum time in seconds before giving up (None for no limit)

    Returns:
        A dictionary containing:
            - 'solution': tuple of button indices pressed, or None if no solution
            - 'nodes_created': total number of nodes created across all iterations
            - 'nodes_expanded': total number of nodes expanded across all iterations
            - 'timed_out': True if search was stopped due to timeout
            - 'max_depth': the depth at which solution was found (or last depth tried)
    """
    import time
    start_time = time.time()

    if n <= 0:
        return {
            'solution': None,
            'nodes_created': 0,
            'nodes_expanded': 0,
            'timed_out': False,
            'max_depth': 0
        }

    initial_state = create_initial_state(n)

    # Check if already at goal
    if is_goal(initial_state, n):
        return {
            'solution': (),
            'nodes_created': 1,
            'nodes_expanded': 0,
            'timed_out': False,
            'max_depth': 0
        }

    # Statistics tracking (cumulative across all depth iterations)
    stats = {
        'nodes_created': 1,  # Count initial state
        'nodes_expanded': 0,
        'timed_out': False
    }

    # Maximum possible depth is n*n (pressing each button once)
    max_possible_depth = n * n

    for depth_limit in range(1, max_possible_depth + 1):
        # Fresh visited set for each depth iteration (start empty)
        visited_at_depth = {}

        result, found, cutoff = depth_limited_dfs(
            initial_state, [], depth_limit, n,
            visited_at_depth, stats, timeout, start_time
        )

        if stats['timed_out']:
            return {
                'solution': None,
                'nodes_created': stats['nodes_created'],
                'nodes_expanded': stats['nodes_expanded'],
                'timed_out': True,
                'max_depth': depth_limit
            }

        if found:
            return {
                'solution': result,
                'nodes_created': stats['nodes_created'],
                'nodes_expanded': stats['nodes_expanded'],
                'timed_out': False,
                'max_depth': depth_limit
            }

        # If no cutoff occurred, there's no solution at deeper levels
        if not cutoff:
            break

    return {
        'solution': None,
        'nodes_created': stats['nodes_created'],
        'nodes_expanded': stats['nodes_expanded'],
        'timed_out': False,
        'max_depth': max_possible_depth
    }


def print_solution(solution: tuple, n: int) -> None:
    """
    Print the solution showing which buttons to press.

    Args:
        solution: Tuple of button indices to press
        n: Grid size
    """
    if solution is None:
        print(f"\n{n}x{n} Lights Out: No solution found")
        return

    print(f"\n{n}x{n} Lights Out Solution:")
    print(f"Press {len(solution)} button(s):")

    if len(solution) == 0:
        print("  (No buttons need to be pressed - already solved!)")
        return

    # Create a grid showing which buttons to press
    press_grid = [0] * (n * n)
    for button in solution:
        press_grid[button] = 1

    print("\nButtons to press (X marks the spot):")
    print("+" + "---+" * n)

    for row in range(n):
        line = "|"
        for col in range(n):
            index = get_index(row, col, n)
            if press_grid[index] == 1:
                line += " X |"
            else:
                line += "   |"
        print(line)
        print("+" + "---+" * n)

    # Also print as coordinate list
    print("\nButton coordinates (row, col):")
    for button in solution:
        row, col = get_coords(button, n)
        print(f"  ({row}, {col})")


def verify_solution(solution: tuple, n: int) -> bool:
    """
    Verify that a solution correctly turns off all lights.

    Args:
        solution: Tuple of button indices to press
        n: Grid size

    Returns:
        True if the solution is valid, False otherwise
    """
    state = create_initial_state(n)

    for button in solution:
        row, col = get_coords(button, n)
        state = press_button(state, row, col, n)

    return is_goal(state, n)


### Main
import time

print("Lights Out Puzzle Solver - IDDFS Performance Analysis")
print("=" * 70)
print("\nInitial state: All lights ON (*)")
print("Goal: Turn all lights OFF")
print("Pressing a button toggles it and its neighbors")
print("\nRunning Iterative Deepening DFS for progressively larger grids...")
print("(Will stop when solve time exceeds ~1 minute)")
print()

# Store results for summary table
results = []
TIME_LIMIT = 90  # seconds - allow a bit over 1 minute to capture data

for n in range(1, 10):  # Will stop early if time exceeds limit
    print(f"\n{'='*70}")
    print(f"Solving {n}x{n} Lights Out puzzle...")

    start_time = time.time()
    result = solve_lights_out_iddfs(n, timeout=TIME_LIMIT)
    elapsed_time = time.time() - start_time

    solution = result['solution']
    nodes_created = result['nodes_created']
    nodes_expanded = result['nodes_expanded']
    timed_out = result['timed_out']
    max_depth = result['max_depth']

    # Store results
    results.append({
        'n': n,
        'solution_length': len(solution) if solution else None,
        'nodes_created': nodes_created,
        'nodes_expanded': nodes_expanded,
        'time': elapsed_time,
        'timed_out': timed_out,
        'max_depth': max_depth
    })

    print(f"Time: {elapsed_time:.3f} seconds")
    print(f"Nodes created: {nodes_created:,}")
    print(f"Nodes expanded: {nodes_expanded:,}")
    print(f"Solution depth: {max_depth}")

    if timed_out:
        print(f"TIMED OUT after {elapsed_time:.1f} seconds!")
        print(f"Search was incomplete - explored {nodes_expanded:,} nodes before stopping.")
        print(f"\nStopping experiments: {n}x{n} exceeded time limit.")
        break

    if solution is not None:
        print(f"Solution length: {len(solution)} button press(es)")
        print_solution(solution, n)

        # Verify the solution
        if verify_solution(solution, n):
            print("Solution verified!")
        else:
            print("ERROR: Solution verification failed!")
    else:
        print("No solution found (search completed without finding solution)!")

    # Stop if this run took more than 60 seconds (and completed)
    if elapsed_time > 60:
        print(f"\nStopping: {n}x{n} took {elapsed_time:.1f} seconds (> 1 minute)")
        break

# Print summary table
print("\n" + "=" * 70)
print("SUMMARY: IDDFS Performance for Lights Out Puzzle")
print("=" * 70)
print(f"{'N':>3} | {'Grid':>5} | {'Solution':>8} | {'Nodes Created':>14} | {'Nodes Expanded':>14} | {'Time (s)':>10} | {'Status':>10}")
print("-" * 70)
for r in results:
    grid = f"{r['n']}x{r['n']}"
    sol_len = str(r['solution_length']) if r['solution_length'] is not None else "N/A"
    status = "TIMEOUT" if r['timed_out'] else "OK"
    print(f"{r['n']:>3} | {grid:>5} | {sol_len:>8} | {r['nodes_created']:>14,} | {r['nodes_expanded']:>14,} | {r['time']:>10.3f} | {status:>10}")
