# Sokoban Web Interface Specs

## Overview

A web interface for the Sokoban solver. Users load a pre-designed puzzle on a front-end page, submit it to the back-end solver, and step through the solution to verify correctness. The server processes one puzzle at a time.

## Architecture

- **Backend:** Python Flask, serves the frontend and exposes a REST API
- **Frontend:** Single HTML page with embedded CSS and JavaScript
- **Solver:** Existing `solver.py` module, called directly from the backend

## API

### `GET /api/puzzles`

Returns the list of available pre-designed puzzles.

**Response:**
```json
{
  "puzzles": [
    {"id": "1-box-trivial", "name": "1-Box Trivial"},
    {"id": "3-box-room", "name": "3-Box Room"},
    ...
  ]
}
```

### `POST /api/solve`

Submits a puzzle to be solved.

**Request:**
```json
{
  "puzzle_id": "3-box-room"
}
```

**Response (success):**
```json
{
  "success": true,
  "solution_length": 13,
  "states_explored": 621,
  "steps": [
    {"move": 0, "action": null,  "board": "########\n#  . . #\n# $ $  #\n#  @$. #\n########"},
    {"move": 1, "action": "R",   "board": "########\n#  . . #\n# $ $  #\n#   @* #\n########"},
    ...
  ]
}
```

Each entry in `steps` contains:
- `move`: step number (0 = initial state)
- `action`: the direction moved (`"U"`, `"D"`, `"L"`, `"R"`) or `null` for the initial state
- `board`: the full board rendered as a string using standard Sokoban characters

**Response (failure):**
```json
{
  "success": false,
  "error": "No solution found (explored 100000 states)"
}
```

**Response (invalid puzzle):**
```json
{
  "success": false,
  "error": "Unknown puzzle ID: bad-id"
}
```

## Frontend

### Layout

1. **Puzzle selector** — dropdown populated from `GET /api/puzzles`
2. **Solve button** — sends `POST /api/solve` with the selected puzzle ID
3. **Board display** — renders the current step as a styled grid
4. **Step controls** — Previous / Next buttons and a step counter ("Step 3 of 13")
5. **Status bar** — shows solution length and states explored after solving

### Behavior

- On page load, fetch puzzle list and populate the dropdown
- Clicking "Solve" disables the button, shows a loading indicator, and calls the API
- On response, store the steps array and display step 0 (initial state)
- Previous/Next buttons navigate through the steps array
- The board display maps Sokoban characters to styled grid cells:
  - `#` wall, `@` player, `$` box, `.` goal, `*` box on goal, `+` player on goal, ` ` floor

## Pre-designed Puzzles

The server stores these puzzles (all tested and verified solvable):

| ID | Name | Size | Boxes |
|---|---|---|---|
| 1-box-trivial | 1-Box Trivial | 5x3 | 1 |
| 1-box-walls | 1-Box With Walls | 6x5 | 1 |
| 2-box-l-shape | 2-Box L-Shape | 6x5 | 2 |
| 3-box-room | 3-Box Room | 8x5 | 3 |
| 3-box-corridor | 3-Box Corridor | 8x5 | 3 |
| 4-box-classic | 4-Box Classic | 8x6 | 4 |
| 4-box-square | 4-Box Square | 7x7 | 4 |
| 5-box-open | 5-Box Open | 8x7 | 5 |
| microban-1 | Microban #1 | 6x7 | 2 |

## Solver Integration

The backend reuses three existing functions from `solver.py`:
- `Level.from_string(puzzle_string)` — parse the stored puzzle text
- `solve(level)` — run A* search, returns result dict with the goal state
- `level.to_string(state)` — render the board at any state

To build the steps array, walk the goal state's parent chain to collect all intermediate states, reverse the list, and render each one.
