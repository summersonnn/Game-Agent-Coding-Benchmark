"""
Agent Code: A1-Battleship
Model: google-gemini-3-flash-preview
Run: 3
Generated: 2026-02-11 19:27:56
"""

import random
from collections import deque

class BattleshipAgent:
    """
    An optimized Battleship agent using Parity Hunting and BFS Targeting.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.targets = deque()
        self.hit_cells = set()
        self.miss_cells = set()
        self.last_hunt_parity = 0 # 0 or 1 for checkerboard pattern

    def _is_valid(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _get_placement(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Attempt to place ships away from each other (simple heuristic)
        # We try 100 random valid positions to find one that doesn't touch another ship
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                r = random.randint(0, self.board_size - 1)
                c = random.randint(0, self.board_size - ship_length)
                coords = [(r, c + i) for i in range(ship_length)]
            else:
                r = random.randint(0, self.board_size - ship_length)
                c = random.randint(0, self.board_size - 1)
                coords = [(r + i, c) for i in range(ship_length)]
            
            if all(my_board[row][col] == 'O' for row, col in coords):
                return {
                    'ship_length': ship_length,
                    'start': (r, c),
                    'orientation': orientation
                }
        
        # Fallback to the first valid spot found if random fails
        for r in range(self.board_size):
            for c in range(self.board_size):
                for orientation in ['horizontal', 'vertical']:
                    if orientation == 'horizontal' and c + ship_length <= self.board_size:
                        if all(my_board[r][c+i] == 'O' for i in range(ship_length)):
                            return {'ship_length': ship_length, 'start': (r, c), 'orientation': orientation}
                    elif orientation == 'vertical' and r + ship_length <= self.board_size:
                        if all(my_board[r+i][c] == 'O' for i in range(ship_length)):
                            return {'ship_length': ship_length, 'start': (r, c), 'orientation': orientation}

    def _get_bombing(self, state):
        # Update internal tracking based on history
        history = state.get('shot_history', [])
        fired_shots = set()
        for shot in history:
            fired_shots.add(shot['coord'])
            if shot['result'] == 'HIT':
                self.hit_cells.add(shot['coord'])
            else:
                self.miss_cells.add(shot['coord'])

        # If last shot was a HIT, add neighbors to target queue (Kill phase)
        if state.get('last_shot_result') == 'HIT':
            last_r, last_c = state['last_shot_coord']
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = last_r + dr, last_c + dc
                if self._is_valid(nr, nc) and (nr, nc) not in fired_shots:
                    if (nr, nc) not in self.targets:
                        self.targets.appendleft((nr, nc))

        # Kill Phase: Pop from targeting queue
        while self.targets:
            target = self.targets.popleft()
            if target not in fired_shots:
                return {'target': target}

        # Hunt Phase: Use parity (checkerboard) to find ships
        # Ships are size 3+, so we only need to hit every 2nd cell
        best_shots = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in fired_shots and (r + c) % 2 == 0:
                    best_shots.append((r, c))
        
        if best_shots:
            return {'target': random.choice(best_shots)}
        
        # Final Fallback: Any remaining cell
        all_possible = [(r, c) for r in range(self.board_size) for c in range(self.board_size) 
                        if (r, c) not in fired_shots]
        return {'target': random.choice(all_possible)}

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._get_placement(state)
        else:
            return self._get_bombing(state)