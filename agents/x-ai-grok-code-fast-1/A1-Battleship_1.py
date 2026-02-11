"""
Agent Code: A1-Battleship
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-11 19:20:19
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
        # For placement: simple sequential placement on different rows
        self.placement_index = 0
        # For bombing: track opponent's board and targeting
        self.opponent_board = [['?' for _ in range(self.board_size)] for _ in range(self.board_size)]  # '?' unknown, 'M' miss, 'H' hit
        self.shot_history = set()  # set of (row, col) for quick lookup
        self.target_queue = deque()  # queue for adjacent targets after a hit

    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].

        Parameters:
        - state: Dictionary containing game state (see phase-specific documentation above)
        - feedback: Always None (reserved for future use)

        Returns:
        - During placement phase: Dictionary with 'ship_length', 'start', and 'orientation'
        - During bombing phase: Dictionary with 'target'
        """
        if state['phase'] == 'placement':
            # Place ships horizontally on sequential rows starting from top-left
            ship_length = state['ships_to_place'][0]
            row = self.placement_index
            col = 0
            orientation = 'horizontal'
            self.placement_index += 1
            return {
                'ship_length': ship_length,
                'start': (row, col),
                'orientation': orientation
            }
        else:  # bombing phase
            # Update opponent board and shot history
            for shot in state['shot_history']:
                coord = tuple(shot['coord'])
                if coord not in self.shot_history:
                    r, c = coord
                    self.opponent_board[r][c] = 'M' if shot['result'] == 'MISS' else 'H'
                    self.shot_history.add(coord)
            
            # If last shot was a hit, add adjacent unexplored cells to queue
            if state['last_shot_result'] == 'HIT' and state['last_shot_coord'] is not None:
                r, c = state['last_shot_coord']
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.opponent_board[nr][nc] == '?':
                        self.target_queue.append((nr, nc))
            
            # Decide target
            if state['turn_continues'] and self.target_queue:
                # Continue targeting adjacent cells
                target = self.target_queue.popleft()
            else:
                # Hunt mode: find the next unexplored cell
                target = None
                for r in range(self.board_size):
                    for c in range(self.board_size):
                        if self.opponent_board[r][c] == '?':
                            target = (r, c)
                            break
                    if target:
                        break
                if not target:
                    # Fallback, though unlikely
                    target = (0, 0)
            
            return {'target': target}
