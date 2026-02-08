# Sokoban Solver Design

## Puzzle Representation

The solver separates static level data from dynamic game state using two classes.

### Level (static)

The `Level` class stores everything about the puzzle that never changes during solving:

- **walls**: `frozenset` of `(row, col)` positions
- **goals**: `frozenset` of `(row, col)` positions
- **initial_player**: `(row, col)` starting position
- **initial_boxes**: `frozenset` of `(row, col)` starting positions
- **width / height**: integer dimensions

Levels are parsed from standard Sokoban text format (`#` wall, `@` player, `$` box, `.` goal, `*` box-on-goal, `+` player-on-goal). Using frozensets keeps the static data immutable and hashable.

### SokobanState (dynamic)

Each search state stores only what changes move to move:

- **player**: `(row, col)` current position
- **boxes**: `frozenset` of `(row, col)` current box positions
- **moves**: integer move count from start (the g-cost)
- **parent**: reference to previous state (for path reconstruction)
- **action**: the move that produced this state (`'U'`, `'D'`, `'L'`, `'R'`)

States are hashed and compared by `(player, boxes)` only, so the visited set correctly identifies duplicate configurations regardless of how they were reached.

## Search Algorithm: A*

The solver uses A* search with a priority queue ordered by f-cost = g + h.

1. Start from the initial state with g = 0
2. Pop the lowest f-cost state from the queue
3. If all boxes are on goals, reconstruct and return the solution path
4. Generate successor states (walks and pushes in four directions)
5. Skip successors already in the visited set
6. Add new successors to the queue with their f-cost
7. Stop after exploring `max_states` (default 100,000) if no solution is found

A counter-based tiebreaker ensures consistent ordering when two states have equal f-cost.

## Heuristic

The heuristic uses the **Hungarian algorithm** (via `scipy.optimize.linear_sum_assignment`) to find the optimal one-to-one assignment of boxes to goals.

It builds an NxN cost matrix where `cost[i][j]` is the Manhattan distance from box i to goal j, then finds the assignment that minimizes the total distance. This is stronger than the simpler greedy approach of assigning each box to its nearest goal, because it accounts for the constraint that each goal can only hold one box.

Why this works:

- Each box must end up on exactly one goal, and each goal holds exactly one box — this is an assignment problem
- Manhattan distance is a lower bound on the real number of moves to get a box to a goal
- The optimal assignment of lower bounds is still a lower bound on the total real cost

This makes the heuristic **admissible** (never overestimates), which guarantees A* finds an optimal solution. The tighter bound means A* explores fewer states compared to the greedy nearest-goal heuristic, especially on harder puzzles where boxes compete for nearby goals.

## Deadlock Detection

The solver prunes states where a box is permanently stuck (can never reach a goal). Currently it detects **corner deadlocks**:

A box not on a goal is deadlocked if two adjacent walls form an L-shape around it. The four corner configurations checked are:

- Wall above + wall left
- Wall above + wall right
- Wall below + wall left
- Wall below + wall right

If any box hits a corner deadlock, the entire state is pruned from the search. This avoids wasting time exploring branches that can never lead to a solution.

## Successor Generation

Each state can produce up to four successors (one per direction). Two types of moves:

- **Walk**: Player moves to an empty floor tile (not a wall, not a box)
- **Push**: Player moves into a box, and the box slides one tile in the same direction. The push is only valid if the space behind the box is not a wall or another box.

After generating a push successor, the deadlock check runs before adding it to the queue.

## Solution Output

When a goal state is found, `get_solution_path()` walks the parent chain back to the initial state and returns the reversed list of actions (e.g., `['R', 'R', 'D', 'L']`). The solver returns a dictionary with the solution actions, number of states explored, and solution length.
