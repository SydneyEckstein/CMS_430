# Ultimate Tic-Tac-Toe

A web-based Ultimate Tic-Tac-Toe game with a Monte Carlo Tree Search (MCTS) AI opponent.

## Running the game

```bash
pip install flask
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

## Controls

| Control | Options |
|---------|---------|
| Mode | Human vs AI, Human vs Human |
| AI Difficulty | Easy (300 iterations), Medium (1000), Hard (3000) |
| New Game | Resets the board at any time |

## MCTS Iteration Count Experiments

Timings measured on a mid-game state (10 moves in), averaged over 5 trials.

### Pure random rollout (baseline)

| Iterations | Avg response time | Notes |
|------------|------------------|-------|
| 300        | ~98 ms           | Fast but shallow; misses obvious tactics |
| 1000       | ~403 ms          | Reasonable default; noticeable but acceptable delay |
| 3000       | ~1184 ms         | Strong play; ~1 second wait |
| 5000       | ~1982 ms         | Strongest; ~2 second wait |

### Heuristic rollout (prefer small-board wins)

| Iterations | Avg response time | Notes |
|------------|------------------|-------|
| 300        | ~135 ms          | Slightly slower per iteration but meaningfully stronger than random-300 |
| 1000       | ~569 ms          | **Default** — good balance of speed and quality |
| 3000       | ~1572 ms         | Strong; recommended for competitive play |
| 5000       | ~2563 ms         | Strongest available; ~2.5 second wait |

### Key observations

- The heuristic rollout adds ~35–40% overhead per iteration but significantly improves
  play quality at low iteration counts (300–1000), where each rollout's outcome matters more.
- At 5000 iterations, both policies produce strong play; the heuristic edge diminishes
  as the tree is explored more thoroughly regardless of rollout quality.
- **Recommended settings:**
  - Casual play: Easy (300) with heuristic rollout — responsive and still competent
  - Competitive play: Hard (3000) — strong AI, ~1.5 second think time
  - For the fastest possible AI, reduce to 200 iterations; play quality drops noticeably below 300.

## Architecture

```
app.py          — Flask API (GET /, POST /move, POST /ai_move)
game.py         — Pure game logic (no UI or AI dependencies)
mcts.py         — MCTS with UCB1 selection and heuristic rollouts
templates/
  index.html    — Single-page UI
static/
  style.css     — Dark-theme responsive styles
  game.js       — Game state management and API calls
```
