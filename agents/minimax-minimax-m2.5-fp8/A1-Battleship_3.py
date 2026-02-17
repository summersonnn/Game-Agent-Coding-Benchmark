"""
Agent Code: A1-Battleship
Model: minimax/minimax-m2.5@preset/fp8
Run: 3
Generated: 2026-02-17 12:25:21
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Smart Battleship AI agent implementing strategic placement and targeted bombing.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        
        # Bombing phase state
        self.shot_history = set()  # All coordinates we've shot at
        self.hits = []  # List of hit coordinates
        self.pending_targets = deque()  # Adjacent cells to check after a hit
        self.last_hit = None  # Most recent hit coordinate
        self.ship_hits = {}  # Track which hits belong to which ship (for sinking detection)
        
    def make_move(self, state, feedback):
        """Route to appropriate phase handler."""
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._make_bombing_move(state)
    
    def _place_ship(self, state):
        """Place ships strategically to maximize coverage and minimize predictability."""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Find all valid placements
        valid_placements = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                # Check horizontal placement
                if col + ship_length <= self.board_size:
                    if self._can_place(my_board, row, col, ship_length, 'horizontal'):
                        score = self._evaluate_placement(my_board, row, col, ship_length, 'horizontal')
                        valid_placements.append({
                            'start': (row, col),
                            'orientation': 'horizontal',
                            'score': score
                        })
                # Check vertical placement
                if row + ship_length <= self.board_size:
                    if self._can_place(my_board, row, col, ship_length, 'vertical'):
                        score = self._evaluate_placement(my_board, row, col, ship_length, 'vertical')
                        valid_placements.append({
                            'start': (row, col),
                            'orientation': 'vertical',
                            'score': score
                        })
        
        if not valid_placements:
            # Fallback - should not happen in normal game
            return {
                'ship_length': ship_length,
                'start': (0, 0),
                'orientation': 'horizontal'
            }
        
        # Select placement with best score (prefers分散放置)
        # Add some randomness among top choices
        valid_placements.sort(key=lambda x: x['score'], reverse=True)
        top_score = valid_placements[0]['score']
        top_placements = [p for p in valid_placements if p['score'] == top_score]
        best = random.choice(top_placements)
        
        return {
            'ship_length': ship_length,
            'start': best['start'],
            'orientation': best['orientation']
        }
    
    def _can_place(self, board, row, col, length, orientation):
        """Check if ship can be placed at position."""
        if orientation == 'horizontal':
            for c in range(col, col + length):
                if board[row][c] != 'O':
                    return False
        else:  # vertical
            for r in range(row, row + length):
                if board[r][col] != 'O':
                    return False
        return True
    
    def _evaluate_placement(self, board, row, col, length, orientation):
        """Score a placement - higher is better. Prefers spread out ships."""
        score = 0
        cells = []
        
        # Collect ship cells
        if orientation == 'horizontal':
            for c in range(col, col + length):
                cells.append((row, c))
        else:
            for r in range(row, row + length):
                cells.append((r, col))
        
        # Prefer placements that don't cluster too much
        for r, c in cells:
            # Bonus for edge positions (harder to hit)
            if r == 0 or r == self.board_size - 1 or c == 0 or c == self.board_size - 1:
                score += 3
            
            # Check adjacent empty cells (spreading bonus)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if board[nr][nc] == 'O':
                        score += 1
        
        return score
    
    def _make_bombing_move(self, state):
        """Main bombing logic - uses parity hunting + targeted attacks."""
        last_shot_coord = state.get('last_shot_coord')
        last_shot_result = state.get('last_shot_result')
        turn_continues = state.get('turn_continues', False)
        shot_history = state.get('shot_history', [])
        
        # Update our shot history from state
        for shot in shot_history:
            self.shot_history.add(shot['coord'])
        
        # If we just hit and get another turn, continue hunting
        if turn_continues and last_shot_result == 'HIT' and last_shot_coord:
            return self._continue_hunt(last_shot_coord, last_shot_result)
        
        # If turn doesn't continue but we hit before, continue from last hit
        if last_shot_result == 'HIT' and last_shot_coord:
            return self._continue_hunt(last_shot_coord, last_shot_result)
        
        # Otherwise, start new hunt
        return self._start_new_hunt()
    
    def _start_new_hunt(self):
        """Find next target using parity-based search pattern."""
        # Use parity pattern: check (row + col) % 2 == 0 cells first
        # This ensures maximum coverage with minimum shots
        
        candidates = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.shot_history:
                    parity = (row + col) % 2
                    candidates.append((row, col, parity))
        
        if not candidates:
            # All cells shot - shouldn't happen unless game is over
            return {'target': (0, 0)}
        
        # Prefer parity 0 cells first, then parity 1
        candidates.sort(key=lambda x: (x[2], random.random()))
        
        # Choose from best parity
        best_parity = candidates[0][2]
        best_candidates = [c for c in candidates if c[2] == best_parity]
        target = (best_candidates[0][0], best_candidates[0][1])
        
        self.shot_history.add(target)
        return {'target': target}
    
    def _continue_hunt(self, last_hit, result):
        """After a hit, intelligently target adjacent cells."""
        row, col = last_hit
        
        # Add to our hits list
        self.hits.append(last_hit)
        self.last_hit = last_hit
        
        # Determine valid adjacent untargeted cells
        candidates = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                if (nr, nc) not in self.shot_history:
                    candidates.append((nr, nc))
        
        if candidates:
            # Pick a random adjacent cell
            target = random.choice(candidates)
            self.shot_history.add(target)
            return {'target': target}
        
        # No valid adjacent cells, go back to search mode
        return self._start_new_hunt()
