"""
Agent Code: A1-Battleship
Model: qwen/qwen3-coder@preset/fp8
Run: 2
Generated: 2026-02-11 19:37:45
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)  # Process largest ships first for placement
        self.enemy_board = [[None for _ in range(board_size)] for _ in range(board_size)]  # Track hits/misses
        self.enemy_ships_sunk = []  # List of sunk ship lengths
        self.last_hit = None
        self.potential_targets = deque()  # Queue for adjacent cells after a hit
        self.targeting_ship = False
        self.hunt_mode = False
        self.hunt_direction = None
        self.hunt_start = None
        self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb_ship(state)

    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        
        # Try to place ships in corners or edges for better defense
        attempts = 0
        while attempts < 100:
            attempts += 1
            # Prefer placing ships along edges
            if random.random() < 0.7:  # 70% chance to try edge placement
                # Try horizontal placement on top/bottom rows
                if random.choice([True, False]):
                    row = random.choice([0, self.board_size - 1])
                    col = random.randint(0, self.board_size - ship_length)
                    orientation = 'horizontal'
                else:
                    col = random.choice([0, self.board_size - 1])
                    row = random.randint(0, self.board_size - ship_length)
                    orientation = 'vertical'
            else:
                # Random placement
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)

            # Validate placement
            if self._is_valid_placement(state['my_board'], ship_length, (row, col), orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Fallback to random if no valid placement found
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

    def _is_valid_placement(self, board, ship_length, start, orientation):
        row, col = start
        if orientation == 'horizontal':
            if col + ship_length > self.board_size:
                return False
            for i in range(ship_length):
                if board[row][col + i] != 'O':
                    return False
        else:  # vertical
            if row + ship_length > self.board_size:
                return False
            for i in range(ship_length):
                if board[row + i][col] != 'O':
                    return False
        return True

    def _bomb_ship(self, state):
        # Update our knowledge based on last shot result
        if state['last_shot_result'] is not None and state['last_shot_coord'] is not None:
            row, col = state['last_shot_coord']
            self.enemy_board[row][col] = state['last_shot_result']
            
            if state['last_shot_result'] == 'HIT':
                self.last_hit = (row, col)
                # Add adjacent cells to potential targets if not already added
                self._add_adjacent_targets(row, col)
                
                # Check if we just sunk a ship
                if self._check_if_sunk(state):
                    self._reset_hunt()
            elif state['last_shot_result'] == 'MISS':
                # If we were hunting in a direction and missed, try the opposite direction
                if self.hunt_mode and self.hunt_direction:
                    self._switch_hunt_direction()
        
        # If we have specific targets from a hit, use them
        if self.potential_targets:
            target = self.potential_targets.popleft()
            # Ensure target is valid (not already shot)
            while self.enemy_board[target[0]][target[1]] is not None:
                if not self.potential_targets:
                    break
                target = self.potential_targets.popleft()
            else:
                return {'target': target}
        
        # Reset hunting if needed
        self._reset_hunt_if_needed()
        
        # Otherwise use parity search (checkerboard pattern) for better efficiency
        return {'target': self._get_parity_target()}

    def _add_adjacent_targets(self, row, col):
        # If this is a new hit (not continuing a line), start hunting
        if not self.hunt_mode:
            self.hunt_mode = True
            self.hunt_start = (row, col)
            self.hunt_direction = None
            
        # Add all adjacent cells that haven't been shot yet
        for dr, dc in self.directions:
            r, c = row + dr, col + dc
            if (0 <= r < self.board_size and 
                0 <= c < self.board_size and 
                self.enemy_board[r][c] is None):
                
                # If we're already hunting in a direction, only add targets in that line
                if self.hunt_direction:
                    # Check if this cell is in the current hunting direction
                    dir_r, dir_c = self.hunt_direction
                    if (r == row + dir_r and c == col + dir_c) or \
                       (r == row - dir_r and c == col - dir_c):
                        self.potential_targets.append((r, c))
                else:
                    self.potential_targets.append((r, c))

    def _switch_hunt_direction(self):
        # If we missed while hunting in one direction, try the opposite
        if self.hunt_direction and self.hunt_start:
            dr, dc = self.hunt_direction
            opposite_direction = (-dr, -dc)
            
            # Clear current targets and add target in opposite direction
            self.potential_targets.clear()
            r, c = self.hunt_start
            new_r, new_c = r + opposite_direction[0], c + opposite_direction[1]
            
            if (0 <= new_r < self.board_size and 
                0 <= new_c < self.board_size and 
                self.enemy_board[new_r][new_c] is None):
                self.potential_targets.append((new_r, new_c))
                self.hunt_direction = opposite_direction
            else:
                self._reset_hunt()

    def _check_if_sunk(self, state):
        # Count consecutive hits to determine if a ship was sunk
        if not state['shot_history']:
            return False
            
        # Get the most recent hit
        recent_hits = []
        for shot in reversed(state['shot_history']):
            if shot['result'] == 'HIT':
                recent_hits.append(shot['coord'])
            else:
                break
                
        # Check if we've hit the length of any unsunk ship
        hit_count = len(recent_hits)
        for ship_len in self.ships:
            if ship_len not in self.enemy_ships_sunk and hit_count >= ship_len:
                self.enemy_ships_sunk.append(ship_len)
                return True
        return False

    def _reset_hunt(self):
        self.hunt_mode = False
        self.hunt_direction = None
        self.hunt_start = None
        self.potential_targets.clear()

    def _reset_hunt_if_needed(self):
        # If we have no more potential targets but are still in hunt mode, reset
        if self.hunt_mode and not self.potential_targets:
            self._reset_hunt()

    def _get_parity_target(self):
        # Use checkerboard pattern for efficient searching
        # Only target cells that could contain a ship (based on parity)
        available_targets = []
        
        # Create a list of all unshot cells
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.enemy_board[row][col] is None:
                    # Apply parity: for ships of length > 1, we can skip every other cell initially
                    # But we need to be more careful - let's target all unshot cells for now
                    # In practice, a more advanced parity approach would consider ship lengths
                    available_targets.append((row, col))
        
        # If we have targets from hunting, prioritize those
        if self.potential_targets:
            return self.potential_targets[0]
            
        # Otherwise pick randomly from available targets
        if available_targets:
            return random.choice(available_targets)
        else:
            # Fallback (shouldn't happen in normal play)
            return (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))
