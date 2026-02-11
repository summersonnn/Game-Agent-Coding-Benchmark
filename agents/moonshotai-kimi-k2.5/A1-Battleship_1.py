"""
Agent Code: A1-Battleship
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-11 19:24:56
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # Tracking for bombing phase
        self.shots = set()      # Coordinates already fired at
        self.hits = set()       # Coordinates that were hits
        self.targets = deque()  # Priority targets (adjacent to hits)
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Try random positions until finding a valid one
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
                coords = [(row, col + i) for i in range(ship_length)]
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
                coords = [(row + i, col) for i in range(ship_length)]
            
            # Check validity: all cells must be empty ('O')
            if all(my_board[r][c] == 'O' for r, c in coords):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Fallback (should rarely happen with valid board)
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }
    
    def _bomb(self, state):
        # Update knowledge based on previous shot result
        if state['last_shot_coord'] is not None:
            row, col = state['last_shot_coord']
            result = state['last_shot_result']
            
            self.shots.add((row, col))
            
            if result == 'HIT':
                self.hits.add((row, col))
                # Add adjacent cells to target queue for sinking the ship
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if (nr, nc) not in self.shots:
                            self.targets.append((nr, nc))
        
        # Select next target
        target = None
        
        # Priority: targets adjacent to existing hits (to finish sinking ships)
        while self.targets:
            candidate = self.targets.popleft()
            if candidate not in self.shots:
                target = candidate
                break
        
        # No priority targets: use checkerboard hunt pattern
        if target is None:
            for parity in [0, 1]:
                for r in range(self.board_size):
                    for c in range(self.board_size):
                        if (r + c) % 2 == parity and (r, c) not in self.shots:
                            target = (r, c)
                            break
                    if target:
                        break
                if target:
                    break
        
        return {'target': target}
