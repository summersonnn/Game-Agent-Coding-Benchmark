"""
Agent Code: A1-Battleship
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:03:41
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Smart Battleship agent with strategic placement and targeting.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships  # List of ship lengths, e.g., [5, 4, 3]
        
        # Bombing phase state
        self.shot_history = set()  # Set of (row, col) that have been shot at
        self.target_queue = deque()  # Adjacent cells to try after a hit
        self.hits_on_current_ship = []  # Track hits on current ship for targeting
        self.possible_ships = []  # Track possible ship positions
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._placement_phase(state)
        else:
            return self._bombing_phase(state)
    
    def _placement_phase(self, state):
        """Place ships strategically with spread-out positioning."""
        ship_length = state['ships_to_place'][0]
        board_size = self.board_size
        my_board = state['my_board']
        
        # Try multiple placements and pick the best one
        best_pos = None
        best_score = -float('inf')
        
        # Generate all possible placements
        for orientation in ['horizontal', 'vertical']:
            for row in range(board_size):
                for col in range(board_size):
                    if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                        score = self._evaluate_placement(my_board, row, col, ship_length, orientation)
                        if score > best_score:
                            best_score = score
                            best_pos = (row, col, orientation)
        
        # If no valid placement found (shouldn't happen), use random
        if best_pos is None:
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, board_size - 1)
                col = random.randint(0, board_size - ship_length)
            else:
                row = random.randint(0, board_size - ship_length)
                col = random.randint(0, board_size - 1)
            return {
                'ship_length': ship_length,
                'start': (row, col),
                'orientation': orientation
            }
        
        row, col, orientation = best_pos
        return {
            'ship_length': ship_length,
            'start': (row, col),
            'orientation': orientation
        }
    
    def _is_valid_placement(self, board, row, col, length, orientation):
        """Check if placement is valid."""
        if orientation == 'horizontal':
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
    
    def _evaluate_placement(self, board, row, col, length, orientation):
        """Score a placement - prefer spread out ships."""
        score = 0
        
        # Check adjacent cells (prefer more open space around ship)
        for r in range(row - 1, row + length + 1):
            for c in range(col - 1, col + 2):
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if board[r][c] == 'O':
                        score += 1
        
        # Prefer not touching other ships
        if orientation == 'horizontal':
            for c in range(col, col + length):
                for dr, dc in [(-1, 0), (1, 0)]:
                    nr, nc = row + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if board[nr][nc] == 'S':
                            score -= 10
        else:
            for r in range(row, row + length):
                for dr, dc in [(0, -1), (0, 1)]:
                    nr, nc = r + dr, col + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if board[nr][nc] == 'S':
                            score -= 10
        
        # Prefer central positions for larger ships
        if orientation == 'horizontal':
            center_col = col + length // 2
            score += abs(board_size // 2 - center_col)
        else:
            center_row = row + length // 2
            score += abs(board_size // 2 - center_row)
        
        return score
    
    def _bombing_phase(self, state):
        """Smart targeting with hunt and target mode."""
        board_size = self.board_size
        
        # Update state from previous shot
        if state.get('last_shot_coord'):
            last_coord = state['last_shot_coord']
            last_result = state.get('last_shot_result', 'MISS')
            
            if last_result == 'HIT':
                # Add adjacent cells to target queue
                row, col = last_coord
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < board_size and 0 <= nc < board_size:
                        if (nr, nc) not in self.shot_history:
                            self.target_queue.append((nr, nc))
                self.hits_on_current_ship.append(last_coord)
            else:
                # Miss - just clear the hits tracking if we were targeting
                # but keep the queue for other potential targets
                pass
        
        # Try to get target from queue first (after a hit)
        while self.target_queue:
            target = self.target_queue.popleft()
            if target not in self.shot_history:
                self.shot_history.add(target)
                return {'target': target}
        
        # No targets in queue - use parity (checkerboard) hunting
        # This is more efficient than pure random
        for row in range(board_size):
            for col in range(board_size):
                # Parity pattern: only shoot on even/odd cells
                if (row + col) % 2 == 0:
                    if (row, col) not in self.shot_history:
                        self.shot_history.add((row, col))
                        return {'target': (row, col)}
        
        # Fallback: pure random (should rarely reach here)
        while True:
            row = random.randint(0, board_size - 1)
            col = random.randint(0, board_size - 1)
            if (row, col) not in self.shot_history:
                self.shot_history.add((row, col))
                return {'target': (row, col)}
