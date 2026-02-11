"""
Agent Code: A1-Battleship
Model: google-gemini-3-pro-preview
Run: 2
Generated: 2026-02-11 19:27:56
"""

import random
from collections import deque

class BattleshipAgent:
    """
    A smart Battleship agent that uses parity-based hunting and 
    stack-based targeting strategies.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        
        # Bombing state tracking
        self.priority_targets = deque() # Queue for 'Target' mode
        self.shots_fired = set()        # Keep track of where we have shot
        self.known_hits = set()         # Keep track of hits to determine axis

    def make_move(self, state, feedback=None):
        """
        Handles both placement and bombing phases based on state['phase'].
        """
        if state['phase'] == 'placement':
            return self._place_ships(state)
        elif state['phase'] == 'bombing':
            return self._bomb_ships(state)
        else:
            raise ValueError("Unknown phase")

    def _place_ships(self, state):
        """
        Tries to find a valid placement for the current ship by checking 
        against the 'my_board' provided in the state.
        """
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        rows = self.board_size
        cols = self.board_size

        # Try up to 100 times to find a valid random spot
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                r = random.randint(0, rows - 1)
                c = random.randint(0, cols - ship_length)
            else:
                r = random.randint(0, rows - ship_length)
                c = random.randint(0, cols - 1)

            # Check for overlap
            valid = True
            if orientation == 'horizontal':
                for k in range(ship_length):
                    if my_board[r][c + k] != 'O': # Assuming 'O' is empty
                        valid = False
                        break
            else: # vertical
                for k in range(ship_length):
                    if my_board[r + k][c] != 'O':
                        valid = False
                        break
            
            if valid:
                return {
                    'ship_length': ship_length,
                    'start': (r, c),
                    'orientation': orientation
                }

        # Fallback (should rarely happen given 100 attempts on empty board)
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }

    def _bomb_ships(self, state):
        """
        Decides where to bomb.
        1. Syncs internal history with game state.
        2. Processes the result of the previous shot (did we hit?).
        3. Fires from Priority Queue (Target Mode) or Parity Hunt (Hunt Mode).
        """
        # --- 1. Sync State ---
        # It is safer to rebuild shots_fired from history to ensure sync with engine
        self.shots_fired = set()
        for shot in state['shot_history']:
            self.shots_fired.add(shot['coord'])
            if shot['result'] == 'HIT':
                self.known_hits.add(shot['coord'])

        # --- 2. Process Previous Shot ---
        # If the last shot was a hit, add neighbors to priority queue
        if state['last_shot_result'] == 'HIT':
            last_r, last_c = state['last_shot_coord']
            self.known_hits.add((last_r, last_c))
            
            # Smart Neighbor Add: Look for adjacent hits to determine alignment
            potential_neighbors = []
            
            # Check for horizontal alignment
            if (last_r, last_c - 1) in self.known_hits or (last_r, last_c + 1) in self.known_hits:
                # We are likely on a horizontal ship, prioritize Left/Right
                potential_neighbors.extend([(last_r, last_c - 1), (last_r, last_c + 1)])
                potential_neighbors.extend([(last_r - 1, last_c), (last_r + 1, last_c)]) # Add others as lower priority
            # Check for vertical alignment
            elif (last_r - 1, last_c) in self.known_hits or (last_r + 1, last_c) in self.known_hits:
                # We are likely on a vertical ship, prioritize Up/Down
                potential_neighbors.extend([(last_r - 1, last_c), (last_r + 1, last_c)])
                potential_neighbors.extend([(last_r, last_c - 1), (last_r, last_c + 1)]) # Add others as lower priority
            else:
                # No alignment yet, add all 4 neighbors (randomize order to be less predictable)
                neighbors = [
                    (last_r - 1, last_c), (last_r + 1, last_c),
                    (last_r, last_c - 1), (last_r, last_c + 1)
                ]
                random.shuffle(neighbors)
                potential_neighbors.extend(neighbors)

            # Add valid neighbors to the FRONT of the queue (Depth-First Search approach)
            # We reverse to maintain the order when appending left
            for r, c in reversed(potential_neighbors):
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if (r, c) not in self.shots_fired and (r, c) not in self.priority_targets:
                        self.priority_targets.appendleft((r, c))

        # --- 3. Execute Strategy ---
        
        # STRATEGY A: Target Mode (Finish off wounded ships)
        while self.priority_targets:
            target = self.priority_targets[0] # Peek
            
            # If we already shot here (e.g. via another path), discard
            if target in self.shots_fired:
                self.priority_targets.popleft()
                continue
            
            # Valid target found
            self.priority_targets.popleft()
            return {'target': target}

        # STRATEGY B: Hunt Mode (Find new ships)
        # Use Checkerboard/Parity pattern. 
        # (r + c) % 2 == 0 ensures we hit every ship > size 1 eventually 
        # while skipping half the board.
        candidates = []
        fallback_candidates = [] # In case parity spots are full
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.shots_fired:
                    if (r + c) % 2 == 0:
                        candidates.append((r, c))
                    else:
                        fallback_candidates.append((r, c))

        if candidates:
            # Pick a random spot from the checkerboard pattern
            target = random.choice(candidates)
            return {'target': target}
        elif fallback_candidates:
            # If checkerboard is full, clean up the rest
            target = random.choice(fallback_candidates)
            return {'target': target}
        
        # Should not happen unless board is full
        return {'target': (0, 0)}