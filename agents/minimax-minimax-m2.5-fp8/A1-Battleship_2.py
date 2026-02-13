"""
Agent Code: A1-Battleship
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-13 14:03:41
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Smart Battleship Agent with strategic placement and probability-based bombing.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.shots_fired = set()  # Track all shots we've made (row, col)
        self.hits = []  # List of hit coordinates to follow up on
        self.pending_targets = deque()  # Adjacent cells to try after a hit
        self.last_shot_result = None
        self.remaining_ships = list(ships)  # Copy of ships to track what's left
    
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ships(state)
        else:
            return self._bomb(state)
    
    def _place_ships(self, state):
        """Smart placement: spread ships out and avoid edges when possible."""
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        # Try multiple strategies in order of preference
        # Strategy 1: Place with maximum distance from center (spreads ships)
        placement = self._find_best_placement(board, ship_length, strategy='spread')
        if placement:
            return placement
            
        # Strategy 2: Any valid placement
        placement = self._find_any_placement(board, ship_length)
        if placement:
            return placement
            
        # Fallback: should never reach here if board is large enough
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }
    
    def _find_best_placement(self, board, ship_length, strategy='spread'):
        """Find best placement based on strategy."""
        best_score = -float('inf')
        best_placement = None
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                for orientation in ['horizontal', 'vertical']:
                    if self._can_place(board, row, col, orientation, ship_length):
                        score = self._evaluate_placement(board, row, col, orientation, ship_length, strategy)
                        if score > best_score:
                            best_score = score
                            best_placement = {
                                'ship_length': ship_length,
                                'start': (row, col),
                                'orientation': orientation
                            }
        
        return best_placement
    
    def _evaluate_placement(self, board, row, col, orientation, ship_length, strategy):
        """Evaluate how good a placement is."""
        if strategy == 'spread':
            # Prefer placements away from edges and other ships
            score = 0
            center = self.board_size / 2
            
            # Prefer toward center
            if orientation == 'horizontal':
                avg_row = row
                avg_col = col + ship_length / 2
            else:
                avg_row = row + ship_length / 2
                avg_col = col
            
            score += abs(avg_row - center) + abs(avg_col - center)
            
            # Penalty for being on edge
            if row == 0 or row == self.board_size - 1 or col == 0 or col == self.board_size - 1:
                score -= 5
            
            # Penalty for adjacency to existing ships
            for r in range(max(0, row - 1), min(self.board_size, row + 2)):
                for c in range(max(0, col - 1), min(self.board_size, col + 2)):
                    if self._in_ship_range(r, c, row, col, orientation, ship_length):
                        continue
                    if board[r][c] == 'S':
                        score -= 10
            
            return score
        return 0
    
    def _in_ship_range(self, r, c, row, col, orientation, length):
        """Check if (r,c) is within the ship placement area."""
        if orientation == 'horizontal':
            return row == r and col <= c < col + length
        else:
            return col == c and row <= r < row + length
    
    def _find_any_placement(self, board, ship_length):
        """Find any valid placement."""
        for row in range(self.board_size):
            for col in range(self.board_size):
                for orientation in ['horizontal', 'vertical']:
                    if self._can_place(board, row, col, orientation, ship_length):
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
        return None
    
    def _can_place(self, board, row, col, orientation, length):
        """Check if ship can be placed at position."""
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
    
    def _bomb(self, state):
        """Smart bombing using probability and hit-following."""
        # Update state from previous turn
        if state.get('last_shot_result'):
            self.last_shot_result = state['last_shot_result']
            
            if state['turn_continues'] and state['last_shot_result'] == 'HIT':
                # Add adjacent cells to pending targets
                last_coord = state['last_shot_coord']
                if last_coord:
                    self._add_adjacent_targets(last_coord)
        
        # Priority 1: Check pending targets from previous hits
        while self.pending_targets:
            target = self.pending_targets.popleft()
            if target not in self.shots_fired:
                self.shots_fired.add(target)
                return {'target': target}
        
        # Priority 2: If we just hit and have turn continuation, target adjacent
        if state.get('turn_continues') and state.get('last_shot_result') == 'HIT':
            last_coord = state.get('last_shot_coord')
            if last_coord:
                self._add_adjacent_targets(last_coord)
                while self.pending_targets:
                    target = self.pending_targets.popleft()
                    if target not in self.shots_fired:
                        self.shots_fired.add(target)
                        return {'target': target}
        
        # Priority 3: Use probability-based targeting
        target = self._find_best_target()
        if target:
            self.shots_fired.add(target)
            return {'target': target}
        
        # Fallback: random unshot cell
        available = [(r, c) for r in range(self.board_size) 
                              for c in range(self.board_size) 
                              if (r, c) not in self.shots_fired]
        if available:
            target = random.choice(available)
            self.shots_fired.add(target)
            return {'target': target}
        
        # Should not reach here unless board is full
        return {'target': (0, 0)}
    
    def _add_adjacent_targets(self, coord):
        """Add adjacent cells (up, down, left, right) to pending targets."""
        row, col = coord
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.board_size and 0 <= new_col < self.board_size:
                if (new_row, new_col) not in self.shots_fired:
                    self.pending_targets.append((new_row, new_col))
    
    def _find_best_target(self):
        """Find the best target using probability density."""
        best_target = None
        best_score = -1
        
        # Calculate probability map
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) in self.shots_fired:
                    continue
                
                score = self._calculate_probability(row, col)
                if score > best_score:
                    best_score = score
                    best_target = (row, col)
        
        return best_target
    
    def _calculate_probability(self, row, col):
        """Calculate probability that a cell contains a ship based on remaining ships."""
        probability = 0
        
        for ship_length in self.remaining_ships:
            # Check horizontal placements
            for start_col in range(max(0, col - ship_length + 1), 
                                    min(col + 1, self.board_size - ship_length + 1)):
                valid = True
                for c in range(start_col, start_col + ship_length):
                    if (row, c) in self.shots_fired:
                        valid = False
                        break
                if valid:
                    probability += 1
            
            # Check vertical placements
            for start_row in range(max(0, row - ship_length + 1),
                                    min(row + 1, self.board_size - ship_length + 1)):
                valid = True
                for r in range(start_row, start_row + ship_length):
                    if (r, col) in self.shots_fired:
                        valid = False
                        break
                if valid:
                    probability += 1
        
        return probability
