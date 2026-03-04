# Ultimate Tic-Tac-Toe — Implementation Plan

## Project Overview
A web-based Ultimate Tic-Tac-Toe game where the AI opponent uses Monte Carlo Tree Search (MCTS) with the UCB1 tree descent policy.

---

## Phase 1: Game Logic (Backend)

**Goal:** Implement the core game rules as a self-contained Python module.

### Tasks
- Represent the board as a 9x9 grid (or 9 small boards of 9 cells each)
- Track:
  - Cell ownership (X, O, empty)
  - Small board winners (X, O, draw, active)
  - Which small board is currently active (or "free choice")
  - Whose turn it is
- Implement move validation:
  - A move is valid only on the active small board (or any active board if free choice)
  - No moves on won/drawn small boards
- Implement win detection:
  - Small board win: standard tic-tac-toe on a 3x3 grid
  - Large board win: standard tic-tac-toe across the 9 small board results
  - Draw: no valid moves remain or large board draw is unavoidable
- Implement `get_legal_moves()`, `apply_move()`, `is_terminal()`, `get_winner()`

### Deliverables
- `game.py` — pure game logic, no UI or AI dependencies

---

## Phase 2: MCTS AI

**Goal:** Implement the Monte Carlo Tree Search algorithm.

### Tasks
- Implement the MCTS node structure:
  - State, parent, children, visit count, total score
- Implement the four MCTS stages:
  1. **Selection** — descend tree using UCB1 until a node with unexplored children is found
  2. **Expansion** — add one new child node for an unexplored move
  3. **Rollout** — simulate a random game from the new node to a terminal state
  4. **Backpropagation** — update visit counts and scores up the tree
- UCB1 formula: `score/visits + C * sqrt(ln(parent_visits) / visits)` where C = √2
- Scoring: +1 win for current player, -1 loss, 0 draw
- Run for a configurable maximum number of iterations (default: 1000)
- Return the root child with the highest win rate as the chosen move

### Deliverables
- `mcts.py` — MCTS implementation using `game.py`

---

## Phase 3: Web Interface

**Goal:** Build a browser-based UI to play the game.

### Tasks
- Create a single-page app using HTML, CSS, and JavaScript
- Render the 9x9 board as a 3x3 grid of 3x3 small boards
- Visually distinguish:
  - Active small board (highlighted border)
  - Won small boards (overlay with X or O symbol)
  - Drawn small boards (grayed out)
  - Current player's turn
- Handle click events for human moves
- Communicate with the backend via a simple API (see Phase 4)
- Display game status: whose turn, winner, or draw

### Deliverables
- `templates/index.html`
- `static/style.css`
- `static/game.js`

---

## Phase 4: Backend API (Flask)

**Goal:** Serve the UI and expose game logic + AI via HTTP endpoints.

### Endpoints
- `GET /` — serve the main page
- `POST /move` — accepts current game state + human move, returns updated state
- `POST /ai_move` — accepts current game state, runs MCTS, returns AI move + updated state

### Tasks
- Serialize/deserialize game state as JSON
- Wire human moves through `game.py`
- Wire AI moves through `mcts.py`
- Handle edge cases: invalid moves, terminal states

### Deliverables
- `app.py` — Flask application

---

## Phase 5: Tuning & Polish

**Goal:** Make the game playable and the AI competitive.

### Tasks
- Experiment with MCTS iteration counts (e.g., 500, 1000, 5000) and note the tradeoff between move quality and response time
- Add a UI control to let the user select AI difficulty (maps to iteration count)
- Add a "New Game" button
- Add option for human vs human or human vs AI
- Improve rollout policy if pure random produces weak play (optional: prefer winning moves in rollouts)
- Add move animation or highlighting of last move played

### Deliverables
- Updated UI with difficulty selector
- Notes in `README.md` on iteration count experiments

---

## File Structure

```
2-Ultimate_Tic-Tac-Toe/
├── specs.md
├── README.md
├── app.py
├── game.py
├── mcts.py
├── static/
│   ├── style.css
│   └── game.js
└── templates/
    └── index.html
```

---

## Implementation Order

1. Phase 1 — Game logic (foundation for everything)
2. Phase 2 — MCTS AI (depends on game logic)
3. Phase 4 — Flask API (wires logic + AI together)
4. Phase 3 — Web UI (depends on API)
5. Phase 5 — Tuning & polish
