"""
Agent Code: A1-Battleship
Model: qwen/qwen3-coder@preset/fp8
Run: 1
Generated: 2026-02-11 19:37:45
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.enemy_board = [[None for _ in range(board_size)] for _ in range(board_size)]  # Tracks hits/misses
        self.remaining_ships = ships[:]
        self.last_hit = None
        self.potential_targets = deque()
        self.hunt_mode = False
        self.hunt_direction = None
        self.hunt_start = None
        self.tried_directions = []
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._make_bombing_move(state)

    def _place_ship(self, state):
        """Smart ship placement - tries to place ships away from each other."""
        ship_length = state['ships_to_place'][0]
        
        # Try up to 100 times to find a good position
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            # Check if placement is valid (no overlapping)
            if self._is_valid_placement(state['my_board'], row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Fallback to random placement if no valid found
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

    def _is_valid_placement(self, board, row, col, length, orientation):
        """Check if ship placement is valid (within bounds and no overlap)."""
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for i in range(length):
                if board[row][col + i] != 'O':
                    return False
        else:  # vertical
            if row + length > self.board_size:
                return False
            for i in range(length):
                if board[row + i][col] != 'O':
                    return False
        return True

    def _make_bombing_move(self, state):
        """Implements hunting algorithm for bombing phase."""
        # Update board with last shot result
        if state['last_shot_coord'] is not None:
            row, col = state['last_shot_coord']
            if state['last_shot_result'] == 'HIT':
                self.enemy_board[row][col] = 'H'
                # If we weren't hunting, start hunting around this hit
                if not self.hunt_mode:
                    self.last_hit = (row, col)
                    self.hunt_mode = True
                    self.hunt_start = (row, col)
                    self.tried_directions = []
                    self._add_adjacent_targets(row, col)
            else:  # MISS
                self.enemy_board[row][col] = 'M'
                
        # If we have potential targets from hunting, try them
        while self.potential_targets:
            target = self.potential_targets.popleft()
            if self._is_valid_target(target[0], target[1]):
                return {'target': target}
        
        # Reset hunting if we've exhausted possibilities
        self.hunt_mode = False
        self.hunt_direction = None
        self.hunt_start = None
        self.tried_directions = []
        
        # Otherwise, use parity search (checkerboard pattern) for initial search
        return self._parity_search()

    def _add_adjacent_targets(self, row, col):
        """Add adjacent cells as potential targets, considering direction."""
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
        
        # If we already have a direction, continue in that direction
        if self.hunt_direction:
            dr, dc = self.hunt_direction
            r, c = row + dr, col + dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size:
                self.potential_targets.append((r, c))
            # Also try the opposite direction from the original hit
            r, c = self.hunt_start[0] - dr, self.hunt_start[1] - dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size:
                self.potential_targets.append((r, c))
        else:
            # Otherwise, try all directions
            for dr, dc in directions:
                r, c = row + dr, col + dc
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    # Only add if we haven't tried this direction
                    if (dr, dc) not in self.tried_directions and (-dr, -dc) not in self.tried_directions:
                        self.potential_targets.append((r, c))

    def _parity_search(self):
        """Use a checkerboard pattern to efficiently search for ships."""
        # Create list of all cells with parity (checkerboard pattern)
        candidates = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                # Check if cell is untargeted
                if self.enemy_board[row][col] is None:
                    # Use checkerboard pattern (only even parity for ships of length > 1)
                    if (row + col) % 2 == 0:
                        candidates.append((row, col))
        
        # If no even parity cells left, try odd parity
        if not candidates:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if self.enemy_board[row][col] is None:
                        if (row + col) % 2 == 1:
                            candidates.append((row, col))
        
        # If still no candidates, just find any untargeted cell
        if not candidates:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if self.enemy_board[row][col] is None:
                        candidates.append((row, col))
        
        if candidates:
            target = random.choice(candidates)
            return {'target': target}
        else:
            # Fallback (shouldn't happen in normal gameplay)
            return {'target': (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))}

    def _is_valid_target(self, row, col):
        """Check if a target is valid (not already targeted)."""
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return self.enemy_board[row][col] is None
        return False
