"""
Agent Code: A1-Battleship
Model: mistralai/mistral-large-2512
Run: 4
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
        self.moves_queue = deque()
        self.hunt_mode = True
        self.target_queue = deque()
        self.last_hits = []
        self.probability_board = [[0 for _ in range(board_size)] for _ in range(board_size)]
        self.initialize_probability_board()

    def initialize_probability_board(self):
        """Initialize probability board based on ship sizes"""
        for length in self.ships_config:
            for r in range(self.board_size):
                for c in range(self.board_size):
                    # Horizontal placement
                    if c + length <= self.board_size:
                        self.probability_board[r][c] += 1
                    # Vertical placement
                    if r + length <= self.board_size:
                        self.probability_board[r][c] += 1

    def update_probability_board(self, row, col, result):
        """Update probability board after a shot"""
        if result == 'MISS':
            # Reduce probability for adjacent cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    self.probability_board[nr][nc] = max(0, self.probability_board[nr][nc] - 1)

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        sunk_coords = []

        # If we're in target mode and have potential targets
        if not self.hunt_mode and self.target_queue:
            row, col = self.target_queue.popleft()
            if not self.target_queue:
                self.hunt_mode = True
            return (row, col), sunk_coords

        # If we got a hit last turn, switch to target mode
        if last_shot_result == 'HIT':
            self.hunt_mode = False
            row, col = last_shot_coord
            self.last_hits.append((row, col))

            # Add adjacent cells to target queue
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if (nr, nc) in self.all_moves:
                        self.target_queue.append((nr, nc))

            # If we have multiple hits, try to find the ship orientation
            if len(self.last_hits) >= 2:
                self.target_queue.clear()
                # Sort hits by row and column
                hits = sorted(self.last_hits)
                # Check if horizontal or vertical
                if hits[0][0] == hits[1][0]:  # Horizontal
                    row = hits[0][0]
                    # Find leftmost and rightmost hits
                    min_col = min(h[1] for h in hits)
                    max_col = max(h[1] for h in hits)
                    # Add cells to the left and right
                    if min_col - 1 >= 0 and (row, min_col - 1) in self.all_moves:
                        self.target_queue.append((row, min_col - 1))
                    if max_col + 1 < self.board_size and (row, max_col + 1) in self.all_moves:
                        self.target_queue.append((row, max_col + 1))
                else:  # Vertical
                    col = hits[0][1]
                    # Find top and bottom hits
                    min_row = min(h[0] for h in hits)
                    max_row = max(h[0] for h in hits)
                    # Add cells above and below
                    if min_row - 1 >= 0 and (min_row - 1, col) in self.all_moves:
                        self.target_queue.append((min_row - 1, col))
                    if max_row + 1 < self.board_size and (max_row + 1, col) in self.all_moves:
                        self.target_queue.append((max_row + 1, col))

        # If we're in hunt mode, use probability-based targeting
        if self.hunt_mode:
            # Find the cell with highest probability that's still available
            max_prob = -1
            candidates = []
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if (r, c) in self.all_moves and self.probability_board[r][c] > max_prob:
                        max_prob = self.probability_board[r][c]
                        candidates = [(r, c)]
                    elif (r, c) in self.all_moves and self.probability_board[r][c] == max_prob:
                        candidates.append((r, c))

            if candidates:
                row, col = random.choice(candidates)
            else:
                # Fallback to random move if no candidates found
                row, col = random.choice(self.all_moves)

        # Remove the chosen move from available moves
        if (row, col) in self.all_moves:
            self.all_moves.remove((row, col))

        return (row, col), sunk_coords
