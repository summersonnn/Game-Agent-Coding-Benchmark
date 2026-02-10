"""
Agent Code: A1-Battleship
Model: x-ai/grok-code-fast-1
Run: 2
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
        self.all_shots = set()
        self.hits = set()
        self.hunt_targets = deque()
        self.target_mode = False
        self.last_hit = None
        # Initialize hunt targets with checkerboard parity (even sum of row + col)
        for r in range(board_size):
            for c in range(board_size):
                if (r + c) % 2 == 0:
                    self.hunt_targets.append((r, c))

    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].

        Parameters:
        - state: Dictionary containing game state (see phase-specific documentation above)
        - feedback: Dictionary containing error feedback (only during placement phase if previous attempt failed)

        Returns:
        - During placement phase: Dictionary with 'ship_length', 'start', and 'orientation'
        - During bombing phase: Dictionary with 'target'
        """
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            board = state['my_board']
            attempts = 0
            while attempts < 3:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                    # Check for overlap
                    overlap = False
                    for i in range(ship_length):
                        if board[row][col + i] == 'S':
                            overlap = True
                            break
                    if not overlap:
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                    # Check for overlap
                    overlap = False
                    for i in range(ship_length):
                        if board[row + i][col] == 'S':
                            overlap = True
                            break
                    if not overlap:
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
                attempts += 1
            # Fallback: return a placement (game will handle penalty if invalid)
            return {
                'ship_length': ship_length,
                'start': (0, 0),
                'orientation': 'horizontal'
            }
        else:  # bombing phase
            # Update from last shot
            if state['last_shot_coord'] is not None:
                self.all_shots.add(state['last_shot_coord'])
                if state['last_shot_result'] == 'HIT':
                    self.hits.add(state['last_shot_coord'])
                    self.target_mode = True
                    self.last_hit = state['last_shot_coord']
                    # Add adjacent cells to hunt_targets if not already shot
                    r, c = self.last_hit
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) not in self.all_shots:
                            self.hunt_targets.append((nr, nc))
            # Choose target
            if self.target_mode and self.hunt_targets:
                target = self.hunt_targets.popleft()
            else:
                # Hunt mode or fallback
                while self.hunt_targets and self.hunt_targets[0] in self.all_shots:
                    self.hunt_targets.popleft()
                if self.hunt_targets:
                    target = self.hunt_targets.popleft()
                else:
                    # Random from remaining possible targets
                    possible = [(r, c) for r in range(self.board_size) for c in range(self.board_size) if (r, c) not in self.all_shots]
                    if possible:
                        target = random.choice(possible)
                    else:
                        target = (0, 0)  # Should not happen
            return {'target': target}
