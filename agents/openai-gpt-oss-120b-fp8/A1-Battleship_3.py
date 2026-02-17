"""
Agent Code: A1-Battleship
Model: openai/gpt-oss-120b@preset/fp8
Run: 3
Generated: 2026-02-17 12:25:21
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    A simple yet effective Battleship agent.

    - Placement: deterministic scan for the first fitting position (longest ships first).
    - Bombing: parity‑based hunting combined with a target queue that expands
      around successful hits (classic hunt‑/target strategy).
    """

    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)          # longest first

        # --- Bombing state ---
        self.mode = "hunt"                                 # 'hunt' or 'target'
        self.target_queue = deque()                       # cells to try after a hit
        self.target_set = set()                           # for fast duplicate checks
        self.hunt_cells = self._init_hunt_cells()
        self.hunt_index = 0                               # next cell in hunt list

    # ----------------------------------------------------------------------
    # Placement helpers
    # ----------------------------------------------------------------------
    def _can_place(self, board, length, r, c, orient):
        """Check if a ship of given length fits at (r,c) with orientation."""
        if orient == "horizontal":
            if c + length > self.board_size:
                return False
            for cc in range(c, c + length):
                if board[r][cc] != 'O':
                    return False
        else:  # vertical
            if r + length > self.board_size:
                return False
            for rr in range(r, r + length):
                if board[rr][c] != 'O':
                    return False
        return True

    def _place_ship(self, state):
        """Find the first valid position for the next ship to place."""
        length = state["ships_to_place"][0]
        board = state["my_board"]

        for r in range(self.board_size):
            for c in range(self.board_size):
                for orient in ("horizontal", "vertical"):
                    if self._can_place(board, length, r, c, orient):
                        return {
                            "ship_length": length,
                            "start": (r, c),
                            "orientation": orient,
                        }
        # Fallback (should never happen): random valid placement
        orientation = random.choice(["horizontal", "vertical"])
        if orientation == "horizontal":
            r = random.randint(0, self.board_size - 1)
            c = random.randint(0, self.board_size - length)
        else:
            r = random.randint(0, self.board_size - length)
            c = random.randint(0, self.board_size - 1)
        return {
            "ship_length": length,
            "start": (r, c),
            "orientation": orientation,
        }

    # ----------------------------------------------------------------------
    # Bombing helpers
    # ----------------------------------------------------------------------
    def _init_hunt_cells(self):
        """
        Generate a shuffled list of cells following a checkerboard pattern.
        Using parity reduces the number of shots needed for ships of length ≥ 2.
        """
        cells = [
            (r, c)
            for r in range(self.board_size)
            for c in range(self.board_size)
            if (r + c) % 2 == 0
        ]
        random.shuffle(cells)
        return cells

    def _add_adjacent_targets(self, hit_coord, shot_set):
        """Enqueue orthogonal neighbours of a hit that have not been shot yet."""
        r, c = hit_coord
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                if (nr, nc) not in shot_set and (nr, nc) not in self.target_set:
                    self.target_queue.append((nr, nc))
                    self.target_set.add((nr, nc))

    # ----------------------------------------------------------------------
    # Main entry point
    # ----------------------------------------------------------------------
    def make_move(self, state, feedback):
        # ------------------------------------------------------------------
        # Placement phase
        # ------------------------------------------------------------------
        if state["phase"] == "placement":
            return self._place_ship(state)

        # ------------------------------------------------------------------
        # Bombing phase
        # ------------------------------------------------------------------
        # Build a set of all previously tried coordinates for fast lookup
        shot_set = {entry["coord"] for entry in state["shot_history"]}

        # Update targeting information based on the result of the previous shot
        last_coord = state.get("last_shot_coord")
        last_result = state.get("last_shot_result")
        if last_coord is not None and last_result == "HIT":
            # Switch to target mode and enqueue neighbours
            self.mode = "target"
            self._add_adjacent_targets(last_coord, shot_set)

        # --------------------------------------------------------------
        # Choose next target
        # --------------------------------------------------------------
        # 1. If we have pending target cells, use them (target mode)
        while self.target_queue:
            cand = self.target_queue.popleft()
            self.target_set.discard(cand)
            if cand not in shot_set:
                return {"target": cand}

        # 2. No pending targets → hunt mode
        self.mode = "hunt"
        # Scan through the pre‑computed hunt list
        while self.hunt_index < len(self.hunt_cells):
            cand = self.hunt_cells[self.hunt_index]
            self.hunt_index += 1
            if cand not in shot_set:
                return {"target": cand}

        # 3. Exhausted parity cells – fall back to any remaining cell
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in shot_set:
                    return {"target": (r, c)}

        # Should never reach here; return a random valid cell as a safety net
        while True:
            r = random.randint(0, self.board_size - 1)
            c = random.randint(0, self.board_size - 1)
            if (r, c) not in shot_set:
                return {"target": (r, c)}
