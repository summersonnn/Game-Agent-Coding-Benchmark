"""
Agent Code: A1-Battleship
Model: x-ai/grok-4.1-fast
Run: 1
Generated: 2026-02-03 19:52:39
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.available = {(r, c) for r in range(board_size) for c in range(board_size)}
        self.open_hits = set()

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        # Process feedback from previous shot (only provided if it was a HIT)
        if last_shot_coord is not None:
            self.open_hits.add(last_shot_coord)

        # Get candidate positions: unshot cells adjacent to any open hit
        candidates = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for hr, hc in self.open_hits:
            for dr, dc in directions:
                nr, nc = hr + dr, hc + dc
                npos = (nr, nc)
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and npos in self.available:
                    candidates.add(npos)

        # Select best move
        if candidates:
            def score(pos):
                r, c = pos
                num_adj = sum(1 for h in self.open_hits if abs(h[0] - r) + abs(h[1] - c) == 1)
                space_score = min(r, self.board_size - 1 - r, c, self.board_size - 1 - c)
                return num_adj * 100 + space_score
            move = max(candidates, key=score)
        else:
            if not self.available:
                return None, []
            def hunt_score(pos):
                r, c = pos
                return min(r, self.board_size - 1 - r, c, self.board_size - 1 - c)
            move = max(self.available, key=hunt_score)

        # Remove the chosen position from available (shot regardless of outcome)
        self.available.discard(move)
        return move, []
