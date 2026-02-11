"""
Agent Code: A1-Battleship
Model: x-ai-grok-4
Run: 2
Generated: 2026-02-11 19:37:45
"""

from collections import deque
import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.opponent_board = [['.' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.shots = set()
        self.target_queue = deque()
        self.remaining_ships = list(self.ships)

    def is_valid_placement(self, board, row, col, length, orientation):
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for c in range(col, col + length):
                if board[row][c] != 'O':
                    return False
        else:
            if row + length > self.board_size:
                return False
            for r in range(row, row + length):
                if board[r][col] != 'O':
                    return False
        return True

    def detect_sunk_ships(self):
        # Horizontal scans
        for r in range(self.board_size):
            c = 0
            while c < self.board_size:
                if self.opponent_board[r][c] == 'X':
                    start = c
                    while c < self.board_size and self.opponent_board[r][c] == 'X':
                        c += 1
                    length = c - start
                    left_bound = (start == 0 or self.opponent_board[r][start - 1] == 'M')
                    right_bound = (c == self.board_size or self.opponent_board[r][c] == 'M')
                    if left_bound and right_bound and length in self.remaining_ships:
                        self.remaining_ships.remove(length)
                        for j in range(start, c):
                            self.opponent_board[r][j] = '#'
                else:
                    c += 1

        # Vertical scans
        for c in range(self.board_size):
            r = 0
            while r < self.board_size:
                if self.opponent_board[r][c] == 'X':
                    start = r
                    while r < self.board_size and self.opponent_board[r][c] == 'X':
                        r += 1
                    length = r - start
                    top_bound = (start == 0 or self.opponent_board[start - 1][c] == 'M')
                    bottom_bound = (r == self.board_size or self.opponent_board[r][c] == 'M')
                    if top_bound and bottom_bound and length in self.remaining_ships:
                        self.remaining_ships.remove(length)
                        for j in range(start, r):
                            self.opponent_board[j][c] = '#'
                else:
                    r += 1

    def compute_prob(self):
        prob = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        for length in self.remaining_ships:
            # Horizontal
            for r in range(self.board_size):
                for start_c in range(self.board_size - length + 1):
                    can_place = all(self.opponent_board[r][c] not in ['M', '#'] for c in range(start_c, start_c + length))
                    if can_place:
                        for c in range(start_c, start_c + length):
                            prob[r][c] += 1
            # Vertical
            for c in range(self.board_size):
                for start_r in range(self.board_size - length + 1):
                    can_place = all(self.opponent_board[r][c] not in ['M', '#'] for r in range(start_r, start_r + length))
                    if can_place:
                        for r in range(start_r, start_r + length):
                            prob[r][c] += 1
        return prob

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            my_board = state['my_board']
            while True:
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
        else:  # bombing phase
            # Update board with new shots if any
            history_len = len(state['shot_history'])
            if history_len > len(self.shots):
                new_shots = state['shot_history'][len(self.shots):]
                for shot in new_shots:
                    row, col = shot['coord']
                    result = shot['result']
                    self.shots.add((row, col))
                    if result == 'HIT':
                        self.opponent_board[row][col] = 'X'
                    else:
                        self.opponent_board[row][col] = 'M'

            # Detect sunk ships
            self.detect_sunk_ships()

            # If last shot was a hit, add adjacent targets
            if state.get('last_shot_result') == 'HIT' and state.get('last_shot_coord') is not None:
                r, c = state['last_shot_coord']
                if self.opponent_board[r][c] == 'X':  # Not sunk
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.opponent_board[nr][nc] == '.':
                            self.target_queue.append((nr, nc))

            # Choose target
            # First, try target queue
            while self.target_queue:
                row, col = self.target_queue.popleft()
                if self.opponent_board[row][col] == '.':
                    return {'target': (row, col)}

            # Else, use probability for hunt mode
            prob = self.compute_prob()
            max_p = -1
            candidates = []
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self.opponent_board[r][c] == '.':
                        p = prob[r][c]
                        if p > max_p:
                            max_p = p
                            candidates = [(r, c)]
                        elif p == max_p:
                            candidates.append((r, c))

            if candidates:
                target = random.choice(candidates)
            else:
                # Should not happen, but fallback
                while True:
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - 1)
                    if self.opponent_board[row][col] == '.':
                        target = (row, col)
                        break

            return {'target': target}