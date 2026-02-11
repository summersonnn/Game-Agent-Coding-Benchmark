"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 1
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
        self.placement_attempts = {}
        self.hit_queue = deque()
        self.potential_targets = set()
        self.shot_history = set()
        self.last_hits = []
        self.ship_sizes = sorted(ships, reverse=True)
        self.remaining_ships = self.ship_sizes.copy()

        # Initialize potential targets for bombing phase
        for i in range(board_size):
            for j in range(board_size):
                self.potential_targets.add((i, j))

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb_target(state)

    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']

        # Try to place ships in a pattern that's hard to predict
        best_placement = None
        best_score = -1

        # Try several random placements and pick the best one
        for _ in range(50):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)

            # Check if placement is valid
            if self._is_valid_placement(my_board, ship_length, (row, col), orientation):
                # Score the placement based on how "hidden" it is
                score = self._score_placement(my_board, ship_length, (row, col), orientation)
                if score > best_score:
                    best_score = score
                    best_placement = {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': orientation
                    }

        # If we found a good placement, use it; otherwise fall back to random
        if best_placement:
            return best_placement
        else:
            # Fallback to random valid placement
            while True:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)

                if self._is_valid_placement(my_board, ship_length, (row, col), orientation):
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
            for c in range(col, col + ship_length):
                if board[row][c] != 'O':
                    return False
                # Check adjacent cells
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        r, c_check = row + dr, c + dc
                        if 0 <= r < self.board_size and 0 <= c_check < self.board_size:
                            if board[r][c_check] == 'S':
                                return False
        else:  # vertical
            if row + ship_length > self.board_size:
                return False
            for r in range(row, row + ship_length):
                if board[r][col] != 'O':
                    return False
                # Check adjacent cells
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        r_check, c = r + dr, col + dc
                        if 0 <= r_check < self.board_size and 0 <= c < self.board_size:
                            if board[r_check][c] == 'S':
                                return False
        return True

    def _score_placement(self, board, ship_length, start, orientation):
        row, col = start
        score = 0

        # Prefer placements that are not along edges
        if orientation == 'horizontal':
            if row == 0 or row == self.board_size - 1:
                score -= 10
            if col == 0 or col + ship_length == self.board_size:
                score -= 5
        else:  # vertical
            if col == 0 or col == self.board_size - 1:
                score -= 10
            if row == 0 or row + ship_length == self.board_size:
                score -= 5

        # Prefer placements that are not adjacent to other ships
        if orientation == 'horizontal':
            for c in range(col, col + ship_length):
                for dr in [-1, 1]:
                    r = row + dr
                    if 0 <= r < self.board_size:
                        if board[r][c] == 'S':
                            score -= 20
                for dc in [-1, 1]:
                    c_check = c + dc
                    if 0 <= c_check < self.board_size:
                        if board[row][c_check] == 'S':
                            score -= 20
        else:  # vertical
            for r in range(row, row + ship_length):
                for dc in [-1, 1]:
                    c = col + dc
                    if 0 <= c < self.board_size:
                        if board[r][c] == 'S':
                            score -= 20
                for dr in [-1, 1]:
                    r_check = r + dr
                    if 0 <= r_check < self.board_size:
                        if board[r_check][col] == 'S':
                            score -= 20

        return score

    def _bomb_target(self, state):
        # Update shot history
        self.shot_history = {tuple(shot['coord']) for shot in state['shot_history']}

        # Check if we have any hits that need follow-up
        if state['last_shot_result'] == 'HIT' and state['turn_continues']:
            last_hit = state['last_shot_coord']
            self.last_hits.append(last_hit)

            # Add adjacent cells to hit queue
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                r, c = last_hit[0] + dr, last_hit[1] + dc
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if (r, c) not in self.shot_history:
                        self.hit_queue.append((r, c))

        # If we have hits in queue, prioritize them
        if self.hit_queue:
            target = self.hit_queue.popleft()
            while target in self.shot_history:
                if not self.hit_queue:
                    target = None
                    break
                target = self.hit_queue.popleft()
            if target:
                return {'target': target}

        # If we have recent hits, try to find the ship direction
        if len(self.last_hits) >= 2:
            # Try to determine ship orientation
            hits = sorted(self.last_hits)
            if hits[0][0] == hits[1][0]:  # horizontal
                row = hits[0][0]
                cols = sorted([h[1] for h in hits])
                # Try to extend in both directions
                for dc in [-1, 1]:
                    c = cols[-1] + dc if dc == 1 else cols[0] + dc
                    if 0 <= c < self.board_size and (row, c) not in self.shot_history:
                        return {'target': (row, c)}
            else:  # vertical
                col = hits[0][1]
                rows = sorted([h[0] for h in hits])
                # Try to extend in both directions
                for dr in [-1, 1]:
                    r = rows[-1] + dr if dr == 1 else rows[0] + dr
                    if 0 <= r < self.board_size and (r, col) not in self.shot_history:
                        return {'target': (r, col)}

        # If no hits to follow up, use probability-based targeting
        target = self._find_best_target(state)
        return {'target': target}

    def _find_best_target(self, state):
        # Create a probability grid
        prob_grid = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]

        # For each remaining ship, calculate possible positions
        for ship_size in self.remaining_ships:
            for i in range(self.board_size):
                for j in range(self.board_size - ship_size + 1):
                    # Check horizontal placement
                    if all((i, j + k) not in self.shot_history for k in range(ship_size)):
                        valid = True
                        for k in range(ship_size):
                            if state['shot_history'] and any(
                                (i, j + k) == tuple(shot['coord']) and shot['result'] == 'HIT'
                                for shot in state['shot_history']
                            ):
                                valid = False
                                break
                        if valid:
                            for k in range(ship_size):
                                prob_grid[i][j + k] += 1

                    # Check vertical placement
                    if all((i + k, j) not in self.shot_history for k in range(ship_size)):
                        valid = True
                        for k in range(ship_size):
                            if state['shot_history'] and any(
                                (i + k, j) == tuple(shot['coord']) and shot['result'] == 'HIT'
                                for shot in state['shot_history']
                            ):
                                valid = False
                                break
                        if valid:
                            for k in range(ship_size):
                                prob_grid[i + k][j] += 1

        # Find the cell with highest probability
        max_prob = -1
        best_targets = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if (i, j) not in self.shot_history and prob_grid[i][j] > max_prob:
                    max_prob = prob_grid[i][j]
                    best_targets = [(i, j)]
                elif (i, j) not in self.shot_history and prob_grid[i][j] == max_prob:
                    best_targets.append((i, j))

        # If multiple targets have same probability, choose one randomly
        if best_targets:
            return random.choice(best_targets)

        # Fallback to random if no good target found
        available_targets = [(i, j) for i in range(self.board_size)
                            for j in range(self.board_size)
                            if (i, j) not in self.shot_history]
        return random.choice(available_targets) if available_targets else (0, 0)
