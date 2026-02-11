"""
Agent Code: A1-Battleship
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-11 19:24:56
"""

from collections import deque

import random
from collections import deque

# Board symbols (imported from the game code)
EMPTY = 'O'
SHIP = 'S'

class BattleshipAgent:
    """
    Battleship agent with deterministic non‑overlapping placement and a
    classic Hunt‑Target bombing strategy.
    """

    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships

        # ----- placement helpers -----
        # our own board to guarantee valid placements
        self.my_board = [[EMPTY for _ in range(board_size)] for _ in range(board_size)]

        # ----- bombing helpers -----
        self.shots_taken = set()               # {(r,c), ...}
        self.hit_cells = set()                 # cells that were hits but not yet known sunk
        self.target_queue = deque()            # cells to fire at next (target mode)
        self.parity = 0                         # 0 for even cells, 1 for odd cells (checkerboard)

    # ----------------------------------------------------------------------
    # --------------------------- PLACEMENT ---------------------------------
    # ----------------------------------------------------------------------
    def _can_place(self, length, start, orientation):
        """Check if a ship of given length can be placed at start with orientation."""
        r, c = start
        if orientation == 'horizontal':
            if c + length > self.board_size:
                return False
            for cc in range(c, c + length):
                if self.my_board[r][cc] != EMPTY:
                    return False
        else:  # vertical
            if r + length > self.board_size:
                return False
            for rr in range(r, r + length):
                if self.my_board[rr][c] != EMPTY:
                    return False
        return True

    def _place_ship(self, length):
        """Find a valid placement; try random first, then deterministic scan."""
        # Try a few random attempts
        for _ in range(200):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                r = random.randint(0, self.board_size - 1)
                c = random.randint(0, self.board_size - length)
            else:
                r = random.randint(0, self.board_size - length)
                c = random.randint(0, self.board_size - 1)

            if self._can_place(length, (r, c), orientation):
                # mark board
                if orientation == 'horizontal':
                    for cc in range(c, c + length):
                        self.my_board[r][cc] = SHIP
                else:
                    for rr in range(r, r + length):
                        self.my_board[rr][c] = SHIP
                return {'ship_length': length,
                        'start': (r, c),
                        'orientation': orientation}

        # Deterministic fallback: scan rows/cols left‑to‑right, top‑to‑bottom
        for r in range(self.board_size):
            for c in range(self.board_size):
                for orientation in ('horizontal', 'vertical'):
                    if self._can_place(length, (r, c), orientation):
                        if orientation == 'horizontal':
                            for cc in range(c, c + length):
                                self.my_board[r][cc] = SHIP
                        else:
                            for rr in range(r, r + length):
                                self.my_board[rr][c] = SHIP
                        return {'ship_length': length,
                                'start': (r, c),
                                'orientation': orientation}
        # Should never happen
        raise RuntimeError("Unable to place ship of length {}".format(length))

    # ----------------------------------------------------------------------
    # ---------------------------- BOMBING ----------------------------------
    # ----------------------------------------------------------------------
    def _add_adjacent_targets(self, hit):
        """After a hit, enqueue orthogonal neighbours that are still unknown."""
        r, c = hit
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                if (nr, nc) not in self.shots_taken and (nr, nc) not in self.target_queue:
                    self.target_queue.append((nr, nc))

    def _choose_hunt_target(self):
        """
        Hunt mode: pick an untried cell respecting a checkerboard pattern.
        The smallest ship length is 3, so a 2‑cell parity is sufficient.
        """
        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r + c) % 2 == self.parity and (r, c) not in self.shots_taken:
                    candidates.append((r, c))
        if not candidates:  # board almost full, fall back to any free cell
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if (r, c) not in self.shots_taken:
                        candidates.append((r, c))
        return random.choice(candidates) if candidates else None

    # ----------------------------------------------------------------------
    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases.
        """
        # ------------------------------------------------------------------
        # Placement Phase
        # ------------------------------------------------------------------
        if state['phase'] == 'placement':
            ship_len = state['ships_to_place'][0]          # must place the first pending ship
            placement = self._place_ship(ship_len)
            return placement

        # ------------------------------------------------------------------
        # Bombing Phase
        # ------------------------------------------------------------------
        # Update internal knowledge from the previous shot (if any)
        last_result = state.get('last_shot_result')
        last_coord = state.get('last_shot_coord')

        if last_coord is not None:
            self.shots_taken.add(last_coord)
            if last_result == 'HIT':
                self.hit_cells.add(last_coord)
                self._add_adjacent_targets(last_coord)

        # If we have queued targets, use them first (target mode)
        while self.target_queue:
            cand = self.target_queue.popleft()
            if cand not in self.shots_taken:
                return {'target': cand}

        # Otherwise we are in hunt mode
        hunt_target = self._choose_hunt_target()
        if hunt_target is None:
            # safety net – pick any remaining cell
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if (r, c) not in self.shots_taken:
                        hunt_target = (r, c)
                        break
                if hunt_target:
                    break

        return {'target': hunt_target}
