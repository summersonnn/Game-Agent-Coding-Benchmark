"""
Agent Code: A1-Battleship
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-10 16:22:20
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Your agent implementation goes here.
    Implement smart placement and bombing logic to beat your opponent.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # For placement: no additional state needed beyond what's in state
        # For bombing
        self.opponent_board = [['?' for _ in range(board_size)] for _ in range(board_size)]  # '?' unknown, 'M' miss, 'H' hit
        self.hunting = True  # True for hunt mode, False for target mode
        self.hunt_queue = deque()  # queue of cells to check in target mode
        self.unshot = set((i, j) for i in range(board_size) for j in range(board_size))

    def _is_valid_placement(self, board, length, row, col, orient):
        if orient == 'horizontal':
            if col + length > self.board_size:
                return False
            for c in range(col, col + length):
                if board[row][c] != 'O':
                    return False
        else:  # vertical
            if row + length > self.board_size:
                return False
            for r in range(row, row + length):
                if board[r][col] != 'O':
                    return False
        return True

    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].

        Parameters:
        - state: Dictionary containing game state (see phase-specific documentation above)
        - feedback: Dictionary containing error feedback (only during placement phase if previous attempt failed)

        Returns:
        - During placement phase: Dictionary with 'ship_length', 'start', and 'orientation'
        - During bombing phase: Dictionary with 'target'

        Examples:

        # Placement phase
        if state['phase'] == 'placement':
            return {
                'ship_length': 5,
                'start': (0, 0),
                'orientation': 'horizontal'
            }

        # Bombing phase
        if state['phase'] == 'bombing':
            return {
                'target': (3, 4)
            }
        """
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            my_board = state['my_board']
            # Try to find a valid placement, preferring horizontal
            for orientation in ['horizontal', 'vertical']:
                for row in range(self.board_size):
                    for col in range(self.board_size):
                        if self._is_valid_placement(my_board, ship_length, row, col, orientation):
                            return {
                                'ship_length': ship_length,
                                'start': (row, col),
                                'orientation': orientation
                            }
            # If no valid placement found (unlikely), fall back to random (but should not happen)
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
        else:  # bombing phase
            # Update opponent board from shot_history
            for shot in state['shot_history']:
                r, c = shot['coord']
                res = shot['result']
                if res == 'HIT':
                    self.opponent_board[r][c] = 'H'
                else:
                    self.opponent_board[r][c] = 'M'
                self.unshot.discard((r, c))
            
            # Check last shot result to manage modes
            if state['last_shot_result'] == 'HIT':
                if self.hunting:
                    self.hunting = False
                    self.last_hit = state['last_shot_coord']
                    # Add adjacent unshot cells to queue
                    r, c = self.last_hit
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) in self.unshot:
                            self.hunt_queue.append((nr, nc))
            elif state['last_shot_result'] == 'MISS' and not self.hunting and not self.hunt_queue:
                # Switch back to hunting if queue is empty after a miss
                self.hunting = True
            
            # Decide target
            if self.hunting:
                if self.unshot:
                    target = random.choice(list(self.unshot))
                else:
                    # All cells shot, shouldn't happen
                    target = (0, 0)
            else:
                if self.hunt_queue:
                    target = self.hunt_queue.popleft()
                else:
                    # Queue empty, switch to hunting
                    self.hunting = True
                    target = random.choice(list(self.unshot)) if self.unshot else (0, 0)
            
            return {'target': target}
