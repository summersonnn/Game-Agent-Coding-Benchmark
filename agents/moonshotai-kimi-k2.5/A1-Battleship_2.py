"""
Agent Code: A1-Battleship
Model: moonshotai/kimi-k2.5
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
        # Maintain a list of high-priority targets (adjacent to hits)
        self.targets = []
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        """Place ships using random valid placement with fallback to systematic."""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Try random placement several times
        for _ in range(50):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                max_row = self.board_size - 1
                max_col = self.board_size - ship_length
            else:
                max_row = self.board_size - ship_length
                max_col = self.board_size - 1
                
            row = random.randint(0, max_row)
            col = random.randint(0, max_col)
            
            if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Systematic fallback: scan board for first valid position
        for row in range(self.board_size):
            for col in range(self.board_size):
                for orientation in ['horizontal', 'vertical']:
                    if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
        
        # Ultimate fallback (should never reach here)
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }
    
    def _is_valid_placement(self, board, row, col, length, orientation):
        """Check if ship placement is valid (in bounds and no overlap)."""
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for c in range(col, col + length):
                if board[row][c] != 'O':  # 'O' represents empty
                    return False
        else:
            if row + length > self.board_size:
                return False
            for r in range(row, row + length):
                if board[r][col] != 'O':
                    return False
        return True
    
    def _bomb(self, state):
        """Bombing strategy using hunt-and-target with checkerboard pattern."""
        shot_history = state['shot_history']
        last_result = state['last_shot_result']
        last_coord = state['last_shot_coord']
        
        # Reconstruct shot tracking from history
        shots = set(s['coord'] for s in shot_history)
        hits = set(s['coord'] for s in shot_history if s['result'] == 'HIT')
        
        # Update targeting strategy based on last shot result
        if last_result == 'HIT' and last_coord:
            r, c = last_coord
            # Check if this hit is adjacent to any previous hit to determine ship direction
            direction_found = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in hits:
                    # Found a line, prioritize continuing in this direction
                    nr2, nc2 = r + 2*dr, c + 2*dc
                    if self._is_valid_target((nr2, nc2), shots):
                        self.targets.insert(0, (nr2, nc2))  # High priority
                    # Also prioritize the opposite end of the ship
                    opp_r, opp_c = r - dr, c - dc
                    if self._is_valid_target((opp_r, opp_c), shots):
                        self.targets.insert(0, (opp_r, opp_c))
                    direction_found = True
                    break
            
            if not direction_found:
                # Isolated hit, add all 4 adjacent cells for investigation
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if self._is_valid_target((nr, nc), shots):
                        self.targets.append((nr, nc))
        
        # Clean up target list: remove already-shot cells and duplicates
        valid_targets = []
        seen = set()
        for t in self.targets:
            if t not in seen and t not in shots and self._in_bounds(t):
                valid_targets.append(t)
                seen.add(t)
        self.targets = valid_targets
        
        # TARGET MODE: If we have pending targets from previous hits, use them
        if self.targets:
            target = self.targets.pop(0)
            return {'target': target}
        
        # HUNT MODE: Use checkerboard pattern to efficiently find ships
        # Since smallest ship is 3, checkerboard ensures we don't miss any
        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r + c) % 2 == 0 and (r, c) not in shots:
                    candidates.append((r, c))
        
        if candidates:
            # Random selection from checkerboard to avoid predictable patterns
            target = random.choice(candidates)
            return {'target': target}
        
        # Fallback: shoot any remaining unshot cell
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in shots:
                    return {'target': (r, c)}
        
        return {'target': (0, 0)}
    
    def _is_valid_target(self, coord, shots):
        """Check if coordinate is valid for bombing (in bounds and not already shot)."""
        r, c = coord
        return 0 <= r < self.board_size and 0 <= c < self.board_size and coord not in shots
    
    def _in_bounds(self, coord):
        r, c = coord
        return 0 <= r < self.board_size and 0 <= c < self.board_size
