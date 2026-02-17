"""
Agent Code: A1-Battleship
Model: qwen/qwen3-coder@preset/fp8
Run: 3
Generated: 2026-02-17 12:25:21
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Smart Battleship agent implementing strategic ship placement and bombing logic.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)  # Largest first for placement
        self.shot_history = set()
        self.last_hit = None
        self.hit_stack = deque()
        self.parity_board = None
        self.remaining_ships = ships[:]
        self._initialize_parity_board()

    def _initialize_parity_board(self):
        """Create a checkerboard pattern for smarter search."""
        self.parity_board = [
            [(i + j) % 2 for j in range(self.board_size)]
            for i in range(self.board_size)
        ]

    def _is_valid_placement(self, board, ship_length, start_row, start_col, orientation):
        """Check if a ship placement is valid."""
        if orientation == 'horizontal':
            if start_col + ship_length > self.board_size:
                return False
            for c in range(start_col, start_col + ship_length):
                if board[start_row][c] != 'O':
                    return False
        else:  # vertical
            if start_row + ship_length > self.board_size:
                return False
            for r in range(start_row, start_row + ship_length):
                if board[r][start_col] != 'O':
                    return False
        return True

    def _place_ship(self, board, ship_length, start_row, start_col, orientation):
        """Place a ship on the board."""
        if orientation == 'horizontal':
            for c in range(start_col, start_col + ship_length):
                board[start_row][c] = 'S'
        else:
            for r in range(start_row, start_row + ship_length):
                board[r][start_col] = 'S'

    def _get_neighbors(self, row, col):
        """Get valid adjacent coordinates."""
        neighbors = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                neighbors.append((nr, nc))
        return neighbors

    def _get_parity_targets(self):
        """Get all cells matching current parity (based on smallest remaining ship)."""
        min_ship = min(self.remaining_ships) if self.remaining_ships else 1
        parity = min_ship % 2
        targets = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.parity_board[r][c] == parity and (r, c) not in self.shot_history:
                    targets.append((r, c))
        return targets

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            # Place ships starting from largest to smallest
            ship_length = state['ships_to_place'][0]
            my_board = [row[:] for row in state['my_board']]  # Deep copy
            
            # Try to place ships away from edges
            attempts = 0
            while attempts < 100:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                
                if self._is_valid_placement(my_board, ship_length, row, col, orientation):
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': orientation
                    }
                attempts += 1
            
            # Fallback to first valid position found
            for row in range(self.board_size):
                for col in range(self.board_size):
                    for orientation in ['horizontal', 'vertical']:
                        if self._is_valid_placement(my_board, ship_length, row, col, orientation):
                            return {
                                'ship_length': ship_length,
                                'start': (row, col),
                                'orientation': orientation
                            }
            
            # Last resort: let engine handle invalid placement
            return {
                'ship_length': ship_length,
                'start': (0, 0),
                'orientation': 'horizontal'
            }

        else:  # bombing phase
            # Update game state based on last shot result
            if state['last_shot_result'] == 'HIT' and state['last_shot_coord']:
                self.last_hit = state['last_shot_coord']
                self.hit_stack.append(self.last_hit)
                
                # Check if we sunk a ship by looking for isolated hits
                # This is a simplified check - in practice you'd track ship segments
                hit_neighbors = [pos for pos in self._get_neighbors(*self.last_hit) 
                               if pos in self.shot_history]
                if not hit_neighbors:  # First hit of a potential ship
                    # Add neighbors to stack for follow-up shots
                    for pos in self._get_neighbors(*self.last_hit):
                        if pos not in self.shot_history:
                            self.hit_stack.append(pos)
            
            if state['last_shot_result'] == 'MISS' and state['last_shot_coord']:
                # Remove from potential targets if it was a planned shot
                if state['last_shot_coord'] in self.hit_stack:
                    self.hit_stack.remove(state['last_shot_coord'])
            
            # Update shot history
            if state['last_shot_coord']:
                self.shot_history.add(state['last_shot_coord'])
            
            # Determine next target
            target = None
            
            # 1. Follow-up on hits
            while self.hit_stack and not target:
                candidate = self.hit_stack.pop()
                if candidate not in self.shot_history:
                    target = candidate
            
            # 2. Parity-based search when no specific targets
            if not target:
                parity_targets = self._get_parity_targets()
                if parity_targets:
                    target = random.choice(parity_targets)
                else:
                    # Fallback to any unshot cell
                    available = [
                        (r, c) for r in range(self.board_size) 
                        for c in range(self.board_size)
                        if (r, c) not in self.shot_history
                    ]
                    if available:
                        target = random.choice(available)
            
            # If still no target (shouldn't happen), pick random
            if not target:
                target = (random.randint(0, self.board_size-1), 
                         random.randint(0, self.board_size-1))
            
            return {'target': target}
