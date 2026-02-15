"""
Agent Code: A1-Battleship
Model: qwen/qwen3-max-thinking
Run: 2
Generated: 2026-02-13 14:03:41
"""

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)
        self.remaining_opponent_ships = sorted(ships, reverse=True)
        self.opponent_board = [['?' for _ in range(board_size)] for _ in range(board_size)]
        self.hit_streak = []  # Track consecutive hits from current targeting sequence
        self.targeting_direction = None  # Current direction being probed: (dr, dc)
        self.base_hit = None  # Original hit that started targeting sequence
    
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        """Strategic placement with spacing optimization and edge avoidance for large ships."""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Generate all valid placements
        candidates = []
        
        # Horizontal placements
        for row in range(self.board_size):
            for col in range(self.board_size - ship_length + 1):
                if self._is_valid_placement(my_board, ship_length, (row, col), 'horizontal'):
                    candidates.append(('horizontal', row, col))
        
        # Vertical placements
        for row in range(self.board_size - ship_length + 1):
            for col in range(self.board_size):
                if self._is_valid_placement(my_board, ship_length, (row, col), 'vertical'):
                    candidates.append(('vertical', row, col))
        
        if not candidates:
            # Fallback to random valid placement
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
                while not self._is_valid_placement(my_board, ship_length, (row, col), 'horizontal'):
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
                while not self._is_valid_placement(my_board, ship_length, (row, col), 'vertical'):
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
            return {'ship_length': ship_length, 'start': (row, col), 'orientation': orientation}
        
        # Score placements: prefer center for large ships, edges for small ships, maximize spacing
        best_score = -float('inf')
        best_placement = None
        
        for orientation, row, col in candidates:
            score = 0
            
            # Distance from board center (favor center for large ships, edges for small)
            center_row, center_col = self.board_size / 2, self.board_size / 2
            dist_to_center = abs(row + (ship_length/2 if orientation == 'horizontal' else 0) - center_row) + \
                           abs(col + (ship_length/2 if orientation == 'vertical' else 0) - center_col)
            
            if ship_length >= 4:
                score -= dist_to_center * 1.5  # Large ships prefer center
            else:
                score += dist_to_center * 1.0  # Small ships prefer edges
            
            # Spacing from existing ships (penalize proximity)
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if my_board[r][c] == 'S':
                        ship_cells = self._get_ship_cells(ship_length, (row, col), orientation)
                        min_dist = min(abs(r - sr) + abs(c - sc) for sr, sc in ship_cells)
                        if min_dist <= 2:
                            score -= (3 - min_dist) * 4
            
            # Avoid aligning with existing ships in same row/col
            ship_cells = self._get_ship_cells(ship_length, (row, col), orientation)
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if my_board[r][c] == 'S':
                        if any(sr == r for sr, _ in ship_cells):
                            score -= 1.5
                        if any(sc == c for _, sc in ship_cells):
                            score -= 1.5
            
            if score > best_score:
                best_score = score
                best_placement = (orientation, row, col)
        
        orientation, row, col = best_placement
        return {'ship_length': ship_length, 'start': (row, col), 'orientation': orientation}
    
    def _is_valid_placement(self, board, length, start, orientation):
        """Check if ship placement is valid (within bounds and no overlap)."""
        row, col = start
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
    
    def _get_ship_cells(self, length, start, orientation):
        """Return list of coordinates occupied by a ship."""
        row, col = start
        cells = []
        if orientation == 'horizontal':
            for c in range(col, col + length):
                cells.append((row, c))
        else:
            for r in range(row, row + length):
                cells.append((r, col))
        return cells
    
    def _bomb(self, state):
        """Intelligent bombing with hunting/targeting modes and sunk ship detection."""
        # Update board state from last shot
        if state['last_shot_coord'] is not None:
            r, c = state['last_shot_coord']
            if state['last_shot_result'] == 'HIT':
                self.opponent_board[r][c] = 'H'
                # Reset targeting if we just got a hit after a miss (new ship found)
                if not state['turn_continues']:
                    self.base_hit = (r, c)
                    self.targeting_direction = None
                    self.hit_streak = [(r, c)]
            else:  # MISS
                self.opponent_board[r][c] = 'M'
                # End current targeting sequence on miss
                if self.targeting_direction is not None:
                    self.targeting_direction = None
        
        # Check if we should continue targeting after a hit
        if state['turn_continues'] and state['last_shot_result'] == 'HIT':
            return self._continue_targeting(state['last_shot_coord'])
        
        # Hunting mode: use probability heatmap
        return {'target': self._hunt()}
    
    def _continue_targeting(self, last_hit):
        """Systematically target around hits to sink ships."""
        lr, lc = last_hit
        
        # If we don't have a base hit yet, use the last hit
        if self.base_hit is None:
            self.base_hit = last_hit
            self.hit_streak = [last_hit]
        
        # If we have a direction established, continue in that direction
        if self.targeting_direction is not None:
            dr, dc = self.targeting_direction
            nr, nc = lr + dr, lc + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.opponent_board[nr][nc] == '?':
                self.hit_streak.append((nr, nc))
                return {'target': (nr, nc)}
            # Direction exhausted - try opposite direction from base hit
            obr, obc = self.base_hit
            opp_r, opp_c = obr - dr, obc - dc
            if 0 <= opp_r < self.board_size and 0 <= opp_c < self.board_size and self.opponent_board[opp_r][opp_c] == '?':
                self.targeting_direction = (-dr, -dc)
                self.hit_streak.append((opp_r, opp_c))
                return {'target': (opp_r, opp_c)}
            # Both directions exhausted - ship is sunk
            self._mark_ship_as_sunk()
            self.targeting_direction = None
            self.base_hit = None
            self.hit_streak = []
            return {'target': self._hunt()}
        
        # No direction established yet - probe orthogonal neighbors of base hit
        br, bc = self.base_hit
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(directions)
        
        for dr, dc in directions:
            nr, nc = br + dr, bc + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.opponent_board[nr][nc] == '?':
                self.targeting_direction = (dr, dc)
                self.hit_streak.append((nr, nc))
                return {'target': (nr, nc)}
        
        # No valid directions - mark as sunk (isolated single-cell hit shouldn't happen with our ships)
        self._mark_ship_as_sunk()
        self.targeting_direction = None
        self.base_hit = None
        self.hit_streak = []
        return {'target': self._hunt()}
    
    def _mark_ship_as_sunk(self):
        """Detect sunk ship size and update remaining ships."""
        if not self.hit_streak:
            return
        
        # Determine ship length from hit streak (must be straight line)
        ship_length = len(self.hit_streak)
        
        # Sort hits to determine orientation
        sorted_hits = sorted(self.hit_streak)
        is_horizontal = all(r == sorted_hits[0][0] for r, _ in sorted_hits)
        is_vertical = all(c == sorted_hits[0][1] for _, c in sorted_hits)
        
        if not (is_horizontal or is_vertical):
            # Hits not in straight line - likely multiple ships (shouldn't happen with proper targeting)
            return
        
        # Find matching ship size in remaining ships
        for size in sorted(self.remaining_opponent_ships, reverse=True):
            if ship_length == size:
                self.remaining_opponent_ships.remove(size)
                # Mark these cells as sunk (optional for strategy)
                break
    
    def _hunt(self):
        """Hunting mode using probability heatmap based on remaining ships."""
        # Build probability map
        prob_map = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # For each remaining ship size, count valid placements covering each cell
        for ship_len in self.remaining_opponent_ships:
            # Horizontal placements
            for row in range(self.board_size):
                for col in range(self.board_size - ship_len + 1):
                    valid = True
                    for c in range(col, col + ship_len):
                        if self.opponent_board[row][c] == 'M':
                            valid = False
                            break
                    if valid:
                        for c in range(col, col + ship_len):
                            if self.opponent_board[row][c] == '?':
                                prob_map[row][c] += 1
            
            # Vertical placements
            for row in range(self.board_size - ship_len + 1):
                for col in range(self.board_size):
                    valid = True
                    for r in range(row, row + ship_len):
                        if self.opponent_board[r][col] == 'M':
                            valid = False
                            break
                    if valid:
                        for r in range(row, row + ship_len):
                            if self.opponent_board[r][col] == '?':
                                prob_map[r][col] += 1
        
        # Find highest probability unknown cells
        max_prob = -1
        best_targets = []
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.opponent_board[r][c] == '?' and prob_map[r][c] > max_prob:
                    max_prob = prob_map[r][c]
                    best_targets = [(r, c)]
                elif self.opponent_board[r][c] == '?' and prob_map[r][c] == max_prob:
                    best_targets.append((r, c))
        
        # Fallback to random unknown cell if needed
        if not best_targets:
            unknown = [(r, c) for r in range(self.board_size) for c in range(self.board_size) 
                      if self.opponent_board[r][c] == '?']
            return random.choice(unknown) if unknown else (0, 0)
        
        # Prefer cells with even parity for initial hunting (optimization for ship placement constraints)
        even_parity_targets = [(r, c) for r, c in best_targets if (r + c) % 2 == 0]
        if even_parity_targets and len(self.hit_streak) == 0:  # Only apply parity when not in targeting mode
            return random.choice(even_parity_targets)
        
        return random.choice(best_targets)