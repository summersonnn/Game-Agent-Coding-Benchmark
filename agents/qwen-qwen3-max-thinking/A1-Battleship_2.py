"""
Agent Code: A1-Battleship
Model: qwen/qwen3-max-thinking
Run: 2
Generated: 2026-02-13 14:03:41
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # Bombing phase state
        self.opponent_grid = [[0] * board_size for _ in range(board_size)]  # 0=UNKNOWN, 1=MISS, 2=HIT
        self.target_queue = deque()
    
    def make_move(self, state, _):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            board = state['my_board']
            candidates = []
            
            # Generate all valid placements
            for row in range(self.board_size):
                for col in range(self.board_size):
                    # Check horizontal placement
                    if col + ship_length <= self.board_size:
                        valid = True
                        for c in range(col, col + ship_length):
                            if board[row][c] != 'O':
                                valid = False
                                break
                        if valid:
                            candidates.append({'start': (row, col), 'orientation': 'horizontal'})
                    # Check vertical placement
                    if row + ship_length <= self.board_size:
                        valid = True
                        for r in range(row, row + ship_length):
                            if board[r][col] != 'O':
                                valid = False
                                break
                        if valid:
                            candidates.append({'start': (row, col), 'orientation': 'vertical'})
            
            # Return random valid placement
            if candidates:
                choice = random.choice(candidates)
                return {
                    'ship_length': ship_length,
                    'start': choice['start'],
                    'orientation': choice['orientation']
                }
            
            # Fallback: return random placement (system will handle invalidity)
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
        
        else:  # Bombing phase
            # Update grid with last shot result
            if state['last_shot_coord'] is not None:
                r, c = state['last_shot_coord']
                if state['last_shot_result'] == 'HIT':
                    self.opponent_grid[r][c] = 2  # HIT
                    # Add adjacent cells to target queue
                    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            if self.opponent_grid[nr][nc] == 0:  # UNKNOWN
                                if (nr, nc) not in self.target_queue:
                                    self.target_queue.append((nr, nc))
                else:  # MISS
                    self.opponent_grid[r][c] = 1  # MISS
            
            # If current turn continues (after hit), use target queue
            if state['turn_continues']:
                while self.target_queue:
                    candidate = self.target_queue.popleft()
                    # Check if candidate is still valid
                    if self.opponent_grid[candidate[0]][candidate[1]] == 0:
                        return {'target': candidate}
                # Fallback to hunt mode if queue exhausted
                unknown_cells = [
                    (i, j) for i in range(self.board_size)
                    for j in range(self.board_size)
                    if self.opponent_grid[i][j] == 0
                ]
                return {'target': random.choice(unknown_cells)} if unknown_cells else {'target': (0, 0)}
            
            # Start of new turn (after miss or first move)
            self.target_queue.clear()
            unknown_cells = [
                (i, j) for i in range(self.board_size)
                for j in range(self.board_size)
                if self.opponent_grid[i][j] == 0
            ]
            return {'target': random.choice(unknown_cells)} if unknown_cells else {'target': (0, 0)}
