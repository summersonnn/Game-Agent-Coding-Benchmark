"""
Agent Code: A1-Battleship
Model: minimax/minimax-m2.1@preset/fp8
Run: 1
Generated: 2026-02-11 19:21:34
"""

from collections import deque

import random
from collections import deque

# --- Game Configuration ---
BOARD_SIZE = 8
SHIPS = [5, 4, 3]
NUM_GAMES = 5
# --- Board Representations ---
EMPTY = 'O'
SHIP = 'S'
HIT = 'X'
SUNK = '#'
MISS = 'M'

class BattleshipGame:
    """ Manages the state and rules of the game. """
    def __init__(self, size, ships):
        self.size = size
        self.ships = ships

    def _create_empty_board(self):
        return [[EMPTY for _ in range(self.size)] for _ in range(self.size)]

    def is_game_over(self, ships_board):
        """Checks if all ships on a given board have been sunk."""
        return not any(SHIP in row for row in ships_board)

# -------------------------------------------------------------------------------
class BattleshipAgent:
    """
    Smart Battleship Agent with strategic placement and adaptive bombing.
    
    Placement Strategy:
    - Places larger ships first to maximize placement options
    - Uses random placement with overlap checking
    - Falls back to systematic search if random attempts fail
    
    Bombing Strategy:
    - Uses "Hunt and Target" approach
    - Hunt mode: Checkerboard pattern search to find ships
    - Target mode: Prioritizes adjacent cells after hits to sink ships
    - Maintains shot history and hit tracking for efficient targeting
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        
        # Precompute search pattern for bombing phase (checkerboard pattern)
        self.search_pattern = []
        for r in range(board_size):
            for c in range(board_size):
                if (r + c) % 2 == 0:  # Checkerboard pattern
                    self.search_pattern.append((r, c))
        self.search_index = 0
        
        # Track potential targets (adjacent to hits)
        self.potential_targets = set()
        
    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].
        
        Parameters:
        - state: Dictionary containing game state
        - feedback: Always None (reserved for future use)
        
        Returns:
        - During placement phase: Dictionary with 'ship_length', 'start', and 'orientation'
        - During bombing phase: Dictionary with 'target'
        """
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:  # bombing phase
            return self._make_bombing_move(state)
    
    def _place_ship(self, state):
        """
        Strategic ship placement avoiding overlaps.
        Uses random placement with systematic fallback.
        """
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Try random placement first (up to 100 attempts)
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            # Check for overlap
            if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Fallback: systematic search for valid placement
        for row in range(self.board_size):
            for col in range(self.board_size):
                for orientation in ['horizontal', 'vertical']:
                    if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
        
        # Ultimate fallback: random placement (will be penalized if invalid)
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
        """Check if ship placement is valid (within bounds, no overlap)."""
        for i in range(length):
            r = row + (i if orientation == 'vertical' else 0)
            c = col + (i if orientation == 'horizontal' else 0)
            
            if not (0 <= r < self.board_size and 0 <= c < self.board_size):
                return False
            if board[r][c] != EMPTY:
                return False
        return True
    
    def _make_bombing_move(self, state):
        """
        Adaptive bombing using Hunt and Target strategy.
        Prioritizes targeting adjacent cells after hits.
        """
        # Build shot history and track hits
        shots_set = set()
        hits_set = set()
        
        for shot in state['shot_history']:
            coord = shot['coord']
            shots_set.add(coord)
            if shot['result'] == 'HIT':
                hits_set.add(coord)
        
        # Update potential targets from all hits
        self._update_potential_targets(hits_set, shots_set)
        
        # If we have potential targets, prioritize them
        if self.potential_targets:
            target = random.choice(list(self.potential_targets))
            self.potential_targets.discard(target)  # Remove used target
            return {'target': target}
        
        # Otherwise, use search pattern
        return self._get_next_search_target(shots_set)
    
    def _update_potential_targets(self, hits_set, shots_set):
        """Update potential targets by checking adjacent cells to hits."""
        self.potential_targets = set()
        
        for hit in hits_set:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                r, c = hit[0] + dr, hit[1] + dc
                
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    target = (r, c)
                    if target not in shots_set:
                        self.potential_targets.add(target)
    
    def _get_next_search_target(self, shots_set):
        """Get next target from search pattern, skipping already-shot cells."""
        # Advance search index past already-shot cells
        while self.search_index < len(self.search_pattern):
            candidate = self.search_pattern[self.search_index]
            self.search_index += 1
            
            if candidate not in shots_set:
                return {'target': candidate}
        
        # Fallback: find any unshot cell
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in shots_set:
                    return {'target': (r, c)}
        
        # Ultimate fallback (shouldn't happen in valid game)
        return {'target': (0, 0)}
