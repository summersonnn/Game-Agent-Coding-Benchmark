"""
Agent Code: A1-Battleship
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 1
Generated: 2026-02-17 12:25:21
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # For bombing phase
        self.target_list = deque()
        self.hunt_mode = True
        self.shot_cells = set()
        self.even_parity = set()
        self.odd_parity = set()
        # Initialize parity sets for hunting
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r + c) % 2 == 0:
                    self.even_parity.add((r, c))
                else:
                    self.odd_parity.add((r, c))
    
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._handle_placement(state)
        else:
            return self._handle_bombing(state)
    
    def _handle_placement(self, state):
        ship_length = state['ships_to_place'][0]
        current_board = state['my_board']
        placements = self._generate_valid_placements(ship_length, current_board)
        
        if not placements:
            # Fallback: random placement (should not happen if we generate correctly)
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
        
        # Define center area (avoid center for placement)
        center_start = self.board_size // 4
        center_end = (3 * self.board_size) // 4 - 1
        
        # Helper to get cells of a placement
        def get_cells(start, orientation):
            row, col = start
            cells = []
            if orientation == 'horizontal':
                for i in range(ship_length):
                    cells.append((row, col + i))
            else:
                for i in range(ship_length):
                    cells.append((row + i, col))
            return cells
        
        # Helper to check if placement is adjacent to existing ships
        def is_adjacent(start, orientation):
            cells = get_cells(start, orientation)
            for r, c in cells:
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if current_board[nr][nc] == 'S':
                            return True
            return False
        
        # Helper to check if placement is in center
        def is_in_center(start, orientation):
            cells = get_cells(start, orientation)
            for r, c in cells:
                if center_start <= r <= center_end and center_start <= c <= center_end:
                    return True
            return False
        
        # Three-tiered selection
        # Tier 1: non-adjacent and non-center
        for start, orientation in placements:
            if not is_adjacent(start, orientation) and not is_in_center(start, orientation):
                return {
                    'ship_length': ship_length,
                    'start': start,
                    'orientation': orientation
                }
        
        # Tier 2: non-adjacent
        for start, orientation in placements:
            if not is_adjacent(start, orientation):
                return {
                    'ship_length': ship_length,
                    'start': start,
                    'orientation': orientation
                }
        
        # Tier 3: non-center
        for start, orientation in placements:
            if not is_in_center(start, orientation):
                return {
                    'ship_length': ship_length,
                    'start': start,
                    'orientation': orientation
                }
        
        # Tier 4: any valid placement
        start, orientation = placements[0]
        return {
            'ship_length': ship_length,
            'start': start,
            'orientation': orientation
        }
    
    def _generate_valid_placements(self, ship_length, board):
        placements = []
        # Horizontal
        for row in range(self.board_size):
            for col in range(self.board_size - ship_length + 1):
                valid = True
                for i in range(ship_length):
                    if board[row][col + i] != 'O':
                        valid = False
                        break
                if valid:
                    placements.append(((row, col), 'horizontal'))
        # Vertical
        for row in range(self.board_size - ship_length + 1):
            for col in range(self.board_size):
                valid = True
                for i in range(ship_length):
                    if board[row + i][col] != 'O':
                        valid = False
                        break
                if valid:
                    placements.append(((row, col), 'vertical'))
        return placements
    
    def _handle_bombing(self, state):
        # Update shot cells from history
        self.shot_cells = {shot['coord'] for shot in state['shot_history']}
        
        # Update parity sets by removing shot cells
        self.even_parity -= self.shot_cells
        self.odd_parity -= self.shot_cells
        
        # If we just got a hit and turn continues, add adjacent cells to target list
        if state['last_shot_result'] == 'HIT' and state['turn_continues']:
            last_shot = state['last_shot_coord']
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = last_shot[0] + dr, last_shot[1] + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if (nr, nc) not in self.shot_cells:
                        self.target_list.append((nr, nc))
        
        # If target list has valid targets, use them
        if self.target_list:
            # Clean up any already shot targets
            while self.target_list and self.target_list[0] in self.shot_cells:
                self.target_list.popleft()
            if self.target_list:
                target = self.target_list.popleft()
                return {'target': target}
        
        # Hunt mode: use parity pattern
        if self.even_parity:
            target = random.choice(list(self.even_parity))
        elif self.odd_parity:
            target = random.choice(list(self.odd_parity))
        else:
            # Fallback: random unshot cell (should not happen if we track correctly)
            all_cells = set((r, c) for r in range(self.board_size) for c in range(self.board_size))
            unshot = all_cells - self.shot_cells
            if unshot:
                target = random.choice(list(unshot))
            else:
                # Should never happen in valid game
                target = (0, 0)
        
        return {'target': target}
