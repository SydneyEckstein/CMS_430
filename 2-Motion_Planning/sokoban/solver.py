"""
Sokoban puzzle solver using A* search.

Sokoban level format:
    '#' - Wall
    ' ' - Empty floor
    '.' - Goal (empty)
    '$' - Box
    '@' - Player
    '*' - Box on goal
    '+' - Player on goal
"""

from queue import PriorityQueue


class Level:
    """
    Represents a Sokoban level's static elements.

    Attributes:
        walls: frozenset of (row, col) - wall positions
        goals: frozenset of (row, col) - goal positions
        width: int - level width
        height: int - level height
        initial_player: tuple (row, col) - starting player position
        initial_boxes: frozenset of (row, col) - starting box positions
    """

    def __init__(self, walls, goals, width, height, initial_player, initial_boxes):
        self.walls = frozenset(walls)
        self.goals = frozenset(goals)
        self.width = width
        self.height = height
        self.initial_player = initial_player
        self.initial_boxes = frozenset(initial_boxes)

    def create_initial_state(self):
        """Create the initial state for this level."""
        return SokobanState(
            self.initial_player,
            self.initial_boxes,
            self
        )

    @classmethod
    def from_string(cls, level_string):
        """
        Parse a level from standard Sokoban format.

        Returns:
            Level object
        """
        walls = set()
        goals = set()
        boxes = set()
        player = None

        lines = level_string.strip().split('\n')
        height = len(lines)
        width = max(len(line) for line in lines)

        for r, line in enumerate(lines):
            for c, char in enumerate(line):
                if char == '#':
                    walls.add((r, c))
                elif char == '.':
                    goals.add((r, c))
                elif char == '$':
                    boxes.add((r, c))
                elif char == '@':
                    player = (r, c)
                elif char == '*':  # Box on goal
                    boxes.add((r, c))
                    goals.add((r, c))
                elif char == '+':  # Player on goal
                    player = (r, c)
                    goals.add((r, c))

        if player is None:
            raise ValueError("Level must contain a player (@)")
        if len(boxes) == 0:
            raise ValueError("Level must contain at least one box ($)")
        if len(boxes) != len(goals):
            raise ValueError(f"Number of boxes ({len(boxes)}) must equal goals ({len(goals)})")

        return cls(walls, goals, width, height, player, boxes)

    def to_string(self, state=None):
        """
        Convert level to string representation.

        Args:
            state: Optional SokobanState to show current positions.
                   If None, shows initial configuration.
        """
        if state is None:
            player = self.initial_player
            boxes = self.initial_boxes
        else:
            player = state.player
            boxes = state.boxes

        lines = []
        for r in range(self.height):
            line = []
            for c in range(self.width):
                pos = (r, c)
                if pos in self.walls:
                    line.append('#')
                elif pos == player:
                    if pos in self.goals:
                        line.append('+')
                    else:
                        line.append('@')
                elif pos in boxes:
                    if pos in self.goals:
                        line.append('*')
                    else:
                        line.append('$')
                elif pos in self.goals:
                    line.append('.')
                else:
                    line.append(' ')
            lines.append(''.join(line))

        return '\n'.join(lines)


class SokobanState:
    """
    Immutable state representation for Sokoban puzzles.

    Attributes:
        player: tuple (row, col) - player position
        boxes: frozenset of (row, col) tuples - box positions
        level: Level object reference (walls, goals, dimensions)
        moves: int - number of moves from initial state (g-cost)
        parent: SokobanState or None - for path reconstruction
        action: str or None - action that led to this state ('U','D','L','R')
    """

    def __init__(self, player, boxes, level, moves=0, parent=None, action=None):
        self.player = player
        self.boxes = frozenset(boxes) if not isinstance(boxes, frozenset) else boxes
        self.level = level
        self.moves = moves
        self.parent = parent
        self.action = action

    def __hash__(self):
        """Hash based on player position and box positions only."""
        return hash((self.player, self.boxes))

    def __eq__(self, other):
        """Two states are equal if player and boxes are in same positions."""
        return self.player == other.player and self.boxes == other.boxes

    def __lt__(self, other):
        """Tie-breaking for priority queue."""
        return self.moves < other.moves

    def is_goal(self):
        """Check if all boxes are on goal positions."""
        return self.boxes == self.level.goals

    def heuristic(self):
        """
        Calculate h-cost using sum of minimum distances from each box to nearest goal.
        """
        total = 0
        for box in self.boxes:
            min_dist = min(
                abs(box[0] - goal[0]) + abs(box[1] - goal[1])
                for goal in self.level.goals
            )
            total += min_dist
        return total

    def generate_successors(self):
        """
        Generate all valid successor states.

        Move types:
        1. Walk: Player moves to empty floor (not wall, not box)
        2. Push: Player moves into box, box moves to empty space behind it
        """
        successors = []
        directions = {
            'U': (-1, 0),
            'D': (1, 0),
            'L': (0, -1),
            'R': (0, 1)
        }

        for action, (dr, dc) in directions.items():
            new_player = (self.player[0] + dr, self.player[1] + dc)

            # Check if new position is a wall
            if new_player in self.level.walls:
                continue

            # Check if new position has a box
            if new_player in self.boxes:
                # Try to push the box
                new_box_pos = (new_player[0] + dr, new_player[1] + dc)

                # Box can't be pushed into wall or another box
                if new_box_pos in self.level.walls:
                    continue
                if new_box_pos in self.boxes:
                    continue

                # Valid push - create new state with moved box
                new_boxes = (self.boxes - {new_player}) | {new_box_pos}

                new_state = SokobanState(
                    new_player, new_boxes, self.level,
                    self.moves + 1, self, action
                )

                # Skip if this creates a deadlock
                if not new_state.is_deadlocked():
                    successors.append(new_state)
            else:
                # Valid walk - no box in the way
                new_state = SokobanState(
                    new_player, self.boxes, self.level,
                    self.moves + 1, self, action
                )
                successors.append(new_state)

        return successors

    def is_deadlocked(self):
        """
        Check for simple deadlock conditions.

        Deadlock types detected:
        1. Corner deadlock: Box in corner that isn't a goal
        """
        for box in self.boxes:
            if box in self.level.goals:
                continue  # Box on goal is fine

            if self._is_corner_deadlock(box):
                return True

        return False

    def _is_corner_deadlock(self, box):
        """Check if box is stuck in a corner."""
        r, c = box
        walls = self.level.walls

        # Check all four corner configurations
        corners = [
            ((r-1, c), (r, c-1)),  # Top-left
            ((r-1, c), (r, c+1)),  # Top-right
            ((r+1, c), (r, c-1)),  # Bottom-left
            ((r+1, c), (r, c+1)),  # Bottom-right
        ]

        for adj1, adj2 in corners:
            if adj1 in walls and adj2 in walls:
                return True

        return False

    def get_solution_path(self):
        """
        Reconstruct the solution path from initial state to this state.

        Returns:
            List of action strings ['U', 'R', 'D', ...] from start to goal.
        """
        path = []
        state = self
        while state.parent is not None:
            path.append(state.action)
            state = state.parent
        return list(reversed(path))


def solve(level, max_states=100000):
    """
    Solve a Sokoban level using A* search.

    Args:
        level: Level object to solve
        max_states: Maximum states to explore before giving up

    Returns:
        dict with keys:
            'success': bool - whether solution was found
            'solution': list of action strings, or None
            'states_explored': int - number of states explored
            'solution_length': int - number of moves, or None
    """
    initial_state = level.create_initial_state()

    # Check if already solved
    if initial_state.is_goal():
        return {
            'success': True,
            'solution': [],
            'states_explored': 1,
            'solution_length': 0
        }

    # Priority queue: (f-cost, counter, state)
    # Counter ensures consistent ordering for equal priorities
    pq = PriorityQueue()
    counter = 0

    f_cost = initial_state.moves + initial_state.heuristic()
    pq.put((f_cost, counter, initial_state))
    counter += 1

    # Visited set - stores (player, boxes) tuples
    visited = {(initial_state.player, initial_state.boxes)}

    states_explored = 0

    while not pq.empty() and states_explored < max_states:
        _, _, current_state = pq.get()
        states_explored += 1

        # Check if this is the goal state
        if current_state.is_goal():
            return {
                'success': True,
                'solution': current_state.get_solution_path(),
                'states_explored': states_explored,
                'solution_length': current_state.moves
            }

        # Generate and process successors
        for successor in current_state.generate_successors():
            state_key = (successor.player, successor.boxes)

            if state_key not in visited:
                visited.add(state_key)
                f_cost = successor.moves + successor.heuristic()
                pq.put((f_cost, counter, successor))
                counter += 1

    return {
        'success': False,
        'solution': None,
        'states_explored': states_explored,
        'solution_length': None
    }


if __name__ == '__main__':
    # Simple test
    test_level = """
#####
#@$.#
#####
"""
    level = Level.from_string(test_level)
    print("Initial state:")
    print(level.to_string())
    print()

    result = solve(level)
    print(f"Solved: {result['success']}")
    print(f"Solution: {result['solution']}")
    print(f"States explored: {result['states_explored']}")
