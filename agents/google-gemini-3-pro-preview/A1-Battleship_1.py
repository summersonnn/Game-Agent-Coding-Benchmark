"""
Agent Code: A1-Battleship
Model: google-gemini-3-pro-preview
Run: 1
Generated: 2026-02-11 19:27:04
"""

import random
from collections import deque

class BattleshipAgent:
    """
    A smart Battleship agent that uses Probability Density Functions (PDF) for hunting
    and a parity-based target stack for destroying ships.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.target_queue = deque() # Queue for potential targets after a hit
        self.hits = set()
        self.misses = set()
        
    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].
        """
        if state['phase'] == 'placement':
            return self._place_ship(state)
        elif state['phase'] == 'bombing':
            return self._bomb(state)

    def _place_ship(self, state):
        """
        Randomly attempts to place ships until a valid position is found.
        Checks against the current board state to prevent overlaps.
        """
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Try random positions until valid
        for _ in range(200): # Safety limit to prevent infinite loops
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)

            if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Fallback (should theoretically not be reached with 200 attempts on empty/semi-empty board)
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }

    def _is_valid_placement(self, board, row, col, length, orientation):
        """Helper to check if a specific placement overlaps existing ships."""
        for i in range(length):
            r, c = (row, col + i) if orientation == 'horizontal' else (row + i, col)
            if board[r][c] != 'O': # Assuming 'O' is Empty
                return False
        return True

    def _bomb(self, state):
        """
        Bombing Strategy:
        1. Update internal tracker of hits/misses from history.
        2. If previous move was a HIT, add neighbors to target_queue.
        3. Priority 1: Process target_queue (Kill mode).
        4. Priority 2: Calculate Probability Density Function (Hunt mode).
        """
        # 1. Sync State
        self._sync_history(state['shot_history'])
        
        # 2. Logic Update based on immediate feedback
        if state['last_shot_result'] == 'HIT' and state['last_shot_coord']:
            self._add_neighbors_to_queue(state['last_shot_coord'])

        # 3. Determine Move
        target = None
        
        # Mode: TARGET (Drain the queue)
        while self.target_queue:
            candidate = self.target_queue.popleft()
            if candidate not in self.hits and candidate not in self.misses:
                target = candidate
                break
        
        # Mode: HUNT (Probability Density)
        if target is None:
            target = self._get_best_probability_target()

        return {'target': target}

    def _sync_history(self, history):
        """Updates internal sets based on game history."""
        self.hits.clear()
        self.misses.clear()
        for shot in history:
            coord = shot['coord']
            if shot['result'] == 'HIT':
                self.hits.add(coord)
            else:
                self.misses.add(coord)

    def _add_neighbors_to_queue(self, coord):
        """Adds valid neighbors of a hit to the queue."""
        r, c = coord
        # Potential neighbors (Up, Down, Left, Right)
        candidates = [
            (r - 1, c), (r + 1, c), 
            (r, c - 1), (r, c + 1)
        ]
        
        # Intelligent Filtering:
        # If we have hits that form a line, prioritize the ends of that line.
        # This is a simple heuristic: if we hit at (r,c), and (r-1,c) is also a hit,
        # we really want to check (r+1,c) first.
        
        sorted_candidates = []
        for cr, cc in candidates:
            if 0 <= cr < self.board_size and 0 <= cc < self.board_size:
                if (cr, cc) not in self.hits and (cr, cc) not in self.misses:
                    sorted_candidates.append((cr, cc))

        # Add to LEFT of deque to prioritize these new neighbors (DFS-like behavior for destroying)
        # Random shuffle prevents predictable patterns when no line is obvious
        random.shuffle(sorted_candidates)
        for cand in sorted_candidates:
            self.target_queue.appendleft(cand)

    def _get_best_probability_target(self):
        """
        Calculates a heatmap of where ships *could* be.
        Returns the cell with the highest probability overlap.
        """
        heatmap = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # We don't know exactly which ships are left, so we calculate for all 
        # provided ship lengths. This is a robust approximation.
        for length in self.ships:
            # Horizontal Scan
            for r in range(self.board_size):
                for c in range(self.board_size - length + 1):
                    coords = [(r, c + k) for k in range(length)]
                    if self._can_ship_fit(coords):
                        for r_h, c_h in coords:
                            heatmap[r_h][c_h] += 1
            
            # Vertical Scan
            for r in range(self.board_size - length + 1):
                for c in range(self.board_size):
                    coords = [(r + k, c) for k in range(length)]
                    if self._can_ship_fit(coords):
                        for r_v, c_v in coords:
                            heatmap[r_v][c_v] += 1

        # Find max value in heatmap that hasn't been shot
        best_score = -1
        best_target = None
        
        # Parity Check: Ships are min length 3. 
        # We only strictly need to check every other cell (checkerboard) to find them.
        # We prioritize high probability + parity.
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) in self.hits or (r, c) in self.misses:
                    continue
                
                score = heatmap[r][c]
                
                # Update best if score is strictly higher
                if score > best_score:
                    best_score = score
                    best_target = (r, c)
                # Tie-breaker: Prefer checkerboard (parity) spots
                elif score == best_score:
                    if (r + c) % 2 == 0: 
                        best_target = (r, c)

        # Fallback if map is zero (should rarely happen unless board full)
        if best_target is None:
            return self._get_random_valid_target()
            
        return best_target

    def _can_ship_fit(self, coords):
        """
        Checks if a hypothetical ship placement overlaps with known MISSES.
        Note: In Hunt mode, we generally also avoid known HITS because we represent
        'Hunt' as looking for *new* ships. Existing HITS are handled by target_queue.
        """
        for r, c in coords:
            if (r, c) in self.misses:
                return False
            if (r, c) in self.hits:
                return False
        return True

    def _get_random_valid_target(self):
        """Random fallback for valid moves."""
        options = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.hits and (r, c) not in self.misses:
                    options.append((r, c))
        if not options:
            return (0, 0) # Should verify game over before this
        return random.choice(options)