"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-04 16:48:07
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = sorted(ships_config, reverse=True)
        self.remaining_ships = self.ships_config.copy()

        # Initialize all possible moves
        self.all_moves = [(r, c) for r in range(board_size) for c in range(board_size)]
        self.missed_moves = set()
        self.hit_moves = set()
        self.sunk_ships = []

        # For tracking potential ship positions after hits
        self.hunt_queue = deque()
        self.hunt_mode = False
        self.current_hunt_targets = []
        self.last_hit_direction = None

        # Probability grid
        self.prob_grid = [[0 for _ in range(board_size)] for _ in range(board_size)]

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        sunk_coords = []

        # Update game state based on last shot result
        if last_shot_result == 'MISS':
            self.missed_moves.add(last_shot_coord)
            if self.hunt_mode and last_shot_coord in self.current_hunt_targets:
                self.current_hunt_targets.remove(last_shot_coord)
        elif last_shot_result == 'HIT':
            self.hit_moves.add(last_shot_coord)
            if not self.hunt_mode:
                self.hunt_mode = True
                self._initialize_hunt(last_shot_coord)
            else:
                self._update_hunt(last_shot_coord)

        # Check if we've sunk a ship
        if self.hunt_mode and self._check_sunk_ship():
            sunk_coords = self._get_sunk_coords()
            self.hunt_mode = False
            self.hunt_queue.clear()
            self.current_hunt_targets = []
            self.last_hit_direction = None
            self._update_remaining_ships()

        # Choose next move
        if self.hunt_mode and self.current_hunt_targets:
            # Hunt mode - target adjacent cells
            move = self.current_hunt_targets.pop(0)
        else:
            # Probability-based search
            self._calculate_probabilities()
            move = self._get_highest_probability_move()

            # If we're not in hunt mode, remove the move from possible moves
            if move in self.all_moves:
                self.all_moves.remove(move)

        return move, sunk_coords

    def _initialize_hunt(self, coord):
        r, c = coord
        # Add all adjacent cells to hunt queue
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                if (nr, nc) not in self.missed_moves and (nr, nc) not in self.hit_moves:
                    self.hunt_queue.append((nr, nc))

        # Initialize hunt targets with all possible directions
        self.current_hunt_targets = list(self.hunt_queue)

    def _update_hunt(self, coord):
        if not self.last_hit_direction:
            # Try to determine direction from last two hits
            if len(self.hit_moves) >= 2:
                hits = list(self.hit_moves)
                last_hit = hits[-1]
                prev_hit = hits[-2]

                dr = last_hit[0] - prev_hit[0]
                dc = last_hit[1] - prev_hit[1]

                if dr == 0:  # Horizontal
                    self.last_hit_direction = (0, 1 if dc > 0 else -1)
                elif dc == 0:  # Vertical
                    self.last_hit_direction = (1 if dr > 0 else -1, 0)

                # Update hunt targets based on direction
                if self.last_hit_direction:
                    self.current_hunt_targets = []
                    r, c = coord
                    dr, dc = self.last_hit_direction
                    # Add cells in both directions
                    for direction in [1, -1]:
                        nr, nc = r + dr * direction, c + dc * direction
                        while 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            if (nr, nc) in self.missed_moves:
                                break
                            if (nr, nc) not in self.hit_moves and (nr, nc) not in self.current_hunt_targets:
                                self.current_hunt_targets.append((nr, nc))
                            nr += dr * direction
                            nc += dc * direction

    def _check_sunk_ship(self):
        if not self.hunt_mode or len(self.hit_moves) < 2:
            return False

        # Check if we've found all parts of a ship
        hits = list(self.hit_moves)
        hits.sort()

        # Check horizontal ships
        for i in range(len(hits)):
            for ship_size in self.remaining_ships:
                if i + ship_size > len(hits):
                    continue
                # Check if consecutive hits form a ship
                consecutive = True
                for j in range(1, ship_size):
                    if hits[i+j][0] != hits[i][0] or hits[i+j][1] != hits[i][1] + j:
                        consecutive = False
                        break
                if consecutive:
                    # Verify all positions are hits
                    all_hits = True
                    for j in range(ship_size):
                        if hits[i+j] not in self.hit_moves:
                            all_hits = False
                            break
                    if all_hits:
                        return True

        # Check vertical ships
        hits.sort(key=lambda x: (x[1], x[0]))
        for i in range(len(hits)):
            for ship_size in self.remaining_ships:
                if i + ship_size > len(hits):
                    continue
                # Check if consecutive hits form a ship
                consecutive = True
                for j in range(1, ship_size):
                    if hits[i+j][1] != hits[i][1] or hits[i+j][0] != hits[i][0] + j:
                        consecutive = False
                        break
                if consecutive:
                    # Verify all positions are hits
                    all_hits = True
                    for j in range(ship_size):
                        if hits[i+j] not in self.hit_moves:
                            all_hits = False
                            break
                    if all_hits:
                        return True

        return False

    def _get_sunk_coords(self):
        if not self.hunt_mode:
            return []

        # Find the sunk ship coordinates
        hits = list(self.hit_moves)
        hits.sort()

        # Check horizontal ships
        for i in range(len(hits)):
            for ship_size in self.remaining_ships:
                if i + ship_size > len(hits):
                    continue
                consecutive = True
                for j in range(1, ship_size):
                    if hits[i+j][0] != hits[i][0] or hits[i+j][1] != hits[i][1] + j:
                        consecutive = False
                        break
                if consecutive:
                    coords = [(hits[i][0], hits[i][1] + j) for j in range(ship_size)]
                    if all(c in self.hit_moves for c in coords):
                        return coords

        # Check vertical ships
        hits.sort(key=lambda x: (x[1], x[0]))
        for i in range(len(hits)):
            for ship_size in self.remaining_ships:
                if i + ship_size > len(hits):
                    continue
                consecutive = True
                for j in range(1, ship_size):
                    if hits[i+j][1] != hits[i][1] or hits[i+j][0] != hits[i][0] + j:
                        consecutive = False
                        break
                if consecutive:
                    coords = [(hits[i][0] + j, hits[i][1]) for j in range(ship_size)]
                    if all(c in self.hit_moves for c in coords):
                        return coords

        return []

    def _update_remaining_ships(self):
        sunk_coords = self._get_sunk_coords()
        if not sunk_coords:
            return

        ship_size = len(sunk_coords)
        if ship_size in self.remaining_ships:
            self.remaining_ships.remove(ship_size)

    def _calculate_probabilities(self):
        # Reset probability grid
        self.prob_grid = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]

        # Calculate probabilities for each remaining ship
        for ship_size in self.remaining_ships:
            for r in range(self.board_size):
                for c in range(self.board_size):
                    # Horizontal placement
                    if c + ship_size <= self.board_size:
                        valid = True
                        for i in range(ship_size):
                            if (r, c + i) in self.missed_moves or (r, c + i) in self.hit_moves:
                                valid = False
                                break
                        if valid:
                            for i in range(ship_size):
                                if (r, c + i) not in self.hit_moves:
                                    self.prob_grid[r][c + i] += 1

                    # Vertical placement
                    if r + ship_size <= self.board_size:
                        valid = True
                        for i in range(ship_size):
                            if (r + i, c) in self.missed_moves or (r + i, c) in self.hit_moves:
                                valid = False
                                break
                        if valid:
                            for i in range(ship_size):
                                if (r + i, c) not in self.hit_moves:
                                    self.prob_grid[r + i][c] += 1

    def _get_highest_probability_move(self):
        max_prob = -1
        best_moves = []

        # Find all moves with maximum probability
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) in self.missed_moves or (r, c) in self.hit_moves:
                    continue
                if self.prob_grid[r][c] > max_prob:
                    max_prob = self.prob_grid[r][c]
                    best_moves = [(r, c)]
                elif self.prob_grid[r][c] == max_prob:
                    best_moves.append((r, c))

        # If no moves with probability > 0, use random move
        if max_prob == 0:
            valid_moves = [(r, c) for r in range(self.board_size) for c in range(self.board_size)
                          if (r, c) not in self.missed_moves and (r, c) not in self.hit_moves]
            if not valid_moves:
                return None
            return random.choice(valid_moves)

        # Choose randomly among best moves
        return random.choice(best_moves)
