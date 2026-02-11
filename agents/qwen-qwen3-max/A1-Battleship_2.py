"""
Agent Code: A1-Battleship
Model: qwen/qwen3-max
Run: 2
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
        self.possible_targets = None
        self.hit_stack = deque()
        self.tried_shots = set()
        self.current_ship_hits = []
        self.last_hit_direction = None
        self.ship_sizes = ships[:]
        self.sunk_ships = []
        self.opponent_board = None

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:  # bombing phase
            return self._make_bombing_move(state)

    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Try to find a valid placement with some strategy
        attempts = 0
        max_attempts = 100
        
        while attempts < max_attempts:
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            # Check if placement is valid
            valid = True
            for i in range(ship_length):
                if orientation == 'horizontal':
                    r, c = row, col + i
                else:
                    r, c = row + i, col
                
                if my_board[r][c] != 'O':
                    valid = False
                    break
            
            if valid:
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
            
            attempts += 1
        
        # Fallback to random placement (should rarely happen)
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

    def _make_bombing_move(self, state):
        # Initialize opponent board tracking if needed
        if self.opponent_board is None:
            self.opponent_board = [['?' for _ in range(self.board_size)] for _ in range(self.board_size)]
            self.possible_targets = [(r, c) for r in range(self.board_size) for c in range(self.board_size)]
            random.shuffle(self.possible_targets)
        
        # Update board state based on last shot
        if state['last_shot_coord'] is not None:
            r, c = state['last_shot_coord']
            if state['last_shot_result'] == 'HIT':
                self.opponent_board[r][c] = 'H'
                self.hit_stack.append((r, c))
                self.current_ship_hits.append((r, c))
            else:  # MISS
                self.opponent_board[r][c] = 'M'
                self.tried_shots.add((r, c))
                if not state['turn_continues']:
                    # Reset current ship tracking if turn ends
                    self.current_ship_hits = []
                    self.last_hit_direction = None
        
        # Check if we should continue hunting a ship we've hit
        if self.current_ship_hits and state['turn_continues']:
            return self._target_adjacent_to_hits()
        
        # If we have hits but turn doesn't continue, we'll start fresh next turn
        if not state['turn_continues']:
            self.current_ship_hits = []
            self.last_hit_direction = None
        
        # Use hunting strategy - prioritize untried spots
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.opponent_board[r][c] == '?':
                    self.tried_shots.add((r, c))
                    return {'target': (r, c)}
        
        # Fallback (should not happen in normal gameplay)
        available = [(r, c) for r in range(self.board_size) for c in range(self.board_size) 
                    if (r, c) not in self.tried_shots]
        if available:
            target = random.choice(available)
            self.tried_shots.add(target)
            return {'target': target}
        else:
            # All cells tried, pick random
            return {'target': (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))}

    def _target_adjacent_to_hits(self):
        """Target cells adjacent to known hits to sink the ship."""
        if not self.current_ship_hits:
            return self._get_random_untargeted()
        
        # Get the most recent hit
        last_hit_r, last_hit_c = self.current_ship_hits[-1]
        
        # Define directions: up, right, down, left
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        # If we have a direction we're exploring, continue in that direction
        if self.last_hit_direction is not None:
            dr, dc = self.last_hit_direction
            next_r, next_c = last_hit_r + dr, last_hit_c + dc
            if (0 <= next_r < self.board_size and 0 <= next_c < self.board_size and 
                self.opponent_board[next_r][next_c] == '?'):
                self.tried_shots.add((next_r, next_c))
                return {'target': (next_r, next_c)}
            # If we can't continue in that direction, try the opposite
            opp_r, opp_c = last_hit_r - dr, last_hit_c - dc
            if (0 <= opp_r < self.board_size and 0 <= opp_c < self.board_size and 
                self.opponent_board[opp_r][opp_c] == '?'):
                self.tried_shots.add((opp_r, opp_c))
                return {'target': (opp_r, opp_c)}
        
        # Try all directions around the last hit
        random.shuffle(directions)
        for dr, dc in directions:
            r, c = last_hit_r + dr, last_hit_c + dc
            if (0 <= r < self.board_size and 0 <= c < self.board_size and 
                self.opponent_board[r][c] == '?'):
                self.last_hit_direction = (dr, dc)
                self.tried_shots.add((r, c))
                return {'target': (r, c)}
        
        # If no adjacent cells available, try around other hits
        for hit_r, hit_c in self.current_ship_hits:
            for dr, dc in directions:
                r, c = hit_r + dr, hit_c + dc
                if (0 <= r < self.board_size and 0 <= c < self.board_size and 
                    self.opponent_board[r][c] == '?'):
                    self.tried_shots.add((r, c))
                    return {'target': (r, c)}
        
        # Fallback to random untargeted cell
        return self._get_random_untargeted()
    
    def _get_random_untargeted(self):
        """Get a random cell that hasn't been targeted yet."""
        available = [(r, c) for r in range(self.board_size) for c in range(self.board_size) 
                    if (r, c) not in self.tried_shots]
        if available:
            target = random.choice(available)
            self.tried_shots.add(target)
            return {'target': target}
        else:
            return {'target': (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))}
