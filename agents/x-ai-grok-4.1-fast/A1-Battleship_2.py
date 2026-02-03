"""
Agent Code: A1-Battleship
Model: x-ai/grok-4.1-fast
Run: 2
Generated: 2026-02-03 19:52:39
"""

from collections import deque

from collections import deque
import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.sizes = ships_config
        self.num_ship_types = len(self.sizes)
        self.dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        self.guess_board = [['.' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.available_moves = set((r, c) for r in range(self.board_size) for c in range(self.board_size))
        
        # Precompute placements and cover counts
        self.active_placements = [[] for _ in range(self.num_ship_types)]
        self.ship_cover = [[[0 for _ in range(self.board_size)] for _ in range(self.board_size)] 
                          for _ in range(self.num_ship_types)]
        self.ship_total = [0 for _ in range(self.num_ship_types)]
        
        for si, L in enumerate(self.sizes):
            # Horizontal placements
            for r in range(self.board_size):
                for c in range(self.board_size - L + 1):
                    placement = (r, c, 0)  # H
                    self.active_placements[si].append(placement)
                    for j in range(L):
                        self.ship_cover[si][r][c + j] += 1
            # Vertical placements
            for c in range(self.board_size):
                for r in range(self.board_size - L + 1):
                    placement = (r, c, 1)  # V
                    self.active_placements[si].append(placement)
                    for i in range(L):
                        self.ship_cover[si][r + i][c] += 1
            self.ship_total[si] = len(self.active_placements[si])

    def covers(self, placement, row, col, ship_idx):
        sr, sc, direction = placement
        length = self.sizes[ship_idx]
        if direction == 0:  # horizontal
            return sr == row and sc <= col < sc + length
        else:  # vertical
            return sc == col and sr <= row < sr + length

    def is_adjacent_to_hit(self, r, c):
        for dr, dc in self.dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.guess_board[nr][nc] == 'H':
                return True
        return False

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        if last_shot_result is not None and last_shot_coord is not None:
            rr, cc = last_shot_coord
            if last_shot_result == 'HIT':
                self.guess_board[rr][cc] = 'H'
            elif last_shot_result == 'MISS':
                self.guess_board[rr][cc] = 'M'
                # Prune placements that cover this miss
                for si in range(self.num_ship_types):
                    to_remove = []
                    for pidx in range(len(self.active_placements[si])):
                        if self.covers(self.active_placements[si][pidx], rr, cc, si):
                            to_remove.append(pidx)
                    for pidx in sorted(to_remove, reverse=True):
                        placement = self.active_placements[si].pop(pidx)
                        pr, pc, pd = placement
                        L = self.sizes[si]
                        if pd == 0:
                            for j in range(L):
                                self.ship_cover[si][pr][pc + j] -= 1
                        else:
                            for i in range(L):
                                self.ship_cover[si][pr + i][pc] -= 1
                    self.ship_total[si] = len(self.active_placements[si])

        if not self.available_moves:
            return None, []

        # Find best shot
        best_score = -1.0
        best_shots = []
        for pos in list(self.available_moves):
            r, c = pos
            prob = sum(
                self.ship_cover[si][r][c] / max(1.0, self.ship_total[si])
                for si in range(self.num_ship_types)
            )
            score = prob
            if self.is_adjacent_to_hit(r, c):
                score += 1000.0
            if score > best_score:
                best_score = score
                best_shots = [pos]
            elif abs(score - best_score) < 1e-9:
                best_shots.append(pos)

        if not best_shots:
            return None, []

        shot = random.choice(best_shots)
        self.available_moves.remove(shot)
        return shot, []
