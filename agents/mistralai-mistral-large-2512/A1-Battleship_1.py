"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 1
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
        self.untargeted_cells = set()
        self.target_queue = deque()
        self.hunt_mode = True
        self.last_hit = None
        self.potential_targets = set()
        self.guess_board = [[EMPTY for _ in range(board_size)] for _ in range(board_size)]

        # Initialize all possible cells
        for row in range(board_size):
            for col in range(board_size):
                self.untargeted_cells.add((row, col))

        # Precompute ship probabilities
        self.probability_board = [[0 for _ in range(board_size)] for _ in range(board_size)]
        self._initialize_probability_board()

    def _initialize_probability_board(self):
        """Initialize probability board based on ship sizes"""
        for length in self.ships_config:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    # Check horizontal placement
                    if col + length <= self.board_size:
                        valid = True
                        for i in range(length):
                            if self.guess_board[row][col + i] != EMPTY:
                                valid = False
                                break
                        if valid:
                            for i in range(length):
                                self.probability_board[row][col + i] += 1

                    # Check vertical placement
                    if row + length <= self.board_size:
                        valid = True
                        for i in range(length):
                            if self.guess_board[row + i][col] != EMPTY:
                                valid = False
                                break
                        if valid:
                            for i in range(length):
                                self.probability_board[row + i][col] += 1

    def _update_probability_board(self, row, col, result):
        """Update probability board after a shot"""
        # Mark the cell as hit or miss
        self.guess_board[row][col] = result

        # Recalculate probabilities
        self.probability_board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        for length in self.remaining_ships:
            for r in range(self.board_size):
                for c in range(self.board_size):
                    # Check horizontal placement
                    if c + length <= self.board_size:
                        valid = True
                        for i in range(length):
                            if self.guess_board[r][c + i] == MISS:
                                valid = False
                                break
                        if valid:
                            for i in range(length):
                                if self.guess_board[r][c + i] == EMPTY:
                                    self.probability_board[r][c + i] += 1

                    # Check vertical placement
                    if r + length <= self.board_size:
                        valid = True
                        for i in range(length):
                            if self.guess_board[r + i][c] == MISS:
                                valid = False
                                break
                        if valid:
                            for i in range(length):
                                if self.guess_board[r + i][c] == EMPTY:
                                    self.probability_board[r + i][c] += 1

    def _get_high_probability_cells(self):
        """Get cells with highest probability of containing a ship"""
        max_prob = max(max(row) for row in self.probability_board)
        if max_prob == 0:
            return list(self.untargeted_cells)

        high_prob_cells = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.probability_board[row][col] == max_prob and self.guess_board[row][col] == EMPTY:
                    high_prob_cells.append((row, col))
        return high_prob_cells

    def _get_adjacent_cells(self, row, col):
        """Get valid adjacent cells for hunt mode"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        adjacent = []
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size and self.guess_board[r][c] == EMPTY:
                adjacent.append((r, c))
        return adjacent

    def _check_sunk_ship(self, row, col):
        """Check if a ship has been sunk and return its coordinates if so"""
        # Check horizontal
        ship_coords = [(row, col)]
        # Left
        c = col - 1
        while c >= 0 and self.guess_board[row][c] == HIT:
            ship_coords.append((row, c))
            c -= 1
        # Right
        c = col + 1
        while c < self.board_size and self.guess_board[row][c] == HIT:
            ship_coords.append((row, c))
            c += 1

        if len(ship_coords) > 1:
            # Check if all parts of the ship are hit
            all_hit = True
            for r, c in ship_coords:
                if self.guess_board[r][c] != HIT:
                    all_hit = False
                    break
            if all_hit:
                length = len(ship_coords)
                if length in self.remaining_ships:
                    self.remaining_ships.remove(length)
                    return ship_coords

        # Check vertical
        ship_coords = [(row, col)]
        # Up
        r = row - 1
        while r >= 0 and self.guess_board[r][col] == HIT:
            ship_coords.append((r, col))
            r -= 1
        # Down
        r = row + 1
        while r < self.board_size and self.guess_board[r][col] == HIT:
            ship_coords.append((r, col))
            r += 1

        if len(ship_coords) > 1:
            # Check if all parts of the ship are hit
            all_hit = True
            for r, c in ship_coords:
                if self.guess_board[r][c] != HIT:
                    all_hit = False
                    break
            if all_hit:
                length = len(ship_coords)
                if length in self.remaining_ships:
                    self.remaining_ships.remove(length)
                    return ship_coords

        return []

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        sunk_coords = []

        # If we're in hunt mode, use probability-based targeting
        if self.hunt_mode:
            # If we got a hit last turn, switch to target mode
            if last_shot_result == 'HIT':
                self.hunt_mode = False
                self.last_hit = last_shot_coord
                self.potential_targets = set(self._get_adjacent_cells(*last_shot_coord))
                # Filter out already targeted cells
                self.potential_targets = {cell for cell in self.potential_targets if cell in self.untargeted_cells}

            # Get highest probability cells
            high_prob_cells = self._get_high_probability_cells()
            if not high_prob_cells:
                # Fallback to random if no high probability cells
                cell = random.choice(list(self.untargeted_cells))
            else:
                cell = random.choice(high_prob_cells)

            row, col = cell
        else:
            # Target mode - try to sink the ship
            if not self.potential_targets:
                # No more potential targets, switch back to hunt mode
                self.hunt_mode = True
                return self.make_move(last_shot_result, last_shot_coord)

            # Get next potential target
            row, col = self.potential_targets.pop()

            # If this was our last potential target, switch back to hunt mode
            if not self.potential_targets:
                self.hunt_mode = True

        # Remove the cell from untargeted cells
        if (row, col) in self.untargeted_cells:
            self.untargeted_cells.remove((row, col))

        # Check if this shot sunk a ship
        if last_shot_result == 'HIT':
            sunk_coords = self._check_sunk_ship(*last_shot_coord)
            if sunk_coords:
                # Remove all cells of the sunk ship from potential targets
                for r, c in sunk_coords:
                    if (r, c) in self.potential_targets:
                        self.potential_targets.remove((r, c))
                # If we sunk a ship, switch back to hunt mode
                self.hunt_mode = True
                self.potential_targets = set()

        return (row, col), sunk_coords
