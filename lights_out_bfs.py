"""
Lights Out puzzle using breadth-first search

The Lights Out puzzle consists of an N x N grid of lights, all initially ON.
Pressing a button toggles its state and the states of its four neighbors
(up, down, left, right). The goal is to turn all lights OFF.

This implementation uses BFS on board configurations with visited state
tracking to efficiently find the minimum number of button presses needed.

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


def solve_lights_out_bfs(n: int, timeout: float = None) -> dict:
    """
    Solve the Lights Out puzzle using Breadth-First Search.

    The algorithm explores board configurations, tracking visited states
    to avoid cycles. BFS guarantees finding the minimum number of button
    presses needed to solve the puzzle.

    Args:
        n: Size of the grid (n x n)
        timeout: Maximum time in seconds before giving up (None for no limit)

    Returns:
        A dictionary containing:
            - 'solution': tuple of button indices pressed, or None if no solution
            - 'nodes_created': number of nodes added to the frontier
            - 'nodes_expanded': number of nodes popped from the frontier
            - 'timed_out': True if search was stopped due to timeout
    """
    import time
    start_time = time.time()

    if n <= 0:
        return {'solution': None, 'nodes_created': 0, 'nodes_expanded': 0, 'timed_out': False}

    # Statistics tracking
    nodes_created = 0
    nodes_expanded = 0

    # Initialize frontier structure (queue for BFS)
    # Each entry is (state, list_of_moves_to_reach_this_state)
    frontier = []

    # Track visited states to avoid cycles
    visited = set()

    # Begin with the starting state (all lights ON)
    initial_state = create_initial_state(n)

    # Check if already at goal (edge case)
    if is_goal(initial_state, n):
        return {'solution': (), 'nodes_created': 1, 'nodes_expanded': 0, 'timed_out': False}

    frontier.append((initial_state, []))
    visited.add(initial_state)
    nodes_created += 1

    while len(frontier) > 0:
        # Check timeout periodically (every 1000 expansions)
        if timeout and nodes_expanded % 1000 == 0:
            if time.time() - start_time > timeout:
                return {
                    'solution': None,
                    'nodes_created': nodes_created,
                    'nodes_expanded': nodes_expanded,
                    'timed_out': True
                }

        # Pop from the front of the queue (BFS)
        state, moves = frontier.pop(0)
        nodes_expanded += 1

        # Generate all successor states by pressing each button
        successors = get_successors(state, n)

        for new_state, button in successors:
            # Skip if we've already visited this state
            if new_state in visited:
                continue

            # Create the new move sequence
            new_moves = moves + [button]

            # Check if we've reached the goal
            if is_goal(new_state, n):
                return {
                    'solution': tuple(new_moves),
                    'nodes_created': nodes_created + 1,
                    'nodes_expanded': nodes_expanded,
                    'timed_out': False
                }

            # Mark as visited and add to frontier
            visited.add(new_state)
            frontier.append((new_state, new_moves))
            nodes_created += 1

    # No solution was found
    return {
        'solution': None,
        'nodes_created': nodes_created,
        'nodes_expanded': nodes_expanded,
        'timed_out': False
    }


def print_board(state: tuple, n: int) -> None:
    """
    Print the current board state.

    Args:
        state: Board state to display
        n: Grid size
    """
    print("+" + "---+" * n)

    for row in range(n):
        line = "|"
        for col in range(n):
            index = get_index(row, col, n)
            if state[index] == 1:
                line += " * |"  # Light ON
            else:
                line += "   |"  # Light OFF
        print(line)
        print("+" + "---+" * n)


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

print("Lights Out Puzzle Solver - BFS Performance Analysis")
print("=" * 70)
print("\nInitial state: All lights ON (*)")
print("Goal: Turn all lights OFF")
print("Pressing a button toggles it and its neighbors")
print("\nRunning BFS for progressively larger grids...")
print("(Will stop when solve time exceeds ~1 minute)")
print()

# Store results for summary table
results = []
TIME_LIMIT = 90  # seconds - allow a bit over 1 minute to capture data

for n in range(1, 10):  # Will stop early if time exceeds limit
    print(f"\n{'='*70}")
    print(f"Solving {n}x{n} Lights Out puzzle...")

    start_time = time.time()
    result = solve_lights_out_bfs(n, timeout=TIME_LIMIT)
    elapsed_time = time.time() - start_time

    solution = result['solution']
    nodes_created = result['nodes_created']
    nodes_expanded = result['nodes_expanded']
    timed_out = result['timed_out']

    # Store results
    results.append({
        'n': n,
        'solution_length': len(solution) if solution else None,
        'nodes_created': nodes_created,
        'nodes_expanded': nodes_expanded,
        'time': elapsed_time,
        'timed_out': timed_out
    })

    print(f"Time: {elapsed_time:.3f} seconds")
    print(f"Nodes created: {nodes_created:,}")
    print(f"Nodes expanded: {nodes_expanded:,}")

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
print("SUMMARY: BFS Performance for Lights Out Puzzle")
print("=" * 70)
print(f"{'N':>3} | {'Grid':>5} | {'Solution':>8} | {'Nodes Created':>14} | {'Nodes Expanded':>14} | {'Time (s)':>10} | {'Status':>10}")
print("-" * 70)
for r in results:
    grid = f"{r['n']}x{r['n']}"
    sol_len = str(r['solution_length']) if r['solution_length'] is not None else "N/A"
    status = "TIMEOUT" if r['timed_out'] else "OK"
    print(f"{r['n']:>3} | {grid:>5} | {sol_len:>8} | {r['nodes_created']:>14,} | {r['nodes_expanded']:>14,} | {r['time']:>10.3f} | {status:>10}")
