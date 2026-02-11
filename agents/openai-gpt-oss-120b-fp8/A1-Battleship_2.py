"""
Agent Code: A1-Battleship
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-11 19:24:56
"""

import itertools
from collections import deque

import itertools
from collections import deque

# -------------------------------------------------------------------------------
class BattleshipAgent:
    """
    Battleship agent with a simple but effective strategy:

    * Placement – tries random positions for each ship while respecting
      board bounds and avoiding overlaps.
    * Bombing   – classic Hunt‑Target approach.
        – Hunt   : fire on a checker‑board pattern (parity) to locate a ship.
        – Target : once a hit is obtained, enqueue the orthogonal neighbours
                  and continue until the ship is sunk, then return to Hunt.
    The agent also keeps a history of its own shots to avoid repeats.
    """

    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships                     # list of ship lengths (e.g. [5,4,3])

        # ---------- placement helpers ----------
        # our own board where we record our ships during placement
        self.my_board = [[ 'O' for _ in range(board_size)] for _ in range(board_size)]

        # ---------- bombing helpers ----------
        self.shots_taken = set()               # {(r,c), ...}
        self.hits = set()                      # successful hits not yet known to be sunk
        self.target_queue = deque()            # cells to try while we are in target mode
        self.parity = 0                        # 0 for (r+c) even, 1 for odd – we start with even

    # -----------------------------------------------------------------------
    # --------------------------- PLACEMENT ---------------------------------
    # -----------------------------------------------------------------------
    def _can_place(self, length, start, orientation):
        """Check whether a ship of given length can be placed at start."""
        r, c = start
        dr, dc = (0, 1) if orientation == 'horizontal' else (1, 0)

        for i in range(length):
            nr, nc = r + dr * i, c + dc * i
            if not (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                return False
            if self.my_board[nr][nc] == 'S':
                return False
        return True

    def _apply_placement(self, length, start, orientation):
        """Write the ship onto our internal board."""
        r, c = start
        dr, dc = (0, 1) if orientation == 'horizontal' else (1, 0)
        for i in range(length):
            self.my_board[r + dr * i][c + dc * i] = 'S'

    # -----------------------------------------------------------------------
    # ---------------------------- BOMBING ----------------------------------
    # -----------------------------------------------------------------------
    def _add_adjacent_targets(self, coord):
        """Enqueue orthogonal neighbours of a hit that are still unknown."""
        r, c = coord
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                if (nr, nc) not in self.shots_taken:
                    self.target_queue.append((nr, nc))

    def _choose_hunt_target(self):
        """Select a cell following a checker‑board pattern that hasn't been tried."""
        # Alternate parity each turn to keep coverage balanced
        for parity in (self.parity, 1-self.parity):
            candidates = [(r,c) for r in range(self.board_size)
                                 for c in range(self.board_size)
                                 if (r + c) % 2 == parity and (r,c) not in self.shots_taken]
            if candidates:
                self.parity = 1 - parity          # flip for next hunt round
                return random.choice(candidates)
        # Fallback – any remaining cell
        remaining = [(r,c) for r in range(self.board_size)
                           for c in range(self.board_size)
                           if (r,c) not in self.shots_taken]
        return random.choice(remaining) if remaining else (0,0)

    # -----------------------------------------------------------------------
    def make_move(self, state, feedback):
        """
        Dispatches to placement or bombing logic based on the current phase.
        """
        # -------------------------- PLACEMENT -----------------------------
        if state['phase'] == 'placement':
            ship_len = state['ships_to_place'][0]          # we must place the first pending ship

            # Try a few random positions; if all fail (very unlikely) fall back to deterministic scan
            for _ in range(100):
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    max_r = self.board_size - 1
                    max_c = self.board_size - ship_len
                else:
                    max_r = self.board_size - ship_len
                    max_c = self.board_size - 1

                start_r = random.randint(0, max_r)
                start_c = random.randint(0, max_c)

                if self._can_place(ship_len, (start_r, start_c), orientation):
                    self._apply_placement(ship_len, (start_r, start_c), orientation)
                    return {
                        'ship_length': ship_len,
                        'start': (start_r, start_c),
                        'orientation': orientation
                    }

            # Deterministic fallback (scan rows/cols)
            for orientation in ('horizontal', 'vertical'):
                for r in range(self.board_size):
                    for c in range(self.board_size):
                        if self._can_place(ship_len, (r, c), orientation):
                            self._apply_placement(ship_len, (r, c), orientation)
                            return {
                                'ship_length': ship_len,
                                'start': (r, c),
                                'orientation': orientation
                            }

            # Should never reach here; return a safe default
            return {
                'ship_length': ship_len,
                'start': (0, 0),
                'orientation': 'horizontal'
            }

        # --------------------------- BOMBING -------------------------------
        # Update internal state with the result of the previous shot (if any)
        last_coord = state.get('last_shot_coord')
        last_result = state.get('last_shot_result')

        if last_coord is not None:
            self.shots_taken.add(last_coord)
            if last_result == 'HIT':
                self.hits.add(last_coord)
                self._add_adjacent_targets(last_coord)

        # If we are currently in target mode (queue not empty), keep using it
        while self.target_queue:
            cand = self.target_queue.popleft()
            if cand not in self.shots_taken:
                return {'target': cand}

        # No pending targets → hunt mode
        hunt_target = self._choose_hunt_target()
        return {'target': hunt_target}
