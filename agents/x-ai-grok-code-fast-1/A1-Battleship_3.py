"""
Agent Code: A1-Battleship
Model: x-ai/grok-code-fast-1
Run: 3
Generated: 2026-02-17 12:25:21
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.shots = set()  # Positions already shot
        self.hits = set()   # Positions that were hits
        self.possible = set((i, j) for i in range(board_size) for j in range(board_size))
        self.priority = deque()  # Queue for priority targets (adjacent to hits)

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            board = state['my_board']
            while True:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                    if all(board[row][c] == 'O' for c in range(col, col + ship_length)):
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                    if all(board[r][col] == 'O' for r in range(row, row + ship_length)):
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
        else:  # bombing phase
            # Update based on last shot
            if state['last_shot_coord'] is not None and state['last_shot_result'] == 'HIT':
                self.hits.add(state['last_shot_coord'])
                r, c = state['last_shot_coord']
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) in self.possible:
                        self.priority.append((nr, nc))

            # Choose target
            if self.priority:
                target = self.priority.popleft()
                while self.priority and target not in self.possible:
                    target = self.priority.popleft()
                if target not in self.possible:
                    target = random.choice(list(self.possible)) if self.possible else (0, 0)
            else:
                target = random.choice(list(self.possible)) if self.possible else (0, 0)

            self.possible.discard(target)
            self.shots.add(target)
            return {'target': target}
