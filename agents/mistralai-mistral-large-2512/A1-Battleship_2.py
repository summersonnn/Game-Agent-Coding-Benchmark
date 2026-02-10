"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-10 16:22:20
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)
        self.my_board = [[EMPTY for _ in range(board_size)] for _ in range(board_size)]
        self.target_queue = deque()
        self.hunt_mode = True
        self.last_hit = None
        self.potential_targets = []
        self.shot_history = set()
        self.initialize_probability_map()

    def initialize_probability_map(self):
        self.probability_map = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self.place_ship(state, feedback)
        else:
            return self.bomb_target(state)

    def place_ship(self, state, feedback):
        ship_length = state['ships_to_place'][0]

        # Try to place ships in a pattern that minimizes clustering
        for attempt in range(MAX_PLACEMENT_ATTEMPTS):
            # Prefer placing larger ships first in less crowded areas
            if ship_length == max(self.ships):
                # Place largest ship in center with some randomness
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(self.board_size//4, 3*self.board_size//4)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(self.board_size//4, 3*self.board_size//4)
            else:
                # Place smaller ships with some spacing from existing ships
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                    # Check if this area is too crowded
                    if self.is_area_crowded(row, col, ship_length, orientation):
                        continue
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                    # Check if this area is too crowded
                    if self.is_area_crowded(row, col, ship_length, orientation):
                        continue

            # Validate placement
            if self.is_valid_placement(state['my_board'], row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }

        # If all attempts failed, place randomly
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

    def is_area_crowded(self, row, col, length, orientation):
        """Check if the area around a potential ship placement is too crowded"""
        padding = 1  # Minimum space between ships
        if orientation == 'horizontal':
            for r in range(max(0, row-padding), min(self.board_size, row+padding+1)):
                for c in range(max(0, col-padding), min(self.board_size, col+length+padding)):
                    if r < len(self.my_board) and c < len(self.my_board[0]) and self.my_board[r][c] == SHIP:
                        return True
        else:
            for r in range(max(0, row-padding), min(self.board_size, row+length+padding)):
                for c in range(max(0, col-padding), min(self.board_size, col+padding+1)):
                    if r < len(self.my_board) and c < len(self.my_board[0]) and self.my_board[r][c] == SHIP:
                        return True
        return False

    def is_valid_placement(self, board, row, col, length, orientation):
        """Check if a ship placement is valid"""
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for c in range(col, col + length):
                if board[row][c] != EMPTY:
                    return False
        else:
            if row + length > self.board_size:
                return False
            for r in range(row, row + length):
                if board[r][col] != EMPTY:
                    return False
        return True

    def bomb_target(self, state):
        # Update shot history
        if state['last_shot_coord']:
            self.shot_history.add(state['last_shot_coord'])

        # If we have potential targets from previous hits, target those first
        if self.target_queue:
            target = self.target_queue.popleft()
            if target in self.shot_history:
                # Skip already targeted cells
                if self.target_queue:
                    target = self.target_queue.popleft()
                else:
                    # Fall back to probability-based targeting
                    target = self.get_probability_target(state)
            return {'target': target}

        # If we got a hit last turn, switch to target mode
        if state['last_shot_result'] == 'HIT':
            self.last_hit = state['last_shot_coord']
            self.hunt_mode = False
            self.generate_potential_targets(state['last_shot_coord'])
            if self.target_queue:
                target = self.target_queue.popleft()
                return {'target': target}

        # If we're in hunt mode or no targets left, use probability-based targeting
        target = self.get_probability_target(state)
        return {'target': target}

    def generate_potential_targets(self, hit_coord):
        """Generate potential targets around a hit coordinate"""
        row, col = hit_coord
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up

        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size and (r, c) not in self.shot_history:
                self.target_queue.append((r, c))

    def get_probability_target(self, state):
        """Calculate probability map and return the highest probability target"""
        self.initialize_probability_map()

        # Update probability map based on remaining ships
        remaining_ships = self.get_remaining_ships(state)

        for length in remaining_ships:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    # Check horizontal placement
                    if col + length <= self.board_size:
                        valid = True
                        for c in range(col, col + length):
                            if (row, c) in self.shot_history and state['shot_history'][-1]['result'] == 'HIT':
                                valid = False
                                break
                        if valid:
                            for c in range(col, col + length):
                                if (row, c) not in self.shot_history:
                                    self.probability_map[row][c] += 1

                    # Check vertical placement
                    if row + length <= self.board_size:
                        valid = True
                        for r in range(row, row + length):
                            if (r, col) in self.shot_history and state['shot_history'][-1]['result'] == 'HIT':
                                valid = False
                                break
                        if valid:
                            for r in range(row, row + length):
                                if (r, col) not in self.shot_history:
                                    self.probability_map[r][col] += 1

        # Find the cell with highest probability that hasn't been shot yet
        max_prob = -1
        best_targets = []

        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.shot_history and self.probability_map[row][col] > max_prob:
                    max_prob = self.probability_map[row][col]
                    best_targets = [(row, col)]
                elif (row, col) not in self.shot_history and self.probability_map[row][col] == max_prob:
                    best_targets.append((row, col))

        # If multiple targets have same probability, choose randomly
        if best_targets:
            return random.choice(best_targets)
        else:
            # Fallback to random if no valid targets found (shouldn't happen)
            while True:
                target = (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))
                if target not in self.shot_history:
                    return target

    def get_remaining_ships(self, state):
        """Estimate remaining ships based on hit patterns"""
        # This is a simplified version - a more sophisticated agent would track sunk ships
        remaining_ships = self.ships.copy()

        # Count hits and estimate which ships might be sunk
        hits = sum(1 for shot in state['shot_history'] if shot['result'] == 'HIT')

        # Very rough estimation - in a real implementation, you'd track sunk ships
        if hits >= sum(remaining_ships):
            return [min(remaining_ships)]

        return remaining_ships
