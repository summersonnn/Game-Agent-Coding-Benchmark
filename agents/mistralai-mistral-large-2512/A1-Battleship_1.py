"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 1
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
        self.opponent_board = [[EMPTY for _ in range(board_size)] for _ in range(board_size)]
        self.target_queue = deque()
        self.hunt_mode = True
        self.last_hit = None
        self.potential_targets = []
        self.ship_sizes = sorted(ships)
        self.remaining_ships = set(ships)

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state, feedback)
        else:
            return self._bomb_opponent(state)

    def _place_ship(self, state, feedback):
        if feedback and 'error_code' in feedback:
            # If we got an error, try to adjust our placement
            if feedback['attempt_number'] < MAX_PLACEMENT_ATTEMPTS:
                return self._adjusted_placement(state, feedback)

        # First attempt for this ship
        ship_length = state['ships_to_place'][0]
        return self._smart_placement(ship_length)

    def _smart_placement(self, ship_length):
        # Try to place ships in a pattern that's harder to hit
        # Prefer edges and corners for larger ships
        best_score = -1
        best_placement = None

        for _ in range(100):  # Try multiple random placements and pick the best
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)

            # Score the placement
            score = self._score_placement(row, col, orientation, ship_length)
            if score > best_score:
                best_score = score
                best_placement = {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }

        return best_placement if best_placement else self._random_placement(ship_length)

    def _score_placement(self, row, col, orientation, ship_length):
        # Higher score means better placement
        score = 0

        # Prefer edges and corners
        if row == 0 or row == self.board_size - 1:
            score += 2
        if col == 0 or col == self.board_size - 1:
            score += 2

        # Avoid placing near other ships
        for i in range(ship_length):
            if orientation == 'horizontal':
                r, c = row, col + i
            else:
                r, c = row + i, col

            # Check adjacent cells
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if 0 <= r + dr < self.board_size and 0 <= c + dc < self.board_size:
                        if self.my_board[r + dr][c + dc] == SHIP:
                            score -= 3  # Penalize being near other ships

        # Prefer larger ships in more protected positions
        score += ship_length * 0.5

        return score

    def _adjusted_placement(self, state, feedback):
        ship_length = state['ships_to_place'][0]
        error = feedback['error_code']

        if error == 'OUT_OF_BOUNDS':
            # Try to place more centrally
            if feedback['attempted_placement']['orientation'] == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length - 1)
            else:
                row = random.randint(0, self.board_size - ship_length - 1)
                col = random.randint(0, self.board_size - 1)
        elif error == 'SHIP_INTERSECTION':
            # Try to place in a different area
            return self._smart_placement(ship_length)
        else:
            # Fallback to random placement
            return self._random_placement(ship_length)

        return {
            'ship_length': ship_length,
            'start': (row, col),
            'orientation': feedback['attempted_placement']['orientation']
        }

    def _random_placement(self, ship_length):
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

    def _bomb_opponent(self, state):
        # Update our knowledge of the opponent's board
        self._update_opponent_board(state)

        # If we're in target mode (we have a hit we're trying to sink)
        if not self.hunt_mode and self.potential_targets:
            target = self.potential_targets.pop(0)
            if self.opponent_board[target[0]][target[1]] == EMPTY:
                return {'target': target}

        # If we have a hit but no potential targets, generate new ones
        if not self.hunt_mode and not self.potential_targets and self.last_hit:
            self._generate_potential_targets()
            if self.potential_targets:
                target = self.potential_targets.pop(0)
                return {'target': target}

        # Hunt mode - look for new ships
        target = self._hunt_mode_target()
        return {'target': target}

    def _update_opponent_board(self, state):
        if state['last_shot_coord']:
            row, col = state['last_shot_coord']
            if state['last_shot_result'] == 'HIT':
                self.opponent_board[row][col] = HIT
                self.last_hit = (row, col)
                self.hunt_mode = False
                self._generate_potential_targets()
            else:
                self.opponent_board[row][col] = MISS

        # Check if we've sunk a ship
        if not state['turn_continues'] and state['last_shot_result'] == 'HIT':
            self._check_sunk_ship()

    def _generate_potential_targets(self):
        if not self.last_hit:
            return

        row, col = self.last_hit
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        # Clear existing potential targets
        self.potential_targets = []

        # Generate targets in all four directions
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.opponent_board[r][c] == EMPTY:
                    self.potential_targets.append((r, c))
                elif self.opponent_board[r][c] == MISS:
                    break  # Stop if we hit a miss
                r += dr
                c += dc

        # Shuffle to randomize direction priority
        random.shuffle(self.potential_targets)

    def _check_sunk_ship(self):
        # Check if we've sunk a ship by looking for contiguous hits
        # This is simplified - a more complete implementation would track ship sizes
        if not self.last_hit:
            return

        row, col = self.last_hit
        directions = [(0, 1), (1, 0)]
        for dr, dc in directions:
            length = 1
            # Check in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.opponent_board[r][c] == HIT:
                length += 1
                r += dr
                c += dc

            # Check in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.opponent_board[r][c] == HIT:
                length += 1
                r -= dr
                c -= dc

            # If we found a ship of known size, mark it as sunk
            if length in self.remaining_ships:
                self.remaining_ships.remove(length)
                self.hunt_mode = True
                self.last_hit = None
                self.potential_targets = []
                return

    def _hunt_mode_target(self):
        # Probability-based targeting
        # Create a probability grid based on remaining ship sizes
        prob_grid = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]

        for ship_size in self.remaining_ships:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    # Check horizontal placement
                    if col + ship_size <= self.board_size:
                        valid = True
                        for c in range(col, col + ship_size):
                            if self.opponent_board[row][c] != EMPTY:
                                valid = False
                                break
                        if valid:
                            for c in range(col, col + ship_size):
                                prob_grid[row][c] += 1

                    # Check vertical placement
                    if row + ship_size <= self.board_size:
                        valid = True
                        for r in range(row, row + ship_size):
                            if self.opponent_board[r][col] != EMPTY:
                                valid = False
                                break
                        if valid:
                            for r in range(row, row + ship_size):
                                prob_grid[r][col] += 1

        # Find the cell with highest probability
        max_prob = -1
        best_targets = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.opponent_board[row][col] == EMPTY:
                    if prob_grid[row][col] > max_prob:
                        max_prob = prob_grid[row][col]
                        best_targets = [(row, col)]
                    elif prob_grid[row][col] == max_prob:
                        best_targets.append((row, col))

        # If multiple cells have same probability, choose randomly
        if best_targets:
            return random.choice(best_targets)

        # Fallback to random if no good targets found
        return self._random_target()

    def _random_target(self):
        # Find all empty cells
        empty_cells = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.opponent_board[row][col] == EMPTY:
                    empty_cells.append((row, col))

        return random.choice(empty_cells) if empty_cells else (0, 0)
