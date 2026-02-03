"""
Agent Code: A1-Battleship
Model: openai/gpt-oss-120b@preset/fp8
Run: 4
Generated: 2026-02-03 19:52:39
"""

import itertools
from collections import defaultdict

import itertools
from collections import defaultdict

class BattleshipAgent:
    """
    A probability‑based Battleship agent.

    Strategy
    --------
    * Keep track of all shots that have been fired, hits and misses.
    * Pre‑compute every possible placement for each ship length.
    * On every turn generate a heat‑map: for every still‑possible ship
      placement (i.e. placements that do **not** intersect a known miss)
      add 1 to each cell of that placement that has not been shot yet.
    * Choose the untried cell with the highest heat value.
    * After each shot update the internal knowledge base.
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config

        # knowledge base
        self.shots_fired = set()          # all coordinates we have already bombed
        self.hits = set()                 # coordinates that were hits
        self.misses = set()               # coordinates that were misses

        # pre‑compute every placement for each ship length
        # self.placements_by_len[length] = list of tuple‑of‑cells
        self.placements_by_len = {}
        for length in self.ships_config:
            self.placements_by_len[length] = self._all_placements(length)

    # ------------------------------------------------------------------ #
    def _all_placements(self, length):
        """Return a list of all horizontal and vertical placements of a ship
        of the given length on the board. Each placement is a tuple of
        (row, col) coordinates."""
        placements = []

        # horizontal placements
        for r in range(self.board_size):
            for c in range(self.board_size - length + 1):
                cells = tuple((r, c + i) for i in range(length))
                placements.append(cells)

        # vertical placements
        for c in range(self.board_size):
            for r in range(self.board_size - length + 1):
                cells = tuple((r + i, c) for i in range(length))
                placements.append(cells)

        return placements

    # ------------------------------------------------------------------ #
    def _update_knowledge(self, last_result, last_coord):
        """Record the outcome of the previous shot."""
        if last_coord is None:
            return
        self.shots_fired.add(last_coord)
        if last_result == 'HIT':
            self.hits.add(last_coord)
        else:  # MISS or any other token
            self.misses.add(last_coord)

    # ------------------------------------------------------------------ #
    def _build_heat_map(self):
        """Create a heat‑map counting how many still‑possible ship placements
        cover each cell that has not been shot yet."""
        heat = [[0] * self.board_size for _ in range(self.board_size)]

        for length, placements in self.placements_by_len.items():
            for placement in placements:
                # a placement is impossible if it touches a known miss
                if any(cell in self.misses for cell in placement):
                    continue
                # otherwise, every untried cell in this placement gets a vote
                for (r, c) in placement:
                    if (r, c) not in self.shots_fired:
                        heat[r][c] += 1
        return heat

    # ------------------------------------------------------------------ #
    def _choose_best_cell(self, heat):
        """Select the untried cell with the highest heat value. If several
        cells tie, pick one at random."""
        max_heat = -1
        best_cells = []

        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) in self.shots_fired:
                    continue
                val = heat[r][c]
                if val > max_heat:
                    max_heat = val
                    best_cells = [(r, c)]
                elif val == max_heat:
                    best_cells.append((r, c))

        # If every cell has heat 0 (should not normally happen), fall back
        # to a random untried cell.
        if not best_cells:
            remaining = [
                (r, c)
                for r in range(self.board_size)
                for c in range(self.board_size)
                if (r, c) not in self.shots_fired
            ]
            return random.choice(remaining) if remaining else None

        return random.choice(best_cells)

    # ------------------------------------------------------------------ #
    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Return a tuple: ((row, col), sunk_coords)

        - (row, col): cell to bomb (0‑indexed)
        - sunk_coords: list of coordinates of a ship we have just sunk
                       (not used in this simple implementation)

        ``last_shot_result`` is either 'HIT' or 'MISS' (or None on the first turn)
        ``last_shot_coord`` is the coordinate of that previous shot.
        """
        # 1. Update internal knowledge with the outcome of the previous move.
        self._update_knowledge(last_shot_result, last_shot_coord)

        # 2. Build a probability heat‑map from all still‑possible placements.
        heat = self._build_heat_map()

        # 3. Choose the best cell according to the heat‑map.
        move = self._choose_best_cell(heat)

        # If for any reason we couldn't find a move (board full), signal end.
        if move is None:
            return None, []

        # No sunk‑detection logic – we just return an empty list.
        return move, []
