"""
Agent Code: A1-Battleship
Model: x-ai/grok-code-fast-1
Run: 2
Generated: 2026-02-11 19:20:19
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    BattleshipAgent with smart placement and bombing strategies.
    - Placement: Tries random valid placements; if none found, defaults to invalid (penalty will apply).
    - Bombing: Uses hunt-and-target with parity search pattern for efficiency.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.opponent_board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]  # None, 'HIT', 'MISS'
        self.target_queue = deque()  # Queue for adjacent targets after a hit
        self.search_pattern = self._generate_search_pattern()  # Parity-based search order
        self.search_index = 0

    def _generate_search_pattern(self):
        """Generates a search pattern prioritizing even sum cells, then odd."""
        pattern = []
        for parity in [0, 1]:  # 0 for even sum, 1 for odd sum
            for i in range(self.board_size):
                for j in range(self.board_size):
                    if (i + j) % 2 == parity:
                        pattern.append((i, j))
        return pattern

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            my_board = state['my_board']
            # Try random valid placements
            for _ in range(100):
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                # Check for overlap
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
            # Fallback: invalid placement, penalty will apply
            return {
                'ship_length': ship_length,
                'start': (0, 0),
                'orientation': 'horizontal'
            }
        else:  # bombing phase
            # Update based on last shot
            if state['last_shot_coord'] is not None:
                row, col = state['last_shot_coord']
                result = state['last_shot_result']
                self.opponent_board[row][col] = result
                if result == 'HIT':
                    # Add adjacent cells to target queue if not already shot and not in queue
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dr, dc in directions:
                        nr, nc = row + dr, col + dc
                        if (0 <= nr < self.board_size and 0 <= nc < self.board_size 
                            and self.opponent_board[nr][nc] is None and (nr, nc) not in self.target_queue):
                            self.target_queue.append((nr, nc))
            # Choose target
            if self.target_queue:
                target = self.target_queue.popleft()
            else:
                if self.search_index < len(self.search_pattern):
                    target = self.search_pattern[self.search_index]
                    self.search_index += 1
                else:
                    # Fallback, though unlikely
                    target = (0, 0)
            return {'target': target}
