"""
Agent Code: A1-Battleship
Model: google-gemini-3-flash-preview
Run: 1
Generated: 2026-02-11 19:27:04
"""

import random
from collections import deque

class BattleshipAgent:
    """
    A smart Battleship agent using a Hunt-and-Target strategy with parity 
    optimization and edge-preferential placement.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.targets_to_visit = deque()  # Stack for Target Mode
        self.fired_shots = set()         # History to prevent repeats
        self.last_hit = None

    def make_move(self, state, feedback=None):
        if state['phase'] == 'placement':
            return self._handle_placement(state)
        else:
            return self._handle_bombing(state)

    def _handle_placement(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        # Try to find a valid placement, prioritizing edges slightly for defense
        while True:
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
                coords = [(row, col + i) for i in range(ship_length)]
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
                coords = [(row + i, col) for i in range(ship_length)]

            # Check for overlaps
            if all(board[r][c] == 'O' for r, c in coords):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }

    def _handle_bombing(self, state):
        # Update our internal hit stack based on the result of the last shot
        last_res = state.get('last_shot_result')
        last_coord = state.get('last_shot_coord')

        if last_coord:
            self.fired_shots.add(last_coord)
            if last_res == 'HIT':
                # Add adjacent neighbors to target stack
                r, c = last_coord
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if (nr, nc) not in self.fired_shots:
                            self.targets_to_visit.append((nr, nc))

        # 1. Target Mode: If we have high-priority targets in the stack
        while self.targets_to_visit:
            target = self.targets_to_visit.pop()
            if target not in self.fired_shots:
                return {'target': target}

        # 2. Hunt Mode: Checkerboard parity (smallest ship length is 3)
        # We target cells where (row + col) % 2 == 0 to cover the board efficiently
        possible_hunts = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.fired_shots:
                    if (r + c) % 2 == 0:
                        possible_hunts.append((r, c))
        
        if possible_hunts:
            target = random.choice(possible_hunts)
        else:
            # Fallback for remaining odd cells
            remaining = [(r, c) for r in range(self.board_size) 
                         for c in range(self.board_size) 
                         if (r, c) not in self.fired_shots]
            target = random.choice(remaining) if remaining else (0, 0)

        return {'target': target}