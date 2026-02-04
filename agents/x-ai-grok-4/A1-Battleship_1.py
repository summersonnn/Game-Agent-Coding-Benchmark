"""
Agent Code: A1-Battleship
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-04 17:06:44
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.guesses = [[' ' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.untried = set((r, c) for r in range(self.board_size) for c in range(self.board_size))
        self.hits = set()
        self.remaining_ships = list(self.ships_config)

    def is_open(self, r, c):
        if not (0 <= r < self.board_size and 0 <= c < self.board_size):
            return False
        return self.guesses[r][c] == ' '

    def get_chain(self, r, c, dr, dc):
        chain = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.guesses[nr][nc] == 'H':
            chain.append((nr, nc))
            nr += dr
            nc += dc
        return chain

    def check_for_sunk(self):
        sunk_coords = []
        to_sink = []
        visited = set()
        for hit in list(self.hits):
            if hit in visited:
                continue
            r, c = hit
            chain_h = self.get_chain(r, c, 0, 1) + self.get_chain(r, c, 0, -1) + [(r, c)]
            chain_h = list(set(chain_h))
            chain_v = self.get_chain(r, c, 1, 0) + self.get_chain(r, c, -1, 0) + [(r, c)]
            chain_v = list(set(chain_v))
            if len(chain_h) > len(chain_v):
                chain = chain_h
                orientation = 'h'
            elif len(chain_v) > 1:
                chain = chain_v
                orientation = 'v'
            else:
                chain = [(r, c)]
                orientation = None
            visited.update(chain)
            chain_len = len(chain)
            if chain_len == 1:
                closed = all(not self.is_open(r + dr, c + dc) for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)])
                if closed and chain_len in self.remaining_ships:
                    to_sink.append((chain, chain_len))
            else:
                closed = False
                if orientation == 'h':
                    chain.sort(key=lambda x: x[1])
                    leftmost = chain[0]
                    rightmost = chain[-1]
                    left_closed = not self.is_open(leftmost[0], leftmost[1] - 1)
                    right_closed = not self.is_open(rightmost[0], rightmost[1] + 1)
                    closed = left_closed and right_closed
                elif orientation == 'v':
                    chain.sort(key=lambda x: x[0])
                    topmost = chain[0]
                    bottommost = chain[-1]
                    top_closed = not self.is_open(topmost[0] - 1, topmost[1])
                    bottom_closed = not self.is_open(bottommost[0] + 1, bottommost[1])
                    closed = top_closed and bottom_closed
                if closed and chain_len in self.remaining_ships:
                    to_sink.append((chain, chain_len))
        for chain, length in to_sink:
            self.remaining_ships.remove(length)
            for pos in chain:
                pr, pc = pos
                self.guesses[pr][pc] = 'S'
                self.hits.discard(pos)
                sunk_coords.append(pos)
        return sunk_coords

    def get_unsunk_chains(self):
        chains = []
        visited = set()
        for hit in list(self.hits):
            if hit in visited:
                continue
            r, c = hit
            chain_h = self.get_chain(r, c, 0, 1) + self.get_chain(r, c, 0, -1) + [(r, c)]
            chain_h = list(set(chain_h))
            chain_v = self.get_chain(r, c, 1, 0) + self.get_chain(r, c, -1, 0) + [(r, c)]
            chain_v = list(set(chain_v))
            if len(chain_h) > len(chain_v):
                chain = chain_h
                orientation = 'h'
            elif len(chain_v) > 1:
                chain = chain_v
                orientation = 'v'
            else:
                chain = [(r, c)]
                orientation = None
            chains.append((chain, orientation))
            visited.update(chain)
        return chains

    def compute_target_probs(self):
        probs = [[0.0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        for chain, orientation in self.get_unsunk_chains():
            chain_len = len(chain)
            possible_lengths = [L for L in self.remaining_ships if L >= chain_len]
            for L in possible_lengths:
                if orientation == 'h' or orientation is None:
                    if chain_len > 1:
                        row = chain[0][0]
                        chain.sort(key=lambda p: p[1])
                        left_col = chain[0][1]
                        right_col = chain[-1][1]
                    else:
                        row = chain[0][0]
                        left_col = chain[0][1]
                        right_col = chain[0][1]
                    min_s = max(0, right_col - L + 1)
                    max_s = min(self.board_size - L, left_col)
                    for s in range(min_s, max_s + 1):
                        valid = True
                        for j in range(L):
                            nr, nc = row, s + j
                            g = self.guesses[nr][nc]
                            if g == 'M' or g == 'S':
                                valid = False
                                break
                            if g == 'H' and (nr, nc) not in set(chain):
                                valid = False
                                break
                        if valid:
                            for j in range(L):
                                nr, nc = row, s + j
                                if self.guesses[nr][nc] == ' ':
                                    probs[nr][nc] += 1
                if orientation == 'v' or orientation is None:
                    if chain_len > 1:
                        col = chain[0][1]
                        chain.sort(key=lambda p: p[0])
                        top_row = chain[0][0]
                        bot_row = chain[-1][0]
                    else:
                        col = chain[0][1]
                        top_row = chain[0][0]
                        bot_row = chain[0][0]
                    min_s = max(0, bot_row - L + 1)
                    max_s = min(self.board_size - L, top_row)
                    for s in range(min_s, max_s + 1):
                        valid = True
                        for j in range(L):
                            nr, nc = s + j, col
                            g = self.guesses[nr][nc]
                            if g == 'M' or g == 'S':
                                valid = False
                                break
                            if g == 'H' and (nr, nc) not in set(chain):
                                valid = False
                                break
                        if valid:
                            for j in range(L):
                                nr, nc = s + j, col
                                if self.guesses[nr][nc] == ' ':
                                    probs[nr][nc] += 1
        return probs

    def compute_hunt_probs(self):
        probs = [[0.0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        for length in self.remaining_ships:
            for r in range(self.board_size):
                # horizontal
                for s in range(self.board_size - length + 1):
                    if all(self.guesses[r][s + j] != 'M' and self.guesses[r][s + j] != 'S' for j in range(length)):
                        for j in range(length):
                            probs[r][s + j] += 1
                # vertical
                for s in range(self.board_size - length + 1):
                    if all(self.guesses[s + j][r] != 'M' and self.guesses[s + j][r] != 'S' for j in range(length)):
                        for j in range(length):
                            probs[s + j][r] += 1
        return probs

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        sunk_coords = []
        if last_shot_result is not None:
            r, c = last_shot_coord
            self.untried.discard((r, c))
            if last_shot_result == 'MISS':
                self.guesses[r][c] = 'M'
            elif last_shot_result == 'HIT':
                self.guesses[r][c] = 'H'
                self.hits.add((r, c))
            sunk_coords = self.check_for_sunk()

        pos = None
        if self.hits:
            probs = self.compute_target_probs()
            max_p = max(max(row) for row in probs) if any(any(row) for row in probs) else 0
            if max_p > 0:
                candidates = [(r, c) for r in range(self.board_size) for c in range(self.board_size)
                              if (r, c) in self.untried and probs[r][c] == max_p]
                if candidates:
                    pos = random.choice(candidates)

        if pos is None:
            probs = self.compute_hunt_probs()
            max_p = max(max(row) for row in probs) if any(any(row) for row in probs) else 0
            candidates = [(r, c) for r in range(self.board_size) for c in range(self.board_size)
                          if (r, c) in self.untried and probs[r][c] == max_p]
            if not candidates and self.untried:
                pos = random.choice(list(self.untried))
            elif candidates:
                pos = random.choice(candidates)

        return pos, sunk_coords
