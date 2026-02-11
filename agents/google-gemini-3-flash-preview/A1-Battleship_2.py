"""
Agent Code: A1-Battleship
Model: google-gemini-3-flash-preview
Run: 2
Generated: 2026-02-11 19:27:56
"""

import random
from collections import deque

class BattleshipAgent:
    """
    A smart Battleship agent using Parity Search for hunting 
    and BFS-based targeting for sinking ships.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.targets_to_hit = deque()
        self.hit_cells = set()
        self.miss_cells = set()
        self.all_shots = set()

    def _is_valid_placement(self, board, ship_length, start, orientation):
        row, col = start
        for i in range(ship_length):
            r, c = (row, col + i) if orientation == 'horizontal' else (row + i, col)
            if not (0 <= r < self.board_size and 0 <= c < self.board_size):
                return False
            if board[r][c] != 'O':
                return False
        return True

    def _get_parity_targets(self):
        """Returns all coordinates that fit a checkerboard pattern."""
        targets = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r + c) % 2 == 0 and (r, c) not in self.all_shots:
                    targets.append((r, c))
        return targets

    def make_move(self, state, feedback=None):
        if state['phase'] == 'placement':
            return self._handle_placement(state)
        else:
            return self._handle_bombing(state)

    def _handle_placement(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        # Attempt to place randomly but validly
        while True:
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                start = (random.randint(0, self.board_size - 1), 
                         random.randint(0, self.board_size - ship_length))
            else:
                start = (random.randint(0, self.board_size - ship_length), 
                         random.randint(0, self.board_size - 1))
            
            if self._is_valid_placement(board, ship_length, start, orientation):
                return {
                    'ship_length': ship_length,
                    'start': start,
                    'orientation': orientation
                }

    def _handle_bombing(self, state):
        # Update internal knowledge based on history
        history = state.get('shot_history', [])
        self.all_shots = {s['coord'] for s in history}
        
        # If the last shot was a HIT, add neighbors to the targeting queue
        if state.get('last_shot_result') == 'HIT':
            last_coord = state['last_shot_coord']
            self.hit_cells.add(last_coord)
            
            # Add adjacent cells to the targeting queue (Target Mode)
            r, c = last_coord
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < self.board_size and 0 <= nc < self.board_size and 
                    (nr, nc) not in self.all_shots):
                    # Prioritize these targets by putting them at the front
                    if (nr, nc) not in self.targets_to_hit:
                        self.targets_to_hit.appendleft((nr, nc))
        
        # Select target
        target = None
        
        # 1. Try targeting queue (Target Mode)
        while self.targets_to_hit:
            candidate = self.targets_to_hit.popleft()
            if candidate not in self.all_shots:
                target = candidate
                break
        
        # 2. Try Parity Search (Hunt Mode)
        if not target:
            parity_targets = self._get_parity_targets()
            if parity_targets:
                target = random.choice(parity_targets)
            else:
                # 3. Fallback: Any valid cell
                all_possible = [(r, c) for r in range(self.board_size) 
                                for c in range(self.board_size) 
                                if (r, c) not in self.all_shots]
                target = random.choice(all_possible) if all_possible else (0, 0)

        return {'target': target}