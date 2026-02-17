"""
Agent Code: A1-Battleship
Model: x-ai-grok-4
Run: 1
Generated: 2026-02-11 19:37:45
"""

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.opponent_board = [[' ' for _ in range(board_size)] for _ in range(board_size)]
        self.target_stack = []
        self.remaining_ships = list(ships)

    def is_valid_placement(self, board, row, col, length, orientation):
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for i in range(length):
                if board[row][col + i] != 'O':
                    return False
        else:
            if row + length > self.board_size:
                return False
            for i in range(length):
                if board[row + i][col] != 'O':
                    return False
        return True

    def detect_sunks(self):
        board = self.opponent_board
        size = self.board_size
        # Horizontal scans
        for r in range(size):
            c = 0
            while c < size:
                if board[r][c] == 'X' and (c == 0 or board[r][c-1] != 'X'):
                    start = c
                    end = start
                    while end < size - 1 and board[r][end+1] == 'X':
                        end += 1
                    length = end - start + 1
                    left_blocked = start == 0 or board[r][start-1] != ' '
                    right_blocked = end == size - 1 or board[r][end+1] != ' '
                    if left_blocked and right_blocked and length in self.remaining_ships:
                        self.remaining_ships.remove(length)
                        for cc in range(start, end + 1):
                            board[r][cc] = '#'
                    c = end
                c += 1
        # Vertical scans
        for c in range(size):
            r = 0
            while r < size:
                if board[r][c] == 'X' and (r == 0 or board[r-1][c] != 'X'):
                    start = r
                    end = start
                    while end < size - 1 and board[end+1][c] == 'X':
                        end += 1
                    length = end - start + 1
                    top_blocked = start == 0 or board[start-1][c] != ' '
                    bottom_blocked = end == size - 1 or board[end+1][c] != ' '
                    if top_blocked and bottom_blocked and length in self.remaining_ships:
                        self.remaining_ships.remove(length)
                        for rr in range(start, end + 1):
                            board[rr][c] = '#'
                    r = end
                r += 1

    def calculate_probs(self):
        probs = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        for ship_len in self.remaining_ships:
            # Horizontal
            for r in range(self.board_size):
                for start_c in range(self.board_size - ship_len + 1):
                    valid = True
                    for i in range(ship_len):
                        if self.opponent_board[r][start_c + i] != ' ':
                            valid = False
                            break
                    if valid:
                        for i in range(ship_len):
                            probs[r][start_c + i] += 1
            # Vertical
            for c in range(self.board_size):
                for start_r in range(self.board_size - ship_len + 1):
                    valid = True
                    for i in range(ship_len):
                        if self.opponent_board[start_r + i][c] != ' ':
                            valid = False
                            break
                    if valid:
                        for i in range(ship_len):
                            probs[start_r + i][c] += 1
        return probs

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            my_board = state['my_board']
            for _ in range(100):
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                if self.is_valid_placement(my_board, row, col, ship_length, orientation):
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': orientation
                    }
            # Fallback (should not reach)
            raise ValueError("Could not find valid placement")
        else:  # bombing
            # Update from last shot
            if state['last_shot_coord'] is not None:
                row, col = state['last_shot_coord']
                result = state['last_shot_result']
                self.opponent_board[row][col] = 'X' if result == 'HIT' else 'M'
                if result == 'HIT':
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        r, c = row + dr, col + dc
                        if 0 <= r < self.board_size and 0 <= c < self.board_size and self.opponent_board[r][c] == ' ':
                            self.target_stack.append((r, c))
            # Detect sunks
            self.detect_sunks()
            # Choose target
            while self.target_stack:
                target = self.target_stack.pop()
                if self.opponent_board[target[0]][target[1]] == ' ':
                    return {'target': target}
            # Hunt mode with probs
            probs = self.calculate_probs()
            unknown = [(i, j) for i in range(self.board_size) for j in range(self.board_size) if self.opponent_board[i][j] == ' ']
            if not unknown:
                raise ValueError("No moves left")
            max_prob = max(probs[i][j] for i, j in unknown)
            candidates = [(i, j) for i, j in unknown if probs[i][j] == max_prob]
            target = random.choice(candidates)
            return {'target': target}