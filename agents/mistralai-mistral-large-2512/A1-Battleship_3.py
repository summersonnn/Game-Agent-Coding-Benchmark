"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 3
Generated: 2026-02-04 16:48:07
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Smart Battleship agent that uses probability-based targeting and hunt-and-target strategy.
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = sorted(ships_config, reverse=True)
        self.remaining_ships = ships_config.copy()

        # Initialize all possible moves
        self.all_moves = set()
        for r in range(board_size):
            for c in range(board_size):
                self.all_moves.add((r, c))

        # For hunt mode (probability targeting)
        self.prob_board = [[0 for _ in range(board_size)] for _ in range(board_size)]
        self._initialize_prob_board()

        # For target mode (after hitting a ship)
        self.target_queue = deque()
        self.current_target_ship = None
        self.hit_coords = set()
        self.sunk_ships = []

    def _initialize_prob_board(self):
        """Initialize probability board based on ship sizes"""
        for length in self.ships_config:
            for r in range(self.board_size):
                for c in range(self.board_size):
                    # Horizontal placement
                    if c + length <= self.board_size:
                        valid = True
                        for i in range(length):
                            if (r, c + i) in self.hit_coords or (r, c + i) in self.sunk_ships:
                                valid = False
                                break
                        if valid:
                            for i in range(length):
                                self.prob_board[r][c + i] += 1

                    # Vertical placement
                    if r + length <= self.board_size:
                        valid = True
                        for i in range(length):
                            if (r + i, c) in self.hit_coords or (r + i, c) in self.sunk_ships:
                                valid = False
                                break
                        if valid:
                            for i in range(length):
                                self.prob_board[r + i][c] += 1

    def _update_prob_board(self, coord, is_hit):
        """Update probability board after a move"""
        r, c = coord
        if is_hit:
            # If it's a hit, we don't need to update probabilities for this cell
            # But we need to update for adjacent cells
            self.prob_board[r][c] = 0
            # Check adjacent cells for potential ship placements
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    self.prob_board[nr][nc] = 0  # Reset probability
                    # Recalculate probability for this cell based on remaining ships
                    for length in self.remaining_ships:
                        # Check horizontal
                        if nc + length <= self.board_size:
                            valid = True
                            for i in range(length):
                                if (nr, nc + i) in self.hit_coords or (nr, nc + i) in self.sunk_ships:
                                    valid = False
                                    break
                            if valid:
                                self.prob_board[nr][nc] += 1

                        # Check vertical
                        if nr + length <= self.board_size:
                            valid = True
                            for i in range(length):
                                if (nr + i, nc) in self.hit_coords or (nr + i, nc) in self.sunk_ships:
                                    valid = False
                                    break
                            if valid:
                                self.prob_board[nr][nc] += 1
        else:
            # If it's a miss, set probability to 0
            self.prob_board[r][c] = 0

    def _get_highest_prob_coords(self):
        """Get coordinates with highest probability"""
        max_prob = max(max(row) for row in self.prob_board)
        if max_prob == 0:
            # Fallback to random if no probabilities left
            return random.choice(list(self.all_moves))

        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.prob_board[r][c] == max_prob:
                    candidates.append((r, c))
        return random.choice(candidates)

    def _get_adjacent_coords(self, coord):
        """Get valid adjacent coordinates for targeting"""
        r, c = coord
        adjacent = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) in self.all_moves:
                adjacent.append((nr, nc))
        return adjacent

    def _check_ship_sunk(self, coord):
        """Check if a ship has been sunk and return its coordinates if so"""
        r, c = coord
        # Check horizontal
        ship_coords = [(r, c)]
        # Left
        for dc in range(1, c + 1):
            if self.prob_board[r][c - dc] == 0 and (r, c - dc) not in self.hit_coords:
                break
            ship_coords.append((r, c - dc))
        # Right
        for dc in range(1, self.board_size - c):
            if self.prob_board[r][c + dc] == 0 and (r, c + dc) not in self.hit_coords:
                break
            ship_coords.append((r, c + dc))

        if len(ship_coords) >= 2:
            # Check if all parts of this potential ship are hit
            all_hit = all((coord in self.hit_coords or coord == (r, c)) for coord in ship_coords)
            if all_hit:
                # Find the actual ship length
                ship_length = len(ship_coords)
                if ship_length in self.remaining_ships:
                    self.remaining_ships.remove(ship_length)
                    return ship_coords

        # Check vertical
        ship_coords = [(r, c)]
        # Up
        for dr in range(1, r + 1):
            if self.prob_board[r - dr][c] == 0 and (r - dr, c) not in self.hit_coords:
                break
            ship_coords.append((r - dr, c))
        # Down
        for dr in range(1, self.board_size - r):
            if self.prob_board[r + dr][c] == 0 and (r + dr, c) not in self.hit_coords:
                break
            ship_coords.append((r + dr, c))

        if len(ship_coords) >= 2:
            # Check if all parts of this potential ship are hit
            all_hit = all((coord in self.hit_coords or coord == (r, c)) for coord in ship_coords)
            if all_hit:
                # Find the actual ship length
                ship_length = len(ship_coords)
                if ship_length in self.remaining_ships:
                    self.remaining_ships.remove(ship_length)
                    return ship_coords

        return []

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Return a tuple: ((row, col), sunk_coords)
        - (row, col): The cell to bomb (0-indexed)
        - sunk_coords: List of coordinates if you've sunk a ship, else []
        """
        sunk_coords = []

        # If we have a hit from last move, check if we sunk a ship
        if last_shot_result == 'HIT':
            self.hit_coords.add(last_shot_coord)
            sunk_coords = self._check_ship_sunk(last_shot_coord)
            if sunk_coords:
                self.sunk_ships.extend(sunk_coords)
                self.hit_coords.difference_update(sunk_coords)
                self.target_queue.clear()
                self._initialize_prob_board()
            else:
                # Add adjacent cells to target queue
                adjacent = self._get_adjacent_coords(last_shot_coord)
                for coord in adjacent:
                    if coord not in self.target_queue:
                        self.target_queue.append(coord)

        # If we have targets in queue, use them first
        if self.target_queue:
            move = self.target_queue.popleft()
        else:
            # Otherwise, use probability-based targeting
            move = self._get_highest_prob_coords()

        # Remove move from available moves
        self.all_moves.discard(move)

        # Update probability board based on last move
        if last_shot_coord is not None:
            self._update_prob_board(last_shot_coord, last_shot_result == 'HIT')

        return move, sunk_coords
