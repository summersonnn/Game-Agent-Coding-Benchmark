"""
Agent Code: A1-Battleship
Model: qwen/qwen3-coder-next
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
        self.my_ships_positions = []  # List of (row, col) for each ship segment
        self.placed_ships = []        # List of placed ships info for reference
        self.target_hunt = []         # Queue of cells to target using hunt mode
        self.target_mode = False      # Whether we're in target mode (after a hit)
        self.hit_stack = []           # Stack for target mode to explore neighbors
        self.known_hits = []          # List of (row, col) that we've hit
        self.known_misses = set()     # Set of (row, col) that we've missed
        self.shot_history = []        # Our shot history for reference
        self.parity_pattern = []      # For parity-based hunting (checkerboard)

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._smart_placement(state)
        else:  # bombing phase
            return self._smart_bombing(state)

    def _smart_placement(self, state):
        # Use a deterministic placement strategy to avoid random penalties
        board = state['my_board']
        ships_to_place = state['ships_to_place']
        ship_length = ships_to_place[0]
        
        # Try to place ships in corners and edges to minimize interference
        # Try 4 quadrants in order: top-left, top-right, bottom-left, bottom-right
        orientations = ['horizontal', 'vertical']
        attempts = []
        
        # Generate candidate placements in a systematic way
        for orientation in orientations:
            for start_row in range(self.board_size):
                for start_col in range(self.board_size):
                    if orientation == 'horizontal':
                        if start_col + ship_length <= self.board_size:
                            candidate = {
                                'start': (start_row, start_col),
                                'orientation': 'horizontal',
                                'ship_length': ship_length
                            }
                            if self._is_valid_placement(board, candidate, ship_length):
                                return {
                                    'ship_length': ship_length,
                                    'start': candidate['start'],
                                    'orientation': candidate['orientation']
                                }
                    else:  # vertical
                        if start_row + ship_length <= self.board_size:
                            candidate = {
                                'start': (start_row, start_col),
                                'orientation': 'vertical',
                                'ship_length': ship_length
                            }
                            if self._is_valid_placement(board, candidate, ship_length):
                                return {
                                    'ship_length': ship_length,
                                    'start': candidate['start'],
                                    'orientation': candidate['orientation']
                                }
        
        # If no deterministic placement found (shouldn't happen), fall back to random
        return {
            'ship_length': ship_length,
            'start': (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1)),
            'orientation': random.choice(['horizontal', 'vertical'])
        }
    
    def _is_valid_placement(self, board, candidate, ship_length):
        start_row, start_col = candidate['start']
        orientation = candidate['orientation']
        
        # Check boundaries
        if orientation == 'horizontal':
            if start_col + ship_length > self.board_size:
                return False
        else:  # vertical
            if start_row + ship_length > self.board_size:
                return False
        
        # Check for overlap with existing ships
        for i in range(ship_length):
            if orientation == 'horizontal':
                r, c = start_row, start_col + i
            else:
                r, c = start_row + i, start_col
            
            if board[r][c] == 'S':
                return False
        
        # Check adjacency (ships can't touch, even diagonally)
        for i in range(ship_length):
            if orientation == 'horizontal':
                r, c = start_row, start_col + i
            else:
                r, c = start_row + i, start_col
            
            # Check all 8 neighbors
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if board[nr][nc] == 'S':
                            return False
        
        return True

    def _smart_bombing(self, state):
        # Update internal state from feedback
        self.shot_history = state.get('shot_history', [])
        self.known_misses = set()
        self.known_hits = []
        
        for entry in self.shot_history:
            coord = entry['coord']
            result = entry['result']
            if result == 'MISS':
                self.known_misses.add(coord)
            else:  # HIT
                self.known_hits.append(coord)
        
        # Check if we need to reset target mode
        last_result = state.get('last_shot_result')
        last_coord = state.get('last_shot_coord')
        turn_continues = state.get('turn_continues', False)
        
        if last_result == 'HIT' and last_coord:
            if not turn_continues:
                # Last hit resulted in a sunk ship - clear stack and restart hunt
                self.hit_stack = []
                self.target_mode = False
            else:
                # Continue targeting around this hit
                self._add_neighbors_to_stack(last_coord)
                self.target_mode = True
        
        # If we're in target mode, try to continue hitting
        if self.target_mode and self.hit_stack:
            target = self.hit_stack.pop()
            while target in self.known_misses or any(c == target for c in self.known_hits):
                if not self.hit_stack:
                    self.target_mode = False
                    break
                target = self.hit_stack.pop()
            
            if 0 <= target[0] < self.board_size and 0 <= target[1] < self.board_size:
                return {'target': target}
        
        # Otherwise, use parity-based hunting (checkerboard pattern)
        # This ensures we cover the board efficiently without wasting moves
        parity_row = state.get('board_size', self.board_size)
        
        # Generate all cells in checkerboard pattern (black squares first)
        black_squares = []
        white_squares = []
        
        for r in range(parity_row):
            for c in range(parity_row):
                if (r + c) % 2 == 0:
                    black_squares.append((r, c))
                else:
                    white_squares.append((r, c))
        
        # Prioritize black squares first if we have no hits yet, else alternate
        # But if we have hits, use the parity that matches the ship orientation
        # For simplicity, use black squares first then white
        all_candidates = black_squares + white_squares
        
        # Filter out already targeted cells
        available = [cell for cell in all_candidates 
                    if cell not in self.known_misses and cell not in self.known_hits]
        
        if available:
            # Prioritize cells adjacent to known hits (if any)
            priority = []
            for cell in available:
                r, c = cell
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    neighbor = (r+dr, c+dc)
                    if neighbor in self.known_hits:
                        priority.append(cell)
                        break
            
            if priority:
                # Choose the most promising among priority cells
                return {'target': priority[0]}
            else:
                # Use a random cell from available to add variety
                return {'target': random.choice(available)}
        else:
            # If all cells are targeted, pick a random untargeted one (fallback)
            for r in range(parity_row):
                for c in range(parity_row):
                    if (r, c) not in self.known_misses and (r, c) not in self.known_hits:
                        return {'target': (r, c)}
            
            # Ultimate fallback: random
            return {'target': (random.randint(0, parity_row-1), random.randint(0, parity_row-1))}

    def _add_neighbors_to_stack(self, hit_coord):
        r, c = hit_coord
        neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        
        # Filter out-of-bounds and already targeted cells
        for n in neighbors:
            if (0 <= n[0] < self.board_size and 
                0 <= n[1] < self.board_size and
                n not in self.known_misses and 
                n not in self.known_hits):
                self.hit_stack.append(n)
