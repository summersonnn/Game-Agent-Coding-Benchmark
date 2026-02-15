"""
Agent Code: A1-Battleship
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 1
Generated: 2026-02-14 16:15:50
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)  # Sort ships by length descending
        self.shots = set()
        self.hits = set()
        self.misses = set()
        self.sunk_ships = []  # Track lengths of sunk ships
        self.target_queue = deque()
        self.last_hit = None
        self.hunt_pattern = self._generate_hunt_pattern()
        
    def _generate_hunt_pattern(self):
        """Generate a hunt pattern that covers the board efficiently."""
        pattern = []
        # Use a checkerboard pattern to cover half the board
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row + col) % 2 == 0:  # Even parity cells
                    pattern.append((row, col))
        # If we need more coverage, add odd parity cells
        if len(pattern) < self.board_size * self.board_size // 2:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if (row + col) % 2 == 1:  # Odd parity cells
                        pattern.append((row, col))
        return pattern
    
    def _is_valid_placement(self, board, start, length, orientation):
        """Check if a ship placement is valid."""
        row, col = start
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for i in range(length):
                if board[row][col + i] != 'O':
                    return False
        else:  # vertical
            if row + length > self.board_size:
                return False
            for i in range(length):
                if board[row + i][col] != 'O':
                    return False
        return True
    
    def _get_adjacent_cells(self, coord):
        """Get valid adjacent cells for targeting."""
        row, col = coord
        adjacent = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                adjacent.append((nr, nc))
        return adjacent
    
    def _estimate_remaining_ships(self):
        """Estimate remaining ship lengths based on hits and known sunk ships."""
        total_hits = len(self.hits)
        sunk_lengths = sum(self.sunk_ships)
        remaining_hits = total_hits - sunk_lengths
        
        # Known ship lengths that haven't been sunk yet
        remaining_ships = [s for s in self.ships if s not in self.sunk_ships]
        
        # If we have clustered hits, they might belong to the same ship
        return remaining_ships, remaining_hits
    
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._handle_placement(state)
        else:
            return self._handle_bombing(state)
    
    def _handle_placement(self, state):
        """Smart ship placement strategy."""
        board = state['my_board']
        ships_to_place = state['ships_to_place']
        
        if not ships_to_place:
            return None
        
        ship_length = ships_to_place[0]
        
        # Strategy: Place ships along edges and corners to avoid common hunt patterns
        # Try different strategies in order of preference
        placements = []
        
        # 1. Try corners first (most defensive)
        corners = [
            (0, 0, 'horizontal'), (0, 0, 'vertical'),
            (0, self.board_size - ship_length, 'horizontal'),
            (self.board_size - ship_length, 0, 'vertical'),
            (self.board_size - 1, self.board_size - ship_length, 'horizontal'),
            (self.board_size - ship_length, self.board_size - 1, 'vertical')
        ]
        
        for row, col, orientation in corners:
            if self._is_valid_placement(board, (row, col), ship_length, orientation):
                placements.append(((row, col), orientation))
        
        # 2. Try edges
        if not placements:
            for row in [0, self.board_size - 1]:  # Top and bottom edges
                for col in range(self.board_size - ship_length + 1):
                    if self._is_valid_placement(board, (row, col), ship_length, 'horizontal'):
                        placements.append(((row, col), 'horizontal'))
            
            for col in [0, self.board_size - 1]:  # Left and right edges
                for row in range(self.board_size - ship_length + 1):
                    if self._is_valid_placement(board, (row, col), ship_length, 'vertical'):
                        placements.append(((row, col), 'vertical'))
        
        # 3. Try interior positions (avoiding center if possible)
        if not placements:
            # Prefer positions away from the center
            center = self.board_size // 2
            for row in range(self.board_size):
                for col in range(self.board_size - ship_length + 1):
                    # Avoid the exact center area for the largest ships
                    if ship_length >= 4 and abs(row - center) <= 1 and col >= center - 2 and col <= center + 2:
                        continue
                    if self._is_valid_placement(board, (row, col), ship_length, 'horizontal'):
                        placements.append(((row, col), 'horizontal'))
            
            for row in range(self.board_size - ship_length + 1):
                for col in range(self.board_size):
                    if ship_length >= 4 and abs(col - center) <= 1 and row >= center - 2 and row <= center + 2:
                        continue
                    if self._is_valid_placement(board, (row, col), ship_length, 'vertical'):
                        placements.append(((row, col), 'vertical'))
        
        # If we found valid placements, choose one strategically
        if placements:
            # Prefer placements that are more spread out from existing ships
            # For simplicity, choose the first valid placement
            (row, col), orientation = placements[0]
            return {
                'ship_length': ship_length,
                'start': (row, col),
                'orientation': orientation
            }
        
        # Fallback: random placement (should rarely happen with proper logic)
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
    
    def _handle_bombing(self, state):
        """Smart bombing strategy with hunt and target modes."""
        # Update shot history
        self.shots = set()
        self.hits = set()
        self.misses = set()
        
        for shot in state['shot_history']:
            coord = shot['coord']
            self.shots.add(coord)
            if shot['result'] == 'HIT':
                self.hits.add(coord)
            else:
                self.misses.add(coord)
        
        # Update target queue based on last shot
        if state['last_shot_result'] == 'HIT' and state['last_shot_coord']:
            self.last_hit = state['last_shot_coord']
            # Add adjacent cells to target queue
            adjacent = self._get_adjacent_cells(state['last_shot_coord'])
            for cell in adjacent:
                if cell not in self.shots and cell not in self.target_queue:
                    self.target_queue.append(cell)
        
        # If we have targets in queue, process them
        if self.target_queue:
            target = self.target_queue.popleft()
            if target not in self.shots:
                return {'target': target}
            else:
                # If already shot, get next target
                return self._handle_bombing(state)
        
        # Hunt mode: Use parity pattern or random from remaining cells
        remaining_cells = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.shots:
                    remaining_cells.append((row, col))
        
        if not remaining_cells:
            # Should not happen, but fallback
            row, col = random.randint(0, self.board_size - 1), random.randint(0, self.board_size - 1)
            return {'target': (row, col)}
        
        # Use hunt pattern if available
        available_pattern = [cell for cell in self.hunt_pattern if cell in remaining_cells]
        
        if available_pattern:
            # Choose a cell from the hunt pattern
            target = random.choice(available_pattern)
        else:
            # Fallback: choose randomly from remaining cells
            target = random.choice(remaining_cells)
        
        return {'target': target}
