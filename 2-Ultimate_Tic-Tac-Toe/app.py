from flask import Flask, request, jsonify, render_template

from game import GameState, X, O, DRAW, EMPTY
from mcts import mcts

app = Flask(__name__)


# ── Serialization helpers ─────────────────────────────────────────────────────

def state_to_dict(state):
    return {
        "cells": state.cells,
        "small_board_winners": state.small_board_winners,
        "active_board": state.active_board,
        "current_player": state.current_player,
    }


def dict_to_state(d):
    s = GameState.__new__(GameState)
    s.cells = list(d["cells"])
    s.small_board_winners = list(d["small_board_winners"])
    s.active_board = d["active_board"]  # None or int
    s.current_player = int(d["current_player"])
    return s


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/move", methods=["POST"])
def move():
    data = request.get_json(force=True)
    try:
        state = dict_to_state(data["state"])
        board_idx = int(data["board_idx"])
        cell_idx = int(data["cell_idx"])
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Bad request: {e}"}), 400

    if state.is_terminal():
        return jsonify({"error": "Game is already over"}), 400

    legal = state.get_legal_moves()
    if (board_idx, cell_idx) not in legal:
        return jsonify({"error": "Illegal move"}), 400

    new_state = state.apply_move(board_idx, cell_idx)
    return jsonify({"state": state_to_dict(new_state)})


@app.route("/ai_move", methods=["POST"])
def ai_move():
    data = request.get_json(force=True)
    try:
        state = dict_to_state(data["state"])
        iterations = int(data.get("iterations", 1000))
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Bad request: {e}"}), 400

    if state.is_terminal():
        return jsonify({"error": "Game is already over"}), 400

    board_idx, cell_idx = mcts(state, iterations=iterations)
    new_state = state.apply_move(board_idx, cell_idx)
    return jsonify({
        "move": {"board_idx": board_idx, "cell_idx": cell_idx},
        "state": state_to_dict(new_state),
    })


if __name__ == "__main__":
    app.run(debug=True)
