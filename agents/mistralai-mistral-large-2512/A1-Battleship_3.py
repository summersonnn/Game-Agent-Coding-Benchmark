"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 3
Generated: 2026-02-17 12:25:21
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.target_queue = deque()
        self.hunt_mode = True
        self.last_hits = []
        self.possible_orientations = ['horizontal', 'vertical']
        self.shot_history = set()
        self.probability_grid = [[0 for _ in range(board_size)] for _ in range(board_size)]
        self.remaining_ships = ships.copy()

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb_target(state)

    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']

        # Try to place ships in a way that minimizes clustering
        best_placement = None
        best_score = -float('inf')

        for _ in range(100):  # Try multiple random placements
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
                    if my_board[row][c] != 'O':
                        valid = False
                        break
            else:
                for r in range(row, row + ship_length):
                    if my_board[r][col] != 'O':
                        valid = False
                        break

            if not valid:
                continue

            # Score the placement based on distance from other ships
            score = self._score_placement(my_board, row, col, ship_length, orientation)
            if score > best_score:
                best_score = score
                best_placement = {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }

        if best_placement is None:
            # Fallback to random valid placement
            while True:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)

                valid = True
                if orientation == 'horizontal':
                    for c in range(col, col + ship_length):
                        if my_board[row][c] != 'O':
                            valid = False
                            break
                else:
                    for r in range(row, row + ship_length):
                        if my_board[r][col] != 'O':
                            valid = False
                            break

                if valid:
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': orientation
                    }

        return best_placement

    def _score_placement(self, board, row, col, length, orientation):
        score = 0
        # Check surrounding cells to avoid clustering
        if orientation == 'horizontal':
            for c in range(col, col + length):
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        r, c = row + dr, c + dc
                        if 0 <= r < self.board_size and 0 <= c < self.board_size:
                            if board[r][c] == 'S':
                                score -= 10  # Penalize being near other ships
        else:
            for r in range(row, row + length):
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        r, c = r + dr, col + dc
                        if 0 <= r < self.board_size and 0 <= c < self.board_size:
                            if board[r][c] == 'S':
                                score -= 10  # Penalize being near other ships

        # Prefer center placement
        center = self.board_size // 2
        distance_to_center = abs(row - center) + abs(col - center)
        score -= distance_to_center

        return score

    def _bomb_target(self, state):
        # Update shot history
        self.shot_history = set()
        for shot in state['shot_history']:
            self.shot_history.add(shot['coord'])

        # Update remaining ships based on hit patterns
        self._update_remaining_ships(state)

        # If we have a target queue, use it (target mode)
        if self.target_queue:
            target = self.target_queue.popleft()
            while target in self.shot_history:
                if not self.target_queue:
                    self.hunt_mode = True
                    break
                target = self.target_queue.popleft()
            if target not in self.shot_history:
                return {'target': target}

        # If we're in hunt mode, use probability targeting
        if self.hunt_mode:
            self._calculate_probability_grid()
            target = self._get_highest_probability_target()
            return {'target': target}
        else:
            # Shouldn't reach here if target_queue is properly managed
            target = random.choice(list(self._get_valid_targets()))
            return {'target': target}

    def _update_remaining_ships(self, state):
        # Simple implementation - just track hits
        # More sophisticated implementation would track sunk ships
        pass

    def _calculate_probability_grid(self):
        # Reset probability grid
        self.probability_grid = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]

        # Calculate probabilities for each remaining ship
        for ship_length in self.remaining_ships:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    # Horizontal placement
                    if col + ship_length <= self.board_size:
                        valid = True
                        for c in range(col, col + ship_length):
                            if (row, c) in self.shot_history:
                                valid = False
                                break
                        if valid:
                            for c in range(col, col + ship_length):
                                self.probability_grid[row][c] += 1

                    # Vertical placement
                    if row + ship_length <= self.board_size:
                        valid = True
                        for r in range(row, row + ship_length):
                            if (r, col) in self.shot_history:
                                valid = False
                                break
                        if valid:
                            for r in range(row, row + ship_length):
                                self.probability_grid[r][col] += 1

    def _get_highest_probability_target(self):
        max_prob = -1
        best_targets = []

        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.shot_history:
                    if self.probability_grid[row][col] > max_prob:
                        max_prob = self.probability_grid[row][col]
                        best_targets = [(row, col)]
                    elif self.probability_grid[row][col] == max_prob:
                        best_targets.append((row, col))

        if not best_targets:
            return random.choice(list(self._get_valid_targets()))
        return random.choice(best_targets)

    def _get_valid_targets(self):
        valid_targets = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.shot_history:
                    valid_targets.append((row, col))
        return valid_targets

    def _handle_hit(self, coord):
        self.hunt_mode = False
        self.last_hits.append(coord)

        # Add adjacent cells to target queue
        row, col = coord
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size and (r, c) not in self.shot_history:
                self.target_queue.append((r, c))

        # If we have multiple hits, try to determine ship orientation
        if len(self.last_hits) >= 2:
            self._determine_ship_orientation()

    def _determine_ship_orientation(self):
        if len(self.last_hits) < 2:
            return

        # Get the last two hits
        hit1 = self.last_hits[-2]
        hit2 = self.last_hits[-1]

        # Check if they're in a straight line
        if hit1[0] == hit2[0]:  # Same row - horizontal
            row = hit1[0]
            col1, col2 = sorted([hit1[1], hit2[1]])
            # Add cells to the left and right
            for c in range(col1 - 1, -1, -1):
                if (row, c) not in self.shot_history:
                    self.target_queue.appendleft((row, c))
                else:
                    break
            for c in range(col2 + 1, self.board_size):
                if (row, c) not in self.shot_history:
                    self.target_queue.appendleft((row, c))
                else:
                    break
        elif hit1[1] == hit2[1]:  # Same column - vertical
            col = hit1[1]
            row1, row2 = sorted([hit1[0], hit2[0]])
            # Add cells above and below
            for r in range(row1 - 1, -1, -1):
                if (r, col) not in self.shot_history:
                    self.target_queue.appendleft((r, col))
                else:
                    break
            for r in range(row2 + 1, self.board_size):
                if (r, col) not in self.shot_history:
                    self.target_queue.appendleft((r, col))
                else:
                    break
