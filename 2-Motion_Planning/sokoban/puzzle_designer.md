# Puzzle Designer — Design Document

## Overview

Add a puzzle designer to the Sokoban web interface that lets users create custom
puzzles by setting the grid size and placing walls, boxes, goals, and a player.
Custom puzzles can then be played manually or sent to the A* solver.

## Grid Initialization

- User sets **width** and **height** (range 4–15, default 7×7)
- Clicking **Create Grid** generates the room:
  - All perimeter cells are filled with walls automatically
  - All interior cells start empty (floor)
- Perimeter walls are **locked** — clicking them does nothing

## Tool Palette

A row of toggle buttons selects the active placement tool:

| Tool    | Symbol | Places         |
|---------|--------|----------------|
| Wall    | `#`    | Interior wall  |
| Box     | `$`    | Box            |
| Goal    | `.`    | Goal location  |
| Player  | `@`    | Player start   |
| Eraser  | ` `    | Clears cell    |

- The active tool stays selected until a different one is clicked
- Clicking an interior cell places the active tool, **replacing** whatever was there
- **Player** is unique: placing a new player removes the old one

## Validation (before Play or Solve)

1. Exactly **1 player** placed
2. At least **1 box**
3. Number of **boxes = number of goals**

Error messages display in the status area if validation fails.

## Data Flow

### Editor State (JavaScript)

Reuses the existing `walls`, `boxes`, `goals`, and `player` variables, plus:

- `editorWidth`, `editorHeight` — grid dimensions
- `activeTool` — currently selected tool (`'wall'`, `'box'`, `'goal'`, `'player'`, `'eraser'`)
- `mode = 'editor'` — new UI mode alongside `'idle'`, `'play'`, `'solution'`

### Conversion to ASCII

The existing `buildBoardString()` function already iterates over the grid and
maps cells to Sokoban characters (`#`, `@`, `$`, `.`, `*`, `+`, ` `). This is
reused directly for both playing and solving custom puzzles.

### Backend Endpoint

**`POST /api/solve-custom`**

- Request body: `{"board": "<ASCII board string>"}`
- Parses with `Level.from_string(board)` (existing code, includes validation)
- Runs `solve(level)` and returns the same response format as `/api/solve`
- Returns error messages for invalid puzzles (no player, mismatched counts, etc.)

## UI Layout

The editor is a **same-page toggle**:

- A **Design Puzzle** button next to the puzzle selector switches into editor mode
- Editor mode hides the puzzle selector and shows:
  - Width/height inputs + Create Grid button
  - Tool palette
  - The board (click to place)
  - Play / Solve / Clear Interior buttons
- A **Back to Puzzles** button returns to the preset puzzle list

## Files Modified

| File | Change |
|------|--------|
| `app.py` | Add `/api/solve-custom` endpoint |
| `templates/index.html` | Add editor UI, tool palette, click handling, validation |
| `solver.py` | No changes — reuse `Level.from_string()` and `solve()` |
