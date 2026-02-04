"""
Agent Code: A1-Battleship
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-04 17:06:44
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.size = board_size
        self.remaining_ships = sorted(ships_config, reverse=True)
        self.guess_board = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.possible_targets = set((r, c) for r in range(self.size) for c in range(self.size))

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        if last_shot_result is not None and last_shot_coord is not None:
            r, c = last_shot_coord
            if last_shot_result == 'MISS':
                self.guess_board[r][c] = 'M'
            elif last_shot_result == 'HIT':
                self.guess_board[r][c] = 'X'
            self.possible_targets.discard((r, c))

        sunk_coords = self.detect_sunk()

        if not self.possible_targets:
            return None, sunk_coords

        next_shot = self.choose_next_shot()
        return next_shot, sunk_coords

    def detect_sunk(self):
        sunk_coords = []
        while True:
            lines = self.find_isolated_lines()
            found = False
            for line in lines:
                L = len(line)
                subset = self.find_subset_summing_to(L)
                if subset:
                    for cell in line:
                        r, c = cell
                        self.guess_board[r][c] = '#'
                    sunk_coords.extend(line)
                    for s in subset:
                        self.remaining_ships.remove(s)
                    found = True
                    break
            if not found:
                break
        return sunk_coords

    def find_isolated_lines(self):
        lines = []
        # Horizontal
        for r in range(self.size):
            c = 0
            while c < self.size:
                if self.guess_board[r][c] == 'X':
                    start = c
                    while c < self.size and self.guess_board[r][c] == 'X':
                        c += 1
                    end = c - 1
                    L = end - start + 1
                    left_blocked = (start == 0) or self.guess_board[r][start - 1] in {'M', '#'}
                    right_blocked = (end == self.size - 1) or self.guess_board[r][end + 1] in {'M', '#'}
                    if left_blocked and right_blocked:
                        lines.append([(r, k) for k in range(start, end + 1)])
                else:
                    c += 1
        # Vertical
        for col in range(self.size):
            r = 0
            while r < self.size:
                if self.guess_board[r][col] == 'X':
                    start = r
                    while r < self.size and self.guess_board[r][col] == 'X':
                        r += 1
                    end = r - 1
                    L = end - start + 1
                    top_blocked = (start == 0) or self.guess_board[start - 1][col] in {'M', '#'}
                    bottom_blocked = (end == self.size - 1) or self.guess_board[end + 1][col] in {'M', '#'}
                    if top_blocked and bottom_blocked:
                        lines.append([(k, col) for k in range(start, end + 1)])
                else:
                    r += 1
        return lines

    def find_subset_summing_to(self, target):
        rem = set(self.remaining_ships)
        if target in rem:
            return [target]
        for a in rem:
            for b in rem - {a}:
                if a + b == target:
                    return [a, b]
        if len(rem) == 3 and sum(rem) == target:
            return list(rem)
        return []

    def get_possible_positions(self, length):
        positions = []
        # Horizontal
        for r in range(self.size):
            for start in range(self.size - length + 1):
                valid = True
                coords = []
                for i in range(length):
                    cc = start + i
                    if self.guess_board[r][cc] not in {' ', 'X'}:
                        valid = False
                        break
                    coords.append((r, cc))
                if valid:
                    positions.append(coords)
        # Vertical
        for c in range(self.size):
            for start in range(self.size - length + 1):
                valid = True
                coords = []
                for i in range(length):
                    rr = start + i
                    if self.guess_board[rr][c] not in {' ', 'X'}:
                        valid = False
                        break
                    coords.append((rr, c))
                if valid:
                    positions.append(coords)
        return positions

    def choose_next_shot(self):
        cell_hits = {}
        total_valid = [0]
        all_x = set((r, c) for r in range(self.size) for c in range(self.size) if self.guess_board[r][c] == 'X')

        def recurse(ship_index, placed_so_far):
            if ship_index == len(self.remaining_ships):
                covered = set()
                for pos in placed_so_far:
                    for cell in pos:
                        covered.add(cell)
                if covered == all_x:
                    total_valid[0] += 1
                    for pos in placed_so_far:
                        for cell in pos:
                            if self.guess_board[cell[0]][cell[1]] == ' ':
                                cell_hits[cell] = cell_hits.get(cell, 0) + 1
                return
            len_ = self.remaining_ships[ship_index]
            possible_pos = self.get_possible_positions(len_)
            for pos in possible_pos:
                pos_set = set(pos)
                if any(pos_set & set(p) for p in placed_so_far):
                    continue
                recurse(ship_index + 1, placed_so_far + [pos])

        recurse(0, [])

        if total_valid[0] == 0:
            return random.choice(list(self.possible_targets))

        max_prob = -1
        candidates = []
        for cell in self.possible_targets:
            hits = cell_hits.get(cell, 0)
            prob = hits / total_valid[0] if total_valid[0] > 0 else 0
            if prob > max_prob:
                max_prob = prob
                candidates = [cell]
            elif prob == max_prob:
                candidates.append(cell)

        if not candidates:
            return random.choice(list(self.possible_targets))

        return random.choice(candidates)
