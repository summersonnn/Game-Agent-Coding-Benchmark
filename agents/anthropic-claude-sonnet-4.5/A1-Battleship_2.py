"""
Agent Code: A1-Battleship
Model: anthropic/claude-sonnet-4.5
Run: 2
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
        
        # Bombing phase tracking
        self.shot_grid = [[None for _ in range(board_size)] for _ in range(board_size)]
        self.targets = deque()  # High-priority targets to pursue
        self.current_hits = []  # Hits on the current ship being targeted
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self.place_ship(state)
        else:
            return self.bomb(state)
    
    def place_ship(self, state):
        """Place ships with validation"""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Try random placements first
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
                if self.is_valid_placement(my_board, row, col, ship_length, 'horizontal'):
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': 'horizontal'
                    }
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
                if self.is_valid_placement(my_board, row, col, ship_length, 'vertical'):
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': 'vertical'
                    }
        
        # Systematic fallback search
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.is_valid_placement(my_board, row, col, ship_length, 'horizontal'):
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': 'horizontal'
                    }
                if self.is_valid_placement(my_board, row, col, ship_length, 'vertical'):
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': 'vertical'
                    }
        
        # Emergency fallback
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }
    
    def is_valid_placement(self, board, row, col, length, orientation):
        """Check if ship placement is valid (within bounds and no overlap)"""
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for c in range(col, col + length):
                if board[row][c] == 'S':
                    return False
        else:  # vertical
            if row + length > self.board_size:
                return False
            for r in range(row, row + length):
                if board[r][col] == 'S':
                    return False
        return True
    
    def bomb(self, state):
        """Intelligent bombing with hunt and target modes"""
        # Update state based on last shot
        if state['last_shot_coord'] is not None:
            row, col = state['last_shot_coord']
            result = state['last_shot_result']
            self.shot_grid[row][col] = result
            
            if result == 'HIT':
                self.current_hits.append((row, col))
                self.update_targets_after_hit(row, col)
        
        target = self.choose_target()
        return {'target': target}
    
    def update_targets_after_hit(self, row, col):
        """Add smart targets after getting a hit"""
        if len(self.current_hits) == 1:
            # First hit on this ship - explore all 4 directions
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                r, c = row + dr, col + dc
                if self.is_valid_target(r, c):
                    self.targets.append((r, c))
        elif len(self.current_hits) >= 2:
            # Multiple hits - determine orientation and focus on line ends
            line_ends = self.get_line_extensions()
            if line_ends:
                self.targets.clear()
                for r, c in line_ends:
                    if self.is_valid_target(r, c):
                        self.targets.append((r, c))
    
    def is_valid_target(self, row, col):
        """Check if coordinate is valid and untargeted"""
        return (0 <= row < self.board_size and 
                0 <= col < self.board_size and
                self.shot_grid[row][col] is None)
    
    def get_line_extensions(self):
        """Get the two ends of the line formed by current hits"""
        if len(self.current_hits) < 2:
            return []
        
        rows = [h[0] for h in self.current_hits]
        cols = [h[1] for h in self.current_hits]
        
        # Check if horizontal line (same row)
        if len(set(rows)) == 1:
            row = rows[0]
            min_col, max_col = min(cols), max(cols)
            return [(row, min_col - 1), (row, max_col + 1)]
        
        # Check if vertical line (same column)
        if len(set(cols)) == 1:
            col = cols[0]
            min_row, max_row = min(rows), max(rows)
            return [(min_row - 1, col), (max_row + 1, col)]
        
        return []
    
    def choose_target(self):
        """Choose the next cell to target"""
        # Priority 1: Follow up on hits
        while self.targets:
            target = self.targets.popleft()
            if self.shot_grid[target[0]][target[1]] is None:
                return target
        
        # No valid targets left from hits - ship is likely sunk
        if self.current_hits:
            self.current_hits = []
        
        # Priority 2: Hunt mode using checkerboard pattern
        # This guarantees finding all ships of size 3+ efficiently
        checkerboard_cells = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.shot_grid[row][col] is None and (row + col) % 2 == 0:
                    checkerboard_cells.append((row, col))
        
        if checkerboard_cells:
            return random.choice(checkerboard_cells)
        
        # Priority 3: Any remaining untargeted cell
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.shot_grid[row][col] is None:
                    return (row, col)
        
        # Fallback (shouldn't reach here)
        return (0, 0)
