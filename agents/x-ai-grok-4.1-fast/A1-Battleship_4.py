"""
Agent Code: A1-Battleship
Model: x-ai/grok-4.1-fast
Run: 4
Generated: 2026-02-03 20:03:51
"""

from collections import deque

from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.available_shots = set((r, c) for r in range(board_size) for c in range(board_size))
        self.shots = set()
        self.hits = set()
        self.adjacent_pending = deque()
        self.pending_set = set()
        self.placements = {}
        self.surviving_placements = {}
        self._init_placements()

    def _init_placements(self):
        for length in self.ships_config:
            poss = []
            # horizontal
            for r in range(self.board_size):
                for c_start in range(self.board_size - length + 1):
                    ship_cells = [(r, c_start + i) for i in range(length)]
                    poss.append(ship_cells)
            # vertical
            for c in range(self.board_size):
                for r_start in range(self.board_size - length + 1):
                    ship_cells = [(r_start + i, c) for i in range(length)]
                    poss.append(ship_cells)
            self.placements[length] = poss
        self.surviving_placements = {
            l: set(range(len(self.placements[l]))) for l in self.ships_config
        }

    def _update_surviving(self):
        known_misses = self.shots - self.hits
        for l in self.ships_config:
            indices = self.surviving_placements[l]
            poss = self.placements[l]
            to_remove = set()
            for idx in indices:
                if any(cell in known_misses for cell in poss[idx]):
                    to_remove.add(idx)
            for idx in to_remove:
                indices.discard(idx)

    def _get_best_hunt(self):
        self._update_surviving()
        cell_scores = {}
        for l in self.ships_config:
            surv_indices = self.surviving_placements[l]
            poss = self.placements[l]
            for idx in surv_indices:
                for cell in poss[idx]:
                    if cell not in self.shots:
                        cell_scores[cell] = cell_scores.get(cell, 0) + 1
        if not cell_scores:
            return None
        max_score = max(cell_scores.values())
        candidates = [
            cell for cell, score in cell_scores.items()
            if score == max_score and cell in self.available_shots
        ]
        if candidates:
            return random.choice(candidates)
        return None

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        if last_shot_result == 'HIT' and last_shot_coord:
            self.hits.add(last_shot_coord)
            dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            r, c = last_shot_coord
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    cell = (nr, nc)
                    if cell in self.available_shots and cell not in self.pending_set:
                        self.adjacent_pending.append(cell)
                        self.pending_set.add(cell)

        # Clean pending
        while self.adjacent_pending and self.adjacent_pending[0] not in self.available_shots:
            gone = self.adjacent_pending.popleft()
            self.pending_set.remove(gone)

        # Choose shot
        if self.adjacent_pending:
            shot = self.adjacent_pending.popleft()
            self.pending_set.remove(shot)
        else:
            shot = self._get_best_hunt()
            if shot is None and self.available_shots:
                shot = random.choice(list(self.available_shots))

        if shot is None:
            return None, []

        self.shots.add(shot)
        self.available_shots.discard(shot)
        return shot, []
