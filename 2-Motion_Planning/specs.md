# Motion Planning with A* Search

## Overview

A motion planning program that uses A* search to find the shortest path from a start position to a goal position in randomly generated grid worlds. If no path exists, the program reports that.

## Grid World

- The world is a R by C grid, indexed from 0 in both dimensions
- Obstacles in the grid have the value `1` and free squares have the value `0`
- The boundaries of the world are always enclosed by walls of `1`s, so we don't need to consider special cases for stepping off the edge of the grid
- Interior cells are randomly set to obstacles based on `obstacle_prob`
- The start square is always at position `(1, 1)`
- The goal square is always at position `(R - 2, C - 2)`
- The robot can move up, down, left, and right, but not diagonally
- Random seed is fixed at `0` for reproducibility

## Search Algorithm

- **Algorithm**: A* search built on a breadth-first search structure
- **Data structure**: `PriorityQueue` from Python's `queue` module
- **Priority function**: `f(n) = g(n) + h(n)`
  - `g(n)`: total moves from start (stored as `total_moves`)
  - `h(n)`: Manhattan distance from current position to goal (`|row_diff| + |col_diff|`)
- **Queue entries**: stored as tuples `(priority, state)` — the queue orders by the first element
- **Visited tracking**: dictionary keyed by position tuples to avoid revisiting squares
- **Moves**: 4-directional (up, down, left, right) — no diagonal movement
- **State representation**: each `State` holds its own `deepcopy` of the grid, with the path so far marked as `*`

## State Class

- `position`: current `(row, col)` tuple
- `goal`: goal `(row, col)` tuple
- `grid`: copy of the grid with `*` marking the path taken
- `total_moves`: number of moves from start (g-cost)
- `manhattan_distance()`: returns the heuristic h-cost
- `generate_successors()`: returns new states for each valid adjacent move
- `__lt__()`: tie-breaking comparison for the priority queue (fewer moves preferred)

## Output

For each trial, the program prints:
1. The original grid (spaces for free cells, `1` for obstacles)
2. Either:
   - The solution grid with `*` marking the shortest path from start to goal, or
   - `"No path exists."` if the goal is unreachable

## Difficulty Levels

| Level  | Rows | Cols | Obstacle Prob | Trials |
|--------|------|------|---------------|--------|
| Easy   | 8    | 16   | 0.20          | 5      |
| Hard   | 15   | 30   | 0.30          | 5      |
| Insane | 20   | 60   | 0.35          | 5      |

## Constraints

- `create_grid()` and `print_grid()` must not be modified
- Random seed is `0` — output is deterministic
