"""
Flask backend for the Sokoban solver web interface.
"""

from flask import Flask, jsonify, request, render_template
from solver import Level, solve

app = Flask(__name__)

# Pre-designed puzzles (all tested and verified solvable)
PUZZLES = {
    "1-box-trivial": {
        "name": "1-Box Trivial",
        "data": "#####\n#@$.#\n#####"
    },
    "1-box-walls": {
        "name": "1-Box With Walls",
        "data": "######\n#. # #\n# $@ #\n#    #\n######"
    },
    "2-box-l-shape": {
        "name": "2-Box L-Shape",
        "data": "######\n#    #\n# $$.#\n#  .@#\n######"
    },
    "3-box-room": {
        "name": "3-Box Room",
        "data": "########\n#  . . #\n# $ $  #\n#  @$. #\n########"
    },
    "3-box-corridor": {
        "name": "3-Box Corridor",
        "data": "########\n#.  $  #\n#.$ @$.#\n#      #\n########"
    },
    "4-box-classic": {
        "name": "4-Box Classic",
        "data": "########\n# .. . #\n# $$$  #\n#  @$  #\n#    . #\n########"
    },
    "4-box-square": {
        "name": "4-Box Square",
        "data": "#######\n#     #\n# .$. #\n# $.$ #\n#  @  #\n#     #\n#######"
    },
    "5-box-open": {
        "name": "5-Box Open",
        "data": "########\n#..  . #\n# $$ $ #\n#  @   #\n#  $$..#\n#      #\n########"
    },
    "microban-1": {
        "name": "Microban #1",
        "data": "######\n#    #\n# #@ #\n# $  #\n# .$ #\n#  .##\n######"
    },
}


def get_solution_states(goal_state):
    """Walk the parent chain to collect all states from initial to goal."""
    states = []
    state = goal_state
    while state is not None:
        states.append(state)
        state = state.parent
    return list(reversed(states))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/puzzles")
def list_puzzles():
    puzzles = [
        {"id": pid, "name": info["name"]}
        for pid, info in PUZZLES.items()
    ]
    return jsonify({"puzzles": puzzles})


@app.route("/api/puzzle/<puzzle_id>")
def get_puzzle(puzzle_id):
    if puzzle_id not in PUZZLES:
        return jsonify({"success": False, "error": f"Unknown puzzle ID: {puzzle_id}"}), 400

    level = Level.from_string(PUZZLES[puzzle_id]["data"])
    return jsonify({
        "success": True,
        "name": PUZZLES[puzzle_id]["name"],
        "board": level.to_string(),
        "walls": list(level.walls),
        "goals": list(level.goals),
        "boxes": list(level.initial_boxes),
        "player": list(level.initial_player),
        "width": level.width,
        "height": level.height,
    })


@app.route("/api/solve", methods=["POST"])
def solve_puzzle():
    data = request.get_json()
    puzzle_id = data.get("puzzle_id")

    if puzzle_id not in PUZZLES:
        return jsonify({"success": False, "error": f"Unknown puzzle ID: {puzzle_id}"}), 400

    level = Level.from_string(PUZZLES[puzzle_id]["data"])
    result = solve(level)

    if not result["success"]:
        return jsonify({
            "success": False,
            "error": f"No solution found (explored {result['states_explored']} states)"
        })

    # Build step-by-step board states
    states = get_solution_states(result["goal_state"])
    steps = []
    for i, state in enumerate(states):
        steps.append({
            "move": i,
            "action": state.action,
            "board": level.to_string(state)
        })

    return jsonify({
        "success": True,
        "solution_length": result["solution_length"],
        "states_explored": result["states_explored"],
        "steps": steps
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
