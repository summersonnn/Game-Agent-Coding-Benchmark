"""
Agent Code: A1-Battleship
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-17 12:25:21
"""



import random

class BattleshipAgent:
    """
    Intelligent Battleship agent using hunt-and-target strategy for bombing
    and validated random placement for ship positioning.
    """
    
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.targeted_cells = set()
        self.hits = []
        
    def make_move(self, state, feedback):
        """Main entry point for both placement and bombing phases."""
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        """Place a ship on the board using validated random placement."""
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        placement = self._find_valid_placement(board, ship_length)
        return placement
    
    def _find_valid_placement(self, board, ship_length):
        """Find a valid placement for the ship."""
        # Try random placements first for efficiency
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            if self._is_valid_placement(board, row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Brute force fallback
        return self._brute_force_placement(board, ship_length)
    
    def _is_valid_placement(self, board, row, col, length, orientation):
        """Check if a placement is valid."""
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            return all(board[row][col + i] == 'O' for i in range(length))
        else:  # vertical
            if row + length > self.board_size:
                return False
            return all(board[row + i][col] == 'O' for i in range(length))
    
    def _brute_force_placement(self, board, ship_length):
        """Exhaustive search for valid placement."""
        # Horizontal placements
        for row in range(self.board_size):
            for col in range(self.board_size - ship_length + 1):
                if self._is_valid_placement(board, row, col, ship_length, 'horizontal'):
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': 'horizontal'
                    }
        
        # Vertical placements
        for col in range(self.board_size):
            for row in range(self.board_size - ship_length + 1):
                if self._is_valid_placement(board, row, col, ship_length, 'vertical'):
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': 'vertical'
                    }
        
        # Fallback (should not happen in valid game)
        return {'ship_length': ship_length, 'start': (0, 0), 'orientation': 'horizontal'}
    
    def _bomb(self, state):
        """Execute bombing strategy."""
        # Update hit tracking from shot history
        for shot in state['shot_history']:
            coord = shot['coord']
            if coord not in self.targeted_cells:
                self.targeted_cells.add(coord)
                if shot['result'] == 'HIT':
                    self.hits.append(coord)
        
        # Select and return target
        target = self._select_target()
        return {'target': target}
    
    def _select_target(self):
        """Select next target: target ship if hit, otherwise hunt."""
        if self.hits:
            target = self._target_around_hits()
            if target:
                return target
        
        return self._hunt_checkerboard()
    
    def _target_around_hits(self):
        """Target cells adjacent to known hits to sink ship."""
        row, col = self.hits[-1]
        
        # Determine if recent hits form a line
        direction = None
        if len(self.hits) >= 2:
            prev_hit = self.hits[-2]
            if prev_hit[0] == row:  # Same row = horizontal line
                direction = 'horizontal'
            elif prev_hit[1] == col:  # Same column = vertical line
                direction = 'vertical'
        
        candidates = []
        
        if direction == 'horizontal':
            # Extend horizontally from the hit
            for offset in range(1, self.board_size):
                for nc in [col + offset, col - offset]:
                    if 0 <= nc < self.board_size and (row, nc) not in self.targeted_cells:
                        candidates.append((row, nc))
        elif direction == 'vertical':
            # Extend vertically from the hit
            for offset in range(1, self.board_size):
                for nr in [row + offset, row - offset]:
                    if 0 <= nr < self.board_size and (nr, col) not in self.targeted_cells:
                        candidates.append((nr, col))
        else:
            # No clear direction yet, try orthogonal neighbors
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) not in self.targeted_cells:
                    candidates.append((nr, nc))
        
        return candidates[0] if candidates else None
    
    def _hunt_checkerboard(self):
        """Hunt for undiscovered ships using checkerboard pattern.
        Guaranteed to hit any ship of size 2+."""
        # Phase 1: checkerboard pattern (efficient for all ship sizes)
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row + col) % 2 == 0 and (row, col) not in self.targeted_cells:
                    return (row, col)
        
        # Phase 2: fill remaining gaps
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.targeted_cells:
                    return (row, col)
        
        # Fallback (should not reach in normal game)
        return (0, 0)
