"""
Agent Code: A1-Battleship
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 2
Generated: 2026-02-11 19:24:56
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
    Your agent implementation goes here.
    Implement smart placement and bombing logic to beat your opponent.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # Initialize internal state tracking
        # We maintain a local view of the opponent's board for our own logic
        self.opponent_view = [[EMPTY for _ in range(board_size)] for _ in range(board_size)]
        self.potential_targets = deque()
        self.hunt_mode = False

    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].
        """
        if state['phase'] == 'placement':
            return self.handle_placement(state)
        else:
            return self.handle_bombing(state)

    def handle_placement(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        size = self.board_size
        
        # Try to place ships somewhat spread out to avoid easy clustering kills
        # We iterate through the board to find a valid spot
        # To make it non-deterministic but smart, we can shuffle the search order
        
        positions = []
        
        # Check horizontal placements
        for r in range(size):
            for c in range(size - ship_length + 1):
                if all(board[r][c+k] == EMPTY for k in range(ship_length)):
                    positions.append({'ship_length': ship_length, 'start': (r, c), 'orientation': 'horizontal'})
        
        # Check vertical placements
        for c in range(size):
            for r in range(size - ship_length + 1):
                if all(board[r+k][c] == EMPTY for k in range(ship_length)):
                    positions.append({'ship_length': ship_length, 'start': (r, c), 'orientation': 'vertical'})
        
        if positions:
            # Pick a random valid position to ensure some variety
            return random.choice(positions)
        
        # Fallback (should rarely happen if logic is correct and board isn't full)
        # This handles edge cases or if the random logic above is too restrictive
        orientation = random.choice(['horizontal', 'vertical'])
        if orientation == 'horizontal':
            row = random.randint(0, size - 1)
            col = random.randint(0, size - ship_length)
        else:
            row = random.randint(0, size - ship_length)
            col = random.randint(0, size - 1)
            
        return {
            'ship_length': ship_length,
            'start': (row, col),
            'orientation': orientation
        }

    def handle_bombing(self, state):
        # Update our internal view of the opponent's board based on the last shot
        if state['last_shot_coord']:
            r, c = state['last_shot_coord']
            result = state['last_shot_result']
            self.opponent_view[r][c] = result
            
            if result == 'HIT':
                self.hunt_mode = True
                self.potential_targets.append((r, c))

        # Strategy:
        # 1. Hunt Mode: If we have recent hits, target adjacent cells to sink the ship.
        # 2. Search Mode: If no active hits, target random cells using a parity strategy (checkerboard)
        #    to maximize the probability of hitting ships (since smallest ship is length 3, 
        #    checkerboard is effective, but random is sufficient for this level).

        target = None

        if self.hunt_mode and self.potential_targets:
            # We have hits, let's try to sink the ship.
            # We prioritize cells that are adjacent to existing hits.
            
            # Check if we can determine the orientation of the ship we are hitting
            # by looking for consecutive hits.
            
            # Try to find a valid target adjacent to any hit in our stack
            # We copy the list to iterate safely while modifying or just iterate
            current_hits = list(self.potential_targets)
            
            # First, try to extend a line of hits (smarter hunting)
            # Check horizontal adjacency
            for r, c in current_hits:
                # Check right
                if c + 1 < self.board_size and self.opponent_view[r][c+1] == EMPTY:
                    # Check if this makes sense with other hits (simple heuristic: if we hit r, c-1, prefer r, c+1)
                    target = (r, c+1)
                    break
                # Check left
                if c - 1 >= 0 and self.opponent_view[r][c-1] == EMPTY:
                    target = (r, c-1)
                    break
            
            # If no horizontal target found, check vertical
            if not target:
                for r, c in current_hits:
                    # Check down
                    if r + 1 < self.board_size and self.opponent_view[r+1][c] == EMPTY:
                        target = (r+1, c)
                        break
                    # Check up
                    if r - 1 >= 0 and self.opponent_view[r-1][c] == EMPTY:
                        target = (r-1, c)
                        break
            
            # If we found a target, return it
            if target:
                return {'target': target}
            else:
                # No valid adjacent targets found. 
                # This might happen if we surrounded a hit or if the hits were isolated and we checked all neighbors.
                # In this case, we assume the ship is sunk or we are blocked, so we clear the hunt mode.
                self.hunt_mode = False
                self.potential_targets.clear()

        # Search Mode: Hunt mode is off or failed to find a target.
        # We pick a random empty cell.
        # Optimization: Checkerboard pattern (target cells where (r+c)%2 == 0) is statistically better
        # for finding ships of length >= 2.
        
        possible_moves = []
        checker_moves = []
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.opponent_view[r][c] == EMPTY:
                    possible_moves.append((r, c))
                    if (r + c) % 2 == 0:
                        checker_moves.append((r, c))
        
        # Prefer checkerboard moves to ensure we hit ships efficiently
        if checker_moves:
            return {'target': random.choice(checker_moves)}
        elif possible_moves:
            return {'target': random.choice(possible_moves)}
        
        # Should not reach here unless board is full
        return {'target': (0, 0)}
