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
        self.opponent_board = [['.' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.target_queue = deque()
        self.hunt_targets = [(i, j) for i in range(self.board_size) for j in range(self.board_size) if (i + j) % 2 == 0]
        random.shuffle(self.hunt_targets)

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            my_board = state['my_board']
            attempts = 0
            while attempts < 100:
                attempts += 1
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                    if all(my_board[row][col + i] == 'O' for i in range(ship_length)):
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                    if all(my_board[row + i][col] == 'O' for i in range(ship_length)):
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
            # Fallback to random if no valid found (unlikely)
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            return {
                'ship_length': ship_length,
                'start': (row, col),
                'orientation': orientation
            }
        else:  # bombing phase
            if state['last_shot_coord'] is not None:
                r, c = state['last_shot_coord']
                res = state['last_shot_result']
                self.opponent_board[r][c] = 'X' if res == 'HIT' else 'M'
                if res == 'HIT':
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.opponent_board[nr][nc] == '.':
                            self.target_queue.append((nr, nc))
            # Choose target
            while self.target_queue:
                target = self.target_queue.pop()  # Stack: focus on recent
                r, c = target
                if self.opponent_board[r][c] == '.':
                    return {'target': target}
            # Hunt mode
            while self.hunt_targets:
                target = self.hunt_targets.pop(0)
                r, c = target
                if self.opponent_board[r][c] == '.':
                    return {'target': target}
            # Fallback random
            unexplored = [(i, j) for i in range(self.board_size) for j in range(self.board_size) if self.opponent_board[i][j] == '.']
            if unexplored:
                return {'target': random.choice(unexplored)}
            # Should not reach here
            return {'target': (0, 0)}