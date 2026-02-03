"""
Agent Code: A1-Battleship
Model: x-ai/grok-4.1-fast
Run: 3
Generated: 2026-02-03 20:03:51
"""

from collections import defaultdict

from collections import defaultdict
import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.fired = set()
        self.hits = set()
        self.hunt_candidates = set()
        self.available = {(r, c) for r in range(board_size) for c in range(board_size)}
        self.prob = self._compute_heatmap()
        self.dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def _compute_heatmap(self):
        prob = [[0.0] * self.board_size for _ in range(self.board_size)]
        for length in self.ships_config:
            num_placements = self.board_size * (self.board_size - length + 1)
            contrib_h = 1.0 / num_placements
            contrib_v = 1.0 / num_placements
            # horizontal
            for r in range(self.board_size):
                for sc in range(self.board_size - length + 1):
                    for i in range(length):
                        prob[r][sc + i] += contrib_h
            # vertical
            for c in range(self.board_size):
                for sr in range(self.board_size - length + 1):
                    for i in range(length):
                        prob[sr + i][c] += contrib_v
        return prob

    def hunt_score(self, pos):
        r, c = pos
        count = 0
        for dr, dc in self.dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) in self.hits:
                count += 1
        return count

    def _add_adj_hunt(self, hit_pos):
        r, c = hit_pos
        for dr, dc in self.dirs:
            nr, nc = r + dr, c + dc
            pos = (nr, nc)
            if (0 <= nr < self.board_size and 0 <= nc < self.board_size and
                pos not in self.fired and pos not in self.hunt_candidates):
                self.hunt_candidates.add(pos)

    def _get_next_shot(self):
        if self.hunt_candidates:
            shot = max(self.hunt_candidates, key=self.hunt_score)
            self.hunt_candidates.discard(shot)
            return shot
        if self.available:
            shot = max(self.available, key=lambda p: self.prob[p[0]][p[1]])
            return shot
        return None

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        if last_shot_coord is not None:
            pos = last_shot_coord
            self.fired.add(pos)
            self.available.discard(pos)
            if last_shot_result == 'HIT':
                self.hits.add(pos)
                self._add_adj_hunt(pos)
        shot = self._get_next_shot()
        return (shot, []) if shot is not None else (None, [])
