"""
Agent Code: A1-Battleship
Model: x-ai/grok-4
Run: 3
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
        self.remaining = set((i, j) for i in range(board_size) for j in range(board_size))
        self.target_queue = []
        self.priority_targets = set()
        self.hit_positions = set()
        self.guess_board = [['O' for _ in range(board_size)] for _ in range(board_size)]
        self.remaining_ships = list(self.ships_config)
        # Hunt targets in checkerboard pattern
        self.hunt_list = []
        for r in range(board_size):
            for c in range(board_size):
                if (r + c) % 2 == 0:
                    self.hunt_list.append((r, c))
        random.shuffle(self.hunt_list)
        self.hunt_list2 = []
        for r in range(board_size):
            for c in range(board_size):
                if (r + c) % 2 == 1:
                    self.hunt_list2.append((r, c))
        random.shuffle(self.hunt_list2)
        self.hunt_list += self.hunt_list2
        self.hunt_index = 0

    def find_sunk_ships(self):
        sunk = []
        # Horizontal
        for r in range(self.board_size):
            c = 0
            while c < self.board_size:
                if self.guess_board[r][c] == 'X':
                    start = c
                    while c < self.board_size and self.guess_board[r][c] == 'X':
                        c += 1
                    end = c - 1
                    L = end - start + 1
                    left_ok = (start == 0 or self.guess_board[r][start - 1] in ('M', '#'))
                    right_ok = (end == self.board_size - 1 or self.guess_board[r][end + 1] in ('M', '#'))
                    if left_ok and right_ok and L >= 3:
                        coords = [(r, start + i) for i in range(L)]
                        if L in self.remaining_ships:
                            sunk.extend(coords)
                            self.remaining_ships.remove(L)
                        elif L == 7 and 3 in self.remaining_ships and 4 in self.remaining_ships:
                            sunk.extend(coords)
                            self.remaining_ships.remove(3)
                            self.remaining_ships.remove(4)
                        elif L == 8 and 3 in self.remaining_ships and 5 in self.remaining_ships:
                            sunk.extend(coords)
                            self.remaining_ships.remove(3)
                            self.remaining_ships.remove(5)
                else:
                    c += 1
        # Vertical
        for c in range(self.board_size):
            r = 0
            while r < self.board_size:
                if self.guess_board[r][c] == 'X':
                    start = r
                    while r < self.board_size and self.guess_board[r][c] == 'X':
                        r += 1
                    end = r - 1
                    L = end - start + 1
                    top_ok = (start == 0 or self.guess_board[start - 1][c] in ('M', '#'))
                    bottom_ok = (end == self.board_size - 1 or self.guess_board[end + 1][c] in ('M', '#'))
                    if top_ok and bottom_ok and L >= 3:
                        coords = [(start + i, c) for i in range(L)]
                        if L in self.remaining_ships:
                            sunk.extend(coords)
                            self.remaining_ships.remove(L)
                        elif L == 7 and 3 in self.remaining_ships and 4 in self.remaining_ships:
                            sunk.extend(coords)
                            self.remaining_ships.remove(3)
                            self.remaining_ships.remove(4)
                        elif L == 8 and 3 in self.remaining_ships and 5 in self.remaining_ships:
                            sunk.extend(coords)
                            self.remaining_ships.remove(3)
                            self.remaining_ships.remove(5)
                else:
                    r += 1
        return sunk

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        sunk_coords = []
        if last_shot_result is not None:
            r, c = last_shot_coord
            self.remaining.discard((r, c))
            if last_shot_result == 'HIT':
                self.guess_board[r][c] = 'X'
                self.hit_positions.add((r, c))
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    target = (nr, nc)
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size and target in self.remaining and target not in self.priority_targets:
                        self.target_queue.append(target)
                        self.priority_targets.add(target)
            else:
                self.guess_board[r][c] = 'M'
            sunk_coords = self.find_sunk_ships()
            for pos in sunk_coords:
                pr, pc = pos
                self.guess_board[pr][pc] = '#'
                self.hit_positions.discard(pos)
        # Target mode
        while self.target_queue:
            candidate = self.target_queue.pop()
            self.priority_targets.discard(candidate)
            if candidate in self.remaining:
                return candidate, sunk_coords
        # Hunt mode
        while self.hunt_index < len(self.hunt_list):
            candidate = self.hunt_list[self.hunt_index]
            self.hunt_index += 1
            if candidate in self.remaining:
                return candidate, sunk_coords
        # Fallback if exhausted
        if not self.remaining:
            return None, sunk_coords
        move = random.choice(list(self.remaining))
        return move, sunk_coords
