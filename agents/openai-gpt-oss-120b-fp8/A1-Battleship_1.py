"""
Agent Code: A1-Battleship
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-10 16:22:20
"""

from collections import deque

import random
from collections import deque

# The constants EMPTY, SHIP, HIT, MISS, SUNK are defined in the game module
# and are available in the same namespace when this class is used.

class BattleshipAgent:
    """
    Battleship agent with a simple but effective strategy:
    * Placement – tries random non‑overlapping positions until a valid one is found.
    * Bombing   – classic hunt/target approach.
        - Hunt mode uses a checker‑board pattern to reduce the search space.
        - When a HIT is recorded, adjacent cells are queued as target cells.
        - Targets are never repeated.
    """

    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships

        # ----- placement board (our own ships) -----
        self.my_board = [[EMPTY for _ in range(board_size)] for _ in range(board_size)]

        # ----- bombing state -----
        self.shots_taken = set()          # {(r,c), ...}
        self.hit_cells = set()            # cells that were hits
        self.target_queue = deque()       # cells to try next (target mode)

    # ----------------------------------------------------------------------
    # Placement helpers
    # ----------------------------------------------------------------------
    def _valid_placement(self, start, orientation, length):
        """Check that a ship of given length fits from start without overlapping."""
        r, c = start
        dr, dc = (0, 1) if orientation == "horizontal" else (1, 0)
        for i in range(length):
            nr, nc = r + dr * i, c + dc * i
            if self.my_board[nr][nc] == SHIP:
                return False
        return True

    def _place_ship(self, length):
        """Try random positions until a legal one is found (up to a limit)."""
        for _ in range(50):                     # reasonable number of attempts
            orientation = random.choice(["horizontal", "vertical"])
            if orientation == "horizontal":
                r = random.randint(0, self.board_size - 1)
                c = random.randint(0, self.board_size - length)
            else:
                r = random.randint(0, self.board_size - length)
                c = random.randint(0, self.board_size - 1)

            if self._valid_placement((r, c), orientation, length):
                # commit to our internal board representation
                dr, dc = (0, 1) if orientation == "horizontal" else (1, 0)
                for i in range(length):
                    self.my_board[r + dr * i][c + dc * i] = SHIP
                return {
                    "ship_length": length,
                    "start": (r, c),
                    "orientation": orientation,
                }

        # If we failed to find a non‑overlapping spot (unlikely), fall back to (0,0)
        return {
            "ship_length": length,
            "start": (0, 0),
            "orientation": "horizontal",
        }

    # ----------------------------------------------------------------------
    # Bombing helpers
    # ----------------------------------------------------------------------
    def _add_adjacent_targets(self, coord):
        """After a hit, enqueue the four orthogonal neighbours that are still unknown."""
        r, c = coord
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                if (nr, nc) not in self.shots_taken:
                    self.target_queue.append((nr, nc))

    def _choose_hunt_target(self):
        """Select a cell in hunt mode using a checker‑board pattern."""
        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) in self.shots_taken:
                    continue
                # Checker‑board (parity) – ships are at least length 2, so this halves the space
                if (r + c) % 2 == 0:
                    candidates.append((r, c))

        # If all parity cells are exhausted, fall back to any remaining cell
        if not candidates:
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if (r, c) not in self.shots_taken:
                        candidates.append((r, c))

        return random.choice(candidates)

    # ----------------------------------------------------------------------
    # Main interface
    # ----------------------------------------------------------------------
    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases.
        """
        # -------------------- Placement phase --------------------
        if state["phase"] == "placement":
            ship_len = state["ships_to_place"][0]          # always the first pending ship
            return self._place_ship(ship_len)

        # -------------------- Bombing phase --------------------
        # Update internal knowledge from the previous shot (if any)
        if state["last_shot_coord"] is not None:
            coord = tuple(state["last_shot_coord"])
            result = state["last_shot_result"]
            self.shots_taken.add(coord)

            if result == "HIT":
                self.hit_cells.add(coord)
                self._add_adjacent_targets(coord)
            # MISS does not require extra handling

        # Target mode: exhaust queued neighbours first
        while self.target_queue:
            cand = self.target_queue.popleft()
            if cand not in self.shots_taken:
                return {"target": cand}

        # Hunt mode: pick a new cell based on parity
        hunt_target = self._choose_hunt_target()
        return {"target": hunt_target}
