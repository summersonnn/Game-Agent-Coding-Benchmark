"""
Agent Code: A1-Battleship
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:03:41
"""

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # Target moves for the bombing phase (adjacent cells after a hit)
        self.target_moves = deque()

    def make_move(self, state, feedback):
        """
        Decide on the next action based on the current game phase.
        """
        if state['phase'] == 'placement':
            return self._do_placement(state)
        else:  # bombing phase
            return self._do_bombing(state)

    # --------------------------------------------------------------------- #
    # Placement phase
    # --------------------------------------------------------------------- #
    def _do_placement(self, state):
        """Place the next ship randomly but legally."""
        ship_length = state['ships_to_place'][0]
        board = state['my_board']

        # Collect all legal placements
        placements = []

        # Horizontal placements
        for r in range(self.board_size):
            for c in range(self.board_size - ship_length + 1):
                valid = True
                for k in range(ship_length):
                    if board[r][c + k] != 'O':
                        valid = False
                        break
                if valid:
                    placements.append(('horizontal', r, c))

        # Vertical placements
        for r in range(self.board_size - ship_length + 1):
            for c in range(self.board_size):
                valid = True
                for k in range(ship_length):
                    if board[r + k][c] != 'O':
                        valid = False
                        break
                if valid:
                    placements.append(('vertical', r, c))

        # Shuffle to randomize selection
        random.shuffle(placements)

        if placements:
            orientation, row, col = placements[0]
            return {
                'ship_length': ship_length,
                'start': (row, col),
                'orientation': orientation
            }

        # Fallback (should never happen on a valid board)
        orientation = random.choice(['horizontal', 'vertical'])
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': orientation
        }

    # --------------------------------------------------------------------- #
    # Bombing phase
    # --------------------------------------------------------------------- #
    def _do_bombing(self, state):
        """Choose the next target using a simple hunt‑and‑target strategy."""
        # Incorporate the result of the previous shot
        last_result = state.get('last_shot_result')
        last_coord = state.get('last_shot_coord')

        # Build a set of coordinates already shot
        shot_set = {entry['coord'] for entry in state.get('shot_history', [])}

        # If we just hit, add its neighbours to the target list
        if last_result == 'HIT' and last_coord is not None:
            r, c = last_coord
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if (nr, nc) not in shot_set and (nr, nc) not in self.target_moves:
                        self.target_moves.append((nr, nc))

        # Try to use a pre‑computed target
        target = None
        while self.target_moves:
            candidate = self.target_moves.popleft()
            if candidate not in shot_set:
                target = candidate
                break

        # If no prepared target, hunt using a checkerboard pattern
        if target is None:
            candidates = []
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if (r, c) not in shot_set and (r + c) % 2 == 0:
                        candidates.append((r, c))

            # If the board is nearly full, fall back to any empty cell
            if not candidates:
                for r in range(self.board_size):
                    for c in range(self.board_size):
                        if (r, c) not in shot_set:
                            candidates.append((r, c))
                if not candidates:  # Board completely filled
                    return {'target': (0, 0)}

            random.shuffle(candidates)
            target = candidates[0]

        return {'target': target}