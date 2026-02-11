"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-11 19:20:19
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)
        self.placement_attempts = 0
        self.hunt_mode = True
        self.target_queue = deque()
        self.shot_history = set()
        self.hit_history = set()
        self.potential_targets = set()
        self.last_hit = None
        self.ship_sizes = sorted(ships)
        self.remaining_ships = self.ship_sizes.copy()

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)

    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']

        # Try to place ships in a pattern that's hard to predict
        for attempt in range(100):  # Limit attempts to prevent timeout
            orientation = random.choice(['horizontal', 'vertical'])

            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)

            # Check if placement is valid
            valid = True
            if orientation == 'horizontal':
                for c in range(col, col + ship_length):
                    if my_board[row][c] != EMPTY:
                        valid = False
                        break
            else:
                for r in range(row, row + ship_length):
                    if my_board[r][col] != EMPTY:
                        valid = False
                        break

            if valid:
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }

        # Fallback to random placement if we can't find a valid spot
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

    def _bomb(self, state):
        # Initialize or update tracking structures
        self._update_shot_history(state['shot_history'])

        # Check if we have potential targets to follow up on
        if self.target_queue:
            target = self.target_queue.popleft()
            while target in self.shot_history:
                if not self.target_queue:
                    break
                target = self.target_queue.popleft()
            if target not in self.shot_history:
                return {'target': target}

        # If we're in hunt mode, use probability-based targeting
        if self.hunt_mode:
            target = self._probability_target(state)
        else:
            # If we're in target mode but queue is empty, switch to hunt mode
            target = self._probability_target(state)
            self.hunt_mode = True

        return {'target': target}

    def _update_shot_history(self, shot_history):
        for shot in shot_history:
            coord = shot['coord']
            self.shot_history.add(coord)
            if shot['result'] == 'HIT':
                self.hit_history.add(coord)
                self.last_hit = coord
                self.hunt_mode = False

    def _probability_target(self, state):
        # Create a probability grid
        prob_grid = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]

        # For each remaining ship, calculate possible positions
        for ship_size in self.remaining_ships:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    # Check horizontal placement
                    if col + ship_size <= self.board_size:
                        valid = True
                        for c in range(col, col + ship_size):
                            if (row, c) in self.shot_history:
                                valid = False
                                break
                        if valid:
                            for c in range(col, col + ship_size):
                                prob_grid[row][c] += 1

                    # Check vertical placement
                    if row + ship_size <= self.board_size:
                        valid = True
                        for r in range(row, row + ship_size):
                            if (r, col) in self.shot_history:
                                valid = False
                                break
                        if valid:
                            for r in range(row, row + ship_size):
                                prob_grid[r][col] += 1

        # Find the cell with highest probability that hasn't been shot yet
        max_prob = 0
        best_targets = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.shot_history and prob_grid[row][col] > max_prob:
                    max_prob = prob_grid[row][col]
                    best_targets = [(row, col)]
                elif (row, col) not in self.shot_history and prob_grid[row][col] == max_prob:
                    best_targets.append((row, col))

        # If we have a last hit, prioritize adjacent cells
        if self.last_hit and not self.hunt_mode:
            last_row, last_col = self.last_hit
            adjacent = [
                (last_row - 1, last_col),
                (last_row + 1, last_col),
                (last_row, last_col - 1),
                (last_row, last_col + 1)
            ]
            valid_adjacent = []
            for coord in adjacent:
                if (0 <= coord[0] < self.board_size and
                    0 <= coord[1] < self.board_size and
                    coord not in self.shot_history):
                    valid_adjacent.append(coord)

            if valid_adjacent:
                return {'target': random.choice(valid_adjacent)}

        # If we have potential targets from previous hits, use those
        if self.potential_targets:
            target = random.choice(list(self.potential_targets))
            self.potential_targets.remove(target)
            return {'target': target}

        # Otherwise, choose randomly from best probability targets
        if best_targets:
            return {'target': random.choice(best_targets)}

        # Fallback to random if no good targets found
        while True:
            target = (random.randint(0, self.board_size-1),
                      random.randint(0, self.board_size-1))
            if target not in self.shot_history:
                return {'target': target}

    def _check_sunk_ship(self, state):
        # This would be called after a hit to check if a ship was sunk
        # For simplicity, we'll just track remaining ships
        pass
