"""
Agent Code: A1-Battleship
Model: openai/gpt-oss-120b@preset/fp8
Run: 3
Generated: 2026-02-03 19:52:39
"""

from collections import deque, defaultdict
import itertools

import random
from collections import deque, defaultdict
import itertools

class BattleshipAgent:
    """
    A simple yet effective Battleship AI.

    Strategy:
    1. Keep a set of all cells that have not been fired at yet.
    2. When a hit is scored, enqueue the orthogonal neighbours as high‑priority
       targets (hunt mode).
    3. If no hunt targets exist, use a probability heat‑map: for every possible
       placement of each ship length that does **not** overlap known misses,
       increment a counter for each cell of that placement.  The cell with the
       highest count (and still untried) is chosen.
    4. All fired cells (hit or miss) are removed from the untried set so they
       are never selected again.
    """

    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config

        # All coordinates that have not been fired at yet
        self.untried = {(r, c) for r in range(board_size) for c in range(board_size)}

        # Cells that resulted in a hit
        self.hit_cells = set()

        # Cells that resulted in a miss
        self.miss_cells = set()

        # Queue of high‑priority target cells (hunt mode)
        self.target_queue = deque()

        # Directions for neighbour generation
        self._dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    # --------------------------------------------------------------------- #
    # Helper methods
    # --------------------------------------------------------------------- #
    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _enqueue_neighbours(self, coord):
        """Add orthogonal neighbours of a hit cell to the target queue."""
        r, c = coord
        for dr, dc in self._dirs:
            nr, nc = r + dr, c + dc
            if self._in_bounds(nr, nc) and (nr, nc) in self.untried:
                self.target_queue.append((nr, nc))

    def _update_after_last_shot(self, result, coord):
        """Update internal bookkeeping based on the previous shot."""
        if coord is None:
            return

        # Remove the cell from the pool of possible moves
        self.untried.discard(coord)

        if result == 'HIT':
            self.hit_cells.add(coord)
            self._enqueue_neighbours(coord)
        else:  # MISS
            self.miss_cells.add(coord)

    def _probability_heatmap(self):
        """
        Build a heat‑map of how many ship placements cover each cell.
        Only placements that do not intersect known misses are considered.
        """
        heat = defaultdict(int)

        for length in self.ships_config:
            # Horizontal placements
            for r in range(self.board_size):
                for c in range(self.board_size - length + 1):
                    cells = [(r, c + i) for i in range(length)]
                    if any(cell in self.miss_cells for cell in cells):
                        continue
                    for cell in cells:
                        heat[cell] += 1

            # Vertical placements
            for c in range(self.board_size):
                for r in range(self.board_size - length + 1):
                    cells = [(r + i, c) for i in range(length)]
                    if any(cell in self.miss_cells for cell in cells):
                        continue
                    for cell in cells:
                        heat[cell] += 1

        return heat

    def _choose_via_heatmap(self):
        """Select the highest‑scoring cell from the heat‑map."""
        heat = self._probability_heatmap()
        if not heat:
            # Fallback – should never happen, but pick a random remaining cell
            return random.choice(list(self.untried))

        # Find the maximum heat value among still‑untried cells
        max_heat = -1
        best_cells = []
        for cell, score in heat.items():
            if cell not in self.untried:
                continue
            if score > max_heat:
                max_heat = score
                best_cells = [cell]
            elif score == max_heat:
                best_cells.append(cell)

        return random.choice(best_cells)

    # --------------------------------------------------------------------- #
    # Public API used by the game loop
    # --------------------------------------------------------------------- #
    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Returns ((row, col), sunk_coords)

        - (row, col): cell to bomb (0‑indexed)
        - sunk_coords: empty list (this agent does not explicitly report sunk ships)
        """
        # -----------------------------------------------------------------
        # 1. Update internal state from the previous shot
        # -----------------------------------------------------------------
        self._update_after_last_shot(last_shot_result, last_shot_coord)

        # -----------------------------------------------------------------
        # 2. If we are in “hunt” mode, pop the next target cell
        # -----------------------------------------------------------------
        while self.target_queue:
            cand = self.target_queue.popleft()
            if cand in self.untried:
                return cand, []

        # -----------------------------------------------------------------
        # 3. Otherwise, use the probability heat‑map to decide where to fire
        # -----------------------------------------------------------------
        next_move = self._choose_via_heatmap()
        return next_move, []
