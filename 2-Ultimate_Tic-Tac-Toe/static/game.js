// Constants matching game.py
const EMPTY = 0, X = 1, O = 2, DRAW = 3;
const SYMBOLS = { [X]: 'X', [O]: 'O', [DRAW]: '–' };

const WIN_LINES = [
  [0,1,2],[3,4,5],[6,7,8],
  [0,3,6],[1,4,7],[2,5,8],
  [0,4,8],[2,4,6],
];

// ── State ─────────────────────────────────────────────────────────────────────
let gameState = null;   // { cells, small_board_winners, active_board, current_player }
let mode = 'human-ai';  // 'human-ai' | 'human-human'
let aiPlayer = O;       // AI always plays O in human-ai mode
let waiting = false;    // true while awaiting AI response
let lastMove = null;    // { boardIdx, cellIdx } of the most recent move

// ── Init ──────────────────────────────────────────────────────────────────────
document.getElementById('new-game-btn').addEventListener('click', newGame);
document.getElementById('mode-select').addEventListener('change', e => {
  mode = e.target.value;
  newGame();
});

buildBoard();
newGame();

// ── Build static DOM ──────────────────────────────────────────────────────────
function buildBoard() {
  const large = document.getElementById('large-board');
  large.innerHTML = '';
  for (let b = 0; b < 9; b++) {
    const sb = document.createElement('div');
    sb.className = 'small-board';
    sb.dataset.board = b;

    for (let c = 0; c < 9; c++) {
      const cell = document.createElement('div');
      cell.className = 'cell';
      cell.dataset.board = b;
      cell.dataset.cell = c;
      cell.addEventListener('click', onCellClick);
      sb.appendChild(cell);
    }

    const overlay = document.createElement('div');
    overlay.className = 'board-overlay';
    sb.appendChild(overlay);

    large.appendChild(sb);
  }
}

// ── New game ──────────────────────────────────────────────────────────────────
function newGame() {
  mode = document.getElementById('mode-select').value;
  waiting = false;
  lastMove = null;
  gameState = {
    cells: Array(81).fill(EMPTY),
    small_board_winners: Array(9).fill(EMPTY),
    active_board: null,
    current_player: X,
  };
  render();
}

// ── Click handler ─────────────────────────────────────────────────────────────
async function onCellClick(e) {
  if (!gameState || waiting) return;

  const boardIdx = parseInt(e.currentTarget.dataset.board);
  const cellIdx  = parseInt(e.currentTarget.dataset.cell);

  // In human-ai mode, ignore clicks when it's the AI's turn
  if (mode === 'human-ai' && gameState.current_player === aiPlayer) return;

  if (!isLegalMove(gameState, boardIdx, cellIdx)) return;

  // Apply human move
  gameState = await postMove(gameState, boardIdx, cellIdx);
  if (!gameState) return;
  lastMove = { boardIdx, cellIdx };
  render();

  // If human-ai mode and game not over, get AI move
  if (mode === 'human-ai' && !isTerminal(gameState)) {
    await doAiMove();
  }
}

// ── AI move ───────────────────────────────────────────────────────────────────
async function doAiMove() {
  waiting = true;
  setStatus('AI is thinking…', 'thinking');

  const iterations = parseInt(document.getElementById('difficulty-select').value);
  const result = await postAiMove(gameState, iterations);
  waiting = false;

  if (!result) return;
  gameState = result;
  render();
}

// ── API calls ─────────────────────────────────────────────────────────────────
async function postMove(state, boardIdx, cellIdx) {
  try {
    const res = await fetch('/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state, board_idx: boardIdx, cell_idx: cellIdx }),
    });
    const data = await res.json();
    if (!res.ok) { console.error(data.error); return null; }
    return data.state;
  } catch (err) {
    console.error('postMove error:', err);
    return null;
  }
}

async function postAiMove(state, iterations) {
  try {
    const res = await fetch('/ai_move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state, iterations }),
    });
    const data = await res.json();
    if (!res.ok) { console.error(data.error); return null; }
    if (data.move) lastMove = { boardIdx: data.move.board_idx, cellIdx: data.move.cell_idx };
    return data.state;
  } catch (err) {
    console.error('postAiMove error:', err);
    return null;
  }
}

// ── Render ────────────────────────────────────────────────────────────────────
function render() {
  if (!gameState) return;
  const { cells, small_board_winners, active_board, current_player } = gameState;

  // Update each small board
  for (let b = 0; b < 9; b++) {
    const sbEl = document.querySelector(`.small-board[data-board="${b}"]`);
    const winner = small_board_winners[b];

    // Board class
    sbEl.className = 'small-board';
    if (winner === X)    sbEl.classList.add('won-x');
    else if (winner === O)    sbEl.classList.add('won-o');
    else if (winner === DRAW) sbEl.classList.add('drawn');
    else if (active_board === null || active_board === b) sbEl.classList.add('active');

    // Overlay text
    const overlay = sbEl.querySelector('.board-overlay');
    overlay.textContent = winner === X ? 'X' : winner === O ? 'O' : winner === DRAW ? '–' : '';

    // Cells
    for (let c = 0; c < 9; c++) {
      const cellEl = sbEl.children[c]; // overlay is last child
      const val = cells[b * 9 + c];

      cellEl.className = 'cell';
      cellEl.textContent = '';

      if (val === X) {
        cellEl.classList.add('x', 'taken');
        cellEl.textContent = 'X';
      } else if (val === O) {
        cellEl.classList.add('o', 'taken');
        cellEl.textContent = 'O';
      } else if (!isLegalMove(gameState, b, c)) {
        cellEl.classList.add('inactive');
      }

      if (lastMove && lastMove.boardIdx === b && lastMove.cellIdx === c) {
        cellEl.classList.add('last-move');
      }
    }
  }

  // Status bar
  const w = getWinner(gameState);
  if (w === X) {
    setStatus('X wins!', 'x-wins');
  } else if (w === O) {
    setStatus('O wins!', 'o-wins');
  } else if (w === DRAW) {
    setStatus('Draw!', 'draw');
  } else {
    const player = current_player === X ? 'X' : 'O';
    const cls = current_player === X ? 'x-turn' : 'o-turn';
    const label = (mode === 'human-ai' && current_player === aiPlayer) ? `${player}'s turn (AI)` : `${player}'s turn`;
    setStatus(label, cls);
  }
}

function setStatus(text, cls) {
  const el = document.getElementById('status');
  el.textContent = text;
  el.className = cls || '';
}

// ── Local game logic helpers (mirror game.py) ─────────────────────────────────
function checkWinner(arr) {
  for (const [a,b,c] of WIN_LINES) {
    if (arr[a] !== EMPTY && arr[a] === arr[b] && arr[b] === arr[c]) return arr[a];
  }
  return null;
}

function isLegalMove(state, boardIdx, cellIdx) {
  const { cells, small_board_winners, active_board } = state;
  if (isTerminal(state)) return false;
  if (small_board_winners[boardIdx] !== EMPTY) return false;
  if (active_board !== null && active_board !== boardIdx) return false;
  return cells[boardIdx * 9 + cellIdx] === EMPTY;
}

function isTerminal(state) {
  return getWinner(state) !== null;
}

function getWinner(state) {
  const lw = checkWinner(state.small_board_winners);
  if (lw) return lw;
  // Draw: no legal moves
  for (let b = 0; b < 9; b++) {
    for (let c = 0; c < 9; c++) {
      if (isLegalMoveRaw(state, b, c)) return null; // game still ongoing
    }
  }
  return DRAW;
}

function isLegalMoveRaw(state, boardIdx, cellIdx) {
  const { cells, small_board_winners, active_board } = state;
  if (small_board_winners[boardIdx] !== EMPTY) return false;
  if (active_board !== null && active_board !== boardIdx) return false;
  return cells[boardIdx * 9 + cellIdx] === EMPTY;
}
