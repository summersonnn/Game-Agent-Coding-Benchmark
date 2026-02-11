"""
Agent Code: A1-Battleship
Model: qwen/qwen3-max
Run: 1
Generated: 2026-02-11 19:24:56
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Your agent implementation goes here.
    Implement smart placement and bombing logic to beat your opponent.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # For bombing phase
        self.shots_fired = set()
        self.hit_stack = deque()  # Stack of coordinates to explore after a hit
        self.current_target_ship = []  # Track coordinates of the ship we're currently sinking
        self.sunk_ships = []  # List of sunk ship coordinates
        self.potential_targets = []  # Generated potential targets for systematic search
        
    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].
        """
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:  # bombing phase
            return self._make_bombing_move(state)
    
    def _place_ship(self, state):
        """Strategically place ships to maximize survivability."""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Try to find a valid placement with some strategy
        valid_placements = []
        
        # Generate all possible placements
        for orientation in ['horizontal', 'vertical']:
            if orientation == 'horizontal':
                for row in range(self.board_size):
                    for col in range(self.board_size - ship_length + 1):
                        if self._can_place_ship(my_board, ship_length, (row, col), orientation):
                            valid_placements.append((ship_length, (row, col), orientation))
            else:  # vertical
                for row in range(self.board_size - ship_length + 1):
                    for col in range(self.board_size):
                        if self._can_place_ship(my_board, ship_length, (row, col), orientation):
                            valid_placements.append((ship_length, (row, col), orientation))
        
        if not valid_placements:
            # Fallback to random placement (shouldn't happen with valid input)
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
        
        # Choose placement that maximizes distance from other ships (if any placed)
        # For simplicity, we'll prefer edge placements for larger ships and center for smaller
        if ship_length >= 4:
            # Prefer edges for larger ships
            edge_placements = []
            for placement in valid_placements:
                _, (row, col), orient = placement
                if orient == 'horizontal':
                    if row == 0 or row == self.board_size - 1 or col == 0 or col + ship_length - 1 == self.board_size - 1:
                        edge_placements.append(placement)
                else:
                    if col == 0 or col == self.board_size - 1 or row == 0 or row + ship_length - 1 == self.board_size - 1:
                        edge_placements.append(placement)
            
            if edge_placements:
                chosen = random.choice(edge_placements)
            else:
                chosen = random.choice(valid_placements)
        else:
            # For smaller ships, prefer more central locations
            center_placements = []
            center_range = range(self.board_size // 4, 3 * self.board_size // 4)
            for placement in valid_placements:
                _, (row, col), orient = placement
                if orient == 'horizontal':
                    if row in center_range and col in center_range:
                        center_placements.append(placement)
                else:
                    if col in center_range and row in center_range:
                        center_placements.append(placement)
            
            if center_placements:
                chosen = random.choice(center_placements)
            else:
                chosen = random.choice(valid_placements)
        
        return {
            'ship_length': chosen[0],
            'start': chosen[1],
            'orientation': chosen[2]
        }
    
    def _can_place_ship(self, board, ship_length, start, orientation):
        """Check if a ship can be placed at the given position."""
        row, col = start
        if orientation == 'horizontal':
            if col + ship_length > self.board_size:
                return False
            for c in range(col, col + ship_length):
                if board[row][c] != 'O':
                    return False
        else:  # vertical
            if row + ship_length > self.board_size:
                return False
            for r in range(row, row + ship_length):
                if board[r][col] != 'O':
                    return False
        return True
    
    def _make_bombing_move(self, state):
        """Make an intelligent bombing move."""
        # Update our tracking based on the last shot result
        if state['last_shot_coord'] is not None:
            last_coord = state['last_shot_coord']
            last_result = state['last_shot_result']
            
            if last_result == 'HIT':
                if last_coord not in self.current_target_ship:
                    self.current_target_ship.append(last_coord)
                # Add adjacent cells to hit_stack if not already fired
                self._add_adjacent_targets(last_coord)
            elif last_result == 'MISS':
                # If we get a miss after hits, we might need to adjust
                # But our hit_stack should handle this
                pass
        
        # Remove already fired shots from hit_stack
        while self.hit_stack and self.hit_stack[0] in self.shots_fired:
            self.hit_stack.popleft()
        
        # If we have targets from hits, prioritize those
        if self.hit_stack:
            target = self.hit_stack.popleft()
            while target in self.shots_fired and self.hit_stack:
                target = self.hit_stack.popleft()
            
            if target not in self.shots_fired:
                self.shots_fired.add(target)
                return {'target': target}
        
        # If we don't have hit-based targets, use systematic search
        if not self.potential_targets:
            self._generate_systematic_targets()
        
        # Remove already fired shots from potential targets
        while self.potential_targets and self.potential_targets[0] in self.shots_fired:
            self.potential_targets.pop(0)
        
        if self.potential_targets:
            target = self.potential_targets.pop(0)
            self.shots_fired.add(target)
            return {'target': target}
        
        # Fallback: random shot (should rarely happen)
        while True:
            row = random.randint(0, self.board_size - 1)
            col = random.randint(0, self.board_size - 1)
            if (row, col) not in self.shots_fired:
                self.shots_fired.add((row, col))
                return {'target': (row, col)}
    
    def _add_adjacent_targets(self, coord):
        """Add adjacent cells to the hit stack for exploration."""
        row, col = coord
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        
        # If we have multiple hits, try to determine ship orientation
        if len(self.current_target_ship) >= 2:
            # Determine if hits are in a line
            rows = [r for r, c in self.current_target_ship]
            cols = [c for r, c in self.current_target_ship]
            
            if len(set(rows)) == 1:  # Horizontal ship
                # Prioritize left and right
                directions = [(0, -1), (0, 1)]
            elif len(set(cols)) == 1:  # Vertical ship
                # Prioritize up and down
                directions = [(-1, 0), (1, 0)]
            # Otherwise, keep all directions
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if (0 <= new_row < self.board_size and 0 <= new_col < self.board_size and
                (new_row, new_col) not in self.shots_fired):
                # Add to front of deque to prioritize recent hits
                self.hit_stack.appendleft((new_row, new_col))
    
    def _generate_systematic_targets(self):
        """Generate a systematic pattern for initial searching."""
        # Use a checkerboard pattern to maximize coverage
        # Since the smallest ship is length 3, we can skip every other cell
        targets = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row + col) % 2 == 0:  # Checkerboard pattern
                    targets.append((row, col))
        
        # Shuffle to add some randomness
        random.shuffle(targets)
        self.potential_targets = targets
