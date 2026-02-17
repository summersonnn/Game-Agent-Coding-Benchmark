"""
Agent Code: A1-Battleship
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-17 12:25:21
"""

from collections import deque

import random
from collections import deque

# Constants for board representation
EMPTY = 'O'
SHIP = 'S'
HIT = 'X'
MISS = 'M'

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        
        # Internal state tracking for the bombing phase
        # Tracks our view of the opponent's board: None=unknown, 'M'=miss, 'H'=hit
        self.opponent_board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # Set of coordinates that are valid to shoot (not yet shot)
        self.possible_targets = {(r, c) for r in range(self.board_size) for c in range(self.board_size)}
        
        # Stack to manage hunting mode (targeting adjacent to hits)
        self.hits_stack = deque()

    def make_move(self, state, feedback):
        """
        Main decision loop for both placement and bombing phases.
        """
        if state['phase'] == 'placement':
            return self._handle_placement(state)
        elif state['phase'] == 'bombing':
            return self._handle_bombing(state)
        return None

    # --- Placement Phase Logic ---

    def _handle_placement(self, state):
        """
        Strategy: Random valid placement.
        The state provides 'my_board', allowing us to check for collisions.
        """
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Find all valid positions
        valid_starts = []
        
        # Check horizontal placements
        for r in range(self.board_size):
            for c in range(self.board_size - ship_length + 1):
                if all(my_board[r][c + k] == EMPTY for k in range(ship_length)):
                    valid_starts.append(((r, c), 'horizontal'))
                    
        # Check vertical placements
        for r in range(self.board_size - ship_length + 1):
            for c in range(self.board_size):
                if all(my_board[r + k][c] == EMPTY for k in range(ship_length)):
                    valid_starts.append(((r, c), 'vertical'))
        
        if valid_starts:
            # Randomly select one valid placement
            start, orientation = random.choice(valid_starts)
            return {
                'ship_length': ship_length,
                'start': start,
                'orientation': orientation
            }
        
        # Fallback (should rarely be needed if logic is correct)
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

    # --- Bombing Phase Logic ---

    def _handle_bombing(self, state):
        """
        Strategy:
        1. Update internal board based on last shot result.
        2. If we have hits, try to sink the ship (Hunt Mode).
        3. Otherwise, search for ships using a checkerboard pattern (Search Mode).
        """
        
        # Update state with the result of the previous shot
        self._process_feedback(state)
        
        target = None
        
        # Priority 1: Hunt Mode (targeting neighbors of hits)
        if self.hits_stack:
            target = self._get_hunt_target()
            
        # Priority 2: Search Mode (random checkerboard)
        if target is None:
            target = self._get_search_target()
            
        # Remove target from possible set to ensure we don't shoot it again
        if target in self.possible_targets:
            self.possible_targets.remove(target)
            # Temporarily mark to prevent race conditions in logic, 
            # though we remove it immediately above.
            self.opponent_board[target[0]][target[1]] = 'PENDING'
            
        return {'target': target}

    def _process_feedback(self, state):
        """
        Updates the opponent board and hits stack based on the last shot.
        """
        last_shot = state['last_shot_coord']
        last_result = state['last_shot_result']
        
        if last_shot is None:
            return

        r, c = last_shot
        
        # If we had marked it pending (or just for safety), clear/update it
        if self.opponent_board[r][c] == 'PENDING':
            self.opponent_board[r][c] = None
            
        if last_result == 'HIT':
            self.opponent_board[r][c] = 'H'
            # Add to stack for processing in hunt mode
            self.hits_stack.append(last_shot)
            
        elif last_result == 'MISS':
            self.opponent_board[r][c] = 'M'
            # If we missed while hunting, we simply continue. 
            # The _get_hunt_target logic handles finding new neighbors 
            # or backtracking if necessary.

    def _get_hunt_target(self):
        """
        Finds a valid neighbor of a known hit.
        """
        # Use a temporary set to avoid reprocessing the same hit in this loop
        processed_in_loop = set()
        
        while self.hits_stack:
            current_hit = self.hits_stack[0]
            
            if current_hit in processed_in_loop:
                # We've checked this hit and found no moves, discard it
                self.hits_stack.popleft()
                continue
                
            r, c = current_hit
            neighbors = []
            
            # Check 4 adjacent directions
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            random.shuffle(directions) # Add randomness to direction selection
            
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if (nr, nc) in self.possible_targets:
                        neighbors.append((nr, nc))
            
            if neighbors:
                return neighbors[0]
            else:
                # No valid neighbors for this hit
                processed_in_loop.add(current_hit)
                self.hits_stack.popleft()
                
        return None

    def _get_search_target(self):
        """
        Selects a target using a checkerboard pattern to maximize hit probability.
        """
        # We prefer (r + c) % 2 == 0 (like white squares on a chessboard)
        # This guarantees a hit on a ship of length 2 or more if it is placed
        # such that it covers a white square.
        parity_targets = [t for t in self.possible_targets if (t[0] + t[1]) % 2 == 0]
        
        if parity_targets:
            return random.choice(parity_targets)
        else:
            # If all parity targets exhausted, shoot anywhere remaining
            return random.choice(list(self.possible_targets))
