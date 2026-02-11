"""
Agent Code: A1-Battleship
Model: qwen/qwen3-coder-next
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
        self.my_board = None
        self.enemy_ships = []  # Track enemy ship placements (if we get feedback)
        self.bombing_state = {
            'last_shot_result': None,
            'last_shot_coord': None,
            'turn_continues': False,
            'shot_history': [],
            'hit_stack': deque(),  # For hunt mode: coordinates to investigate after a hit
            'target_mode': False,  # True when in target mode (after a hit)
            'prob_board': None,
            'possible_ship_positions': None,
            'known_hits': set(),  # Coordinates we know are hits (from feedback)
            'known_misses': set(),  # Coordinates we know are misses
            'possible_orientations': {}  # For each hit, store possible orientations
        }

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ships(state)
        else:  # bombing phase
            return self._make_bombing_move(state)

    def _place_ships(self, state):
        """Strategic ship placement: avoid corners initially, ensure ships are spaced."""
        board = [row[:] for row in state['my_board']]  # Copy board
        ships_to_place = state['ships_to_place'].copy()
        placed_ships = []
        
        # Try to place ships with spacing to avoid clustering
        for ship_len in ships_to_place:
            placed = False
            attempts = 0
            max_attempts = 100
            
            while not placed and attempts < max_attempts:
                attempts += 1
                orientation = random.choice(['horizontal', 'vertical'])
                
                # Prefer center areas for placement
                if orientation == 'horizontal':
                    row = random.randint(1, self.board_size - 2)
                    col = random.randint(0, self.board_size - ship_len)
                else:
                    row = random.randint(0, self.board_size - ship_len)
                    col = random.randint(1, self.board_size - 2)
                
                start = (row, col)
                
                # Check validity
                if self._is_valid_placement(board, start, ship_len, orientation):
                    # Place ship
                    self._place_ship_on_board(board, start, ship_len, orientation)
                    placed_ships.append({
                        'length': ship_len,
                        'start': start,
                        'orientation': orientation
                    })
                    placed = True
            
            if not placed:
                # Fallback: random placement (will be corrected by game engine if invalid)
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_len)
                else:
                    row = random.randint(0, self.board_size - ship_len)
                    col = random.randint(0, self.board_size - 1)
                return {
                    'ship_length': ship_len,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Now we know placement is valid, return first ship placement
        first_ship = placed_ships[0]
        return {
            'ship_length': first_ship['length'],
            'start': first_ship['start'],
            'orientation': first_ship['orientation']
        }

    def _is_valid_placement(self, board, start, length, orientation):
        """Check if a ship placement is valid."""
        row, col = start
        
        if orientation == 'horizontal':
            # Check boundaries and overlap
            if col + length > self.board_size:
                return False
            for c in range(col, col + length):
                if board[row][c] != 'O':
                    return False
        else:  # vertical
            if row + length > self.board_size:
                return False
            for r in range(row, row + length):
                if board[r][col] != 'O':
                    return False
        
        return True

    def _place_ship_on_board(self, board, start, length, orientation):
        """Place a ship on the board (modifies board in-place)."""
        row, col = start
        if orientation == 'horizontal':
            for c in range(col, col + length):
                board[row][c] = 'S'
        else:
            for r in range(row, row + length):
                board[r][col] = 'S'

    def _make_bombing_move(self, state):
        """Smart bombing strategy: Hunt and Target mode with probability weighting."""
        # Update internal state
        self._update_bombing_state(state)
        
        # Initialize probability board if needed
        if self.bombing_state['prob_board'] is None:
            self._init_probability_board()
        
        # Use Hunt and Target mode
        if self.bombing_state['target_mode'] and self.bombing_state['hit_stack']:
            # Target mode: use hit_stack to find adjacent cells to try
            target = self._get_next_target_from_stack()
            if target:
                return {'target': target}
        
        # If not in target mode or stack is empty, use hunt mode with probability
        target = self._get_best_hunt_target()
        if target:
            return {'target': target}
        
        # Fallback: random valid move (shouldn't happen often)
        all_coords = [(r, c) for r in range(self.board_size) for c in range(self.board_size)]
        valid_coords = [(r, c) for r, c in all_coords 
                        if (r, c) not in self.bombing_state['known_hits'] 
                        and (r, c) not in self.bombing_state['known_misses']]
        if valid_coords:
            return {'target': random.choice(valid_coords)}
        else:
            # Very unlikely fallback
            return {'target': (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))}

    def _update_bombing_state(self, state):
        """Update internal state with new information."""
        last_shot_result = state.get('last_shot_result')
        last_shot_coord = state.get('last_shot_coord')
        turn_continues = state.get('turn_continues', False)
        shot_history = state.get('shot_history', [])
        
        # Update shot history
        if shot_history:
            self.bombing_state['shot_history'] = shot_history
            # Extract latest shot info
            if last_shot_coord:
                if last_shot_result == 'HIT':
                    self.bombing_state['known_hits'].add(last_shot_coord)
                    # Add to hit stack for target mode
                    self.bombing_state['hit_stack'].append(last_shot_coord)
                    self.bombing_state['target_mode'] = True
                elif last_shot_result == 'MISS':
                    self.bombing_state['known_misses'].add(last_shot_coord)
        
        # Update known hits/misses from history if needed
        for entry in shot_history:
            coord = entry['coord']
            result = entry['result']
            if result == 'HIT':
                self.bombing_state['known_hits'].add(coord)
            elif result == 'MISS':
                self.bombing_state['known_misses'].add(coord)
        
        # Reset target mode if we missed after a hit (turn_continues=False after a hit means ship sunk)
        if last_shot_result == 'MISS' and self.bombing_state['target_mode']:
            # If we had a hit stack and missed, that hit might be part of a sunk ship
            # Check if we should clear the stack
            pass  # We'll keep it for now and let the stack handle it

    def _init_probability_board(self):
        """Initialize probability board based on remaining ships."""
        self.bombing_state['prob_board'] = [[0.0] * self.board_size for _ in range(self.board_size)]
        self.bombing_state['possible_ship_positions'] = []
        
        # Get remaining ships (we know the full set, but need to track what's been sunk)
        # For simplicity, assume all ships are still in play initially
        remaining_ships = self.ships.copy()
        
        # Update based on known misses (can't place ships there)
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) in self.bombing_state['known_misses']:
                    self.bombing_state['prob_board'][r][c] = -1.0  # Mark as impossible
        
        # Calculate possible positions for each remaining ship
        for ship_len in remaining_ships:
            self._add_possible_positions(ship_len)
        
        # Update probabilities
        self._update_probabilities()

    def _add_possible_positions(self, ship_len):
        """Add all possible positions for a ship of given length."""
        for r in range(self.board_size):
            for c in range(self.board_size):
                # Horizontal
                if c + ship_len <= self.board_size:
                    positions = [(r, c + i) for i in range(ship_len)]
                    # Skip if any position is a known miss
                    if not any(pos in self.bombing_state['known_misses'] for pos in positions):
                        self.bombing_state['possible_ship_positions'].append(positions)
                
                # Vertical
                if r + ship_len <= self.board_size:
                    positions = [(r + i, c) for i in range(ship_len)]
                    if not any(pos in self.bombing_state['known_misses'] for pos in positions):
                        self.bombing_state['possible_ship_positions'].append(positions)

    def _update_probabilities(self):
        """Update probability board based on possible ship positions."""
        if self.bombing_state['prob_board'] is None:
            return
        
        # Reset probabilities
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.bombing_state['known_misses']:
                    self.bombing_state['prob_board'][r][c] = 0.0
        
        # Count how many possible positions include each cell
        for positions in self.bombing_state['possible_ship_positions']:
            for r, c in positions:
                if (r, c) not in self.bombing_state['known_hits']:
                    self.bombing_state['prob_board'][r][c] += 1.0
        
        # Normalize probabilities (optional but helps with comparison)
        max_prob = max(max(row) for row in self.bombing_state['prob_board']) if any(any(row) for row in self.bombing_state['prob_board']) else 1.0
        if max_prob > 0:
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if (r, c) not in self.bombing_state['known_hits'] and (r, c) not in self.bombing_state['known_misses']:
                        self.bombing_state['prob_board'][r][c] /= max_prob

    def _get_best_hunt_target(self):
        """Find the best target in hunt mode (highest probability)."""
        best_coord = None
        best_prob = -1.0
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.bombing_state['known_hits'] and (r, c) not in self.bombing_state['known_misses']:
                    prob = self.bombing_state['prob_board'][r][c] if self.bombing_state['prob_board'] else 1.0
                    # Add small random factor to break ties
                    prob += random.random() * 0.01
                    if prob > best_prob:
                        best_prob = prob
                        best_coord = (r, c)
        
        return best_coord

    def _get_next_target_from_stack(self):
        """Get next target from hit stack, considering adjacency and known info."""
        if not self.bombing_state['hit_stack']:
            return None
        
        # Get the most recent hit
        hit = self.bombing_state['hit_stack'][-1]
        r, c = hit
        
        # Determine adjacent cells to try
        adjacent = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        
        # Filter to valid, untried coordinates
        for coord in adjacent:
            nr, nc = coord
            if (0 <= nr < self.board_size and 0 <= nc < self.board_size and
                coord not in self.bombing_state['known_hits'] and
                coord not in self.bombing_state['known_misses']):
                return coord
        
        # If all adjacent are tried, pop from stack and try next
        self.bombing_state['hit_stack'].pop()
        return self._get_next_target_from_stack()

    def _place_ships(self, state):
        """Optimized ship placement using a greedy algorithm with spacing."""
        board = [row[:] for row in state['my_board']]  # Copy board
        ships_to_place = state['ships_to_place'].copy()
        placed_ships = []
        
        # Try to place ships with spacing to avoid clustering
        for ship_len in ships_to_place:
            placed = False
            attempts = 0
            max_attempts = 200
            
            while not placed and attempts < max_attempts:
                attempts += 1
                orientation = random.choice(['horizontal', 'vertical'])
                
                # Prefer center areas for placement
                if orientation == 'horizontal':
                    row = random.randint(1, self.board_size - 2)
                    col = random.randint(0, self.board_size - ship_len)
                else:
                    row = random.randint(0, self.board_size - ship_len)
                    col = random.randint(1, self.board_size - 2)
                
                start = (row, col)
                
                # Check validity
                if self._is_valid_placement(board, start, ship_len, orientation):
                    # Place ship
                    self._place_ship_on_board(board, start, ship_len, orientation)
                    placed_ships.append({
                        'length': ship_len,
                        'start': start,
                        'orientation': orientation
                    })
                    placed = True
            
            if not placed:
                # Fallback: random placement
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_len)
                else:
                    row = random.randint(0, self.board_size - ship_len)
                    col = random.randint(0, self.board_size - 1)
                return {
                    'ship_length': ship_len,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Now we know placement is valid, return first ship placement
        first_ship = placed_ships[0]
        return {
            'ship_length': first_ship['length'],
            'start': first_ship['start'],
            'orientation': first_ship['orientation']
        }
