"""
Agent Code: A1-Battleship
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-11 19:24:56
"""

from collections import defaultdict

import random
from collections import defaultdict

class BattleshipAgent:
    """
    An intelligent Battleship agent that uses strategic placement and probability-based targeting.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # Track opponent's board state (what we know from our shots)
        self.opponent_board = [[None] * board_size for _ in range(board_size)]  # None=unknown, True=hit, False=miss
        self.hit_cells = set()      # Cells we've hit
        self.miss_cells = set()     # Cells we've missed
        self.shot_history = []      # Our own shot history (list of (coord, result))
        self.active_targets = []    # List of ongoing hit segments we're investigating
        self.sunk_ships = set()     # Lengths of ships we believe are sunk
        
    def make_move(self, state, feedback):
        """
        Main decision function for both placement and bombing phases.
        """
        if state['phase'] == 'placement':
            return self._placement_move(state)
        else:  # bombing phase
            return self._bombing_move(state)
    
    def _placement_move(self, state):
        """Strategically place ships to minimize vulnerability."""
        board = state['my_board']
        ship_length = state['ships_to_place'][0]
        valid_placements = []
        
        # Generate all valid placements
        for orientation in ['horizontal', 'vertical']:
            if orientation == 'horizontal':
                for row in range(self.board_size):
                    for col in range(self.board_size - ship_length + 1):
                        if all(board[row][c] == 'O' for c in range(col, col + ship_length)):
                            valid_placements.append((row, col, orientation))
            else:
                for row in range(self.board_size - ship_length + 1):
                    for col in range(self.board_size):
                        if all(board[r][col] == 'O' for r in range(row, row + ship_length)):
                            valid_placements.append((row, col, orientation))
        
        if valid_placements:
            # Choose placement that maximizes distance from edges/corners (spread out)
            # Score: prefer center positions, avoid clustering
            best_score = -1
            best_placement = None
            center = self.board_size / 2
            
            for row, col, orientation in valid_placements:
                # Calculate distance from center (prefer center)
                if orientation == 'horizontal':
                    ship_center_col = col + ship_length / 2
                    dist = abs(row - center) + abs(ship_center_col - center)
                else:
                    ship_center_row = row + ship_length / 2
                    dist = abs(ship_center_row - center) + abs(col - center)
                score = -dist  # negative because we want minimum distance
                
                if score > best_score:
                    best_score = score
                    best_placement = (row, col, orientation)
            
            row, col, orientation = best_placement
        else:
            # Fallback to random if no valid placements (shouldn't happen normally)
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
    
    def _bombing_move(self, state):
        """Intelligent bombing using probability maps and hunt/target mode."""
        # Update our knowledge from shot history
        self._update_knowledge(state)
        
        # Check if we have active hit segments to extend
        target = self._extend_active_hits()
        if target:
            return {'target': target}
        
        # Otherwise, use probability-based targeting
        target = self._probability_targeting()
        return {'target': target}
    
    def _update_knowledge(self, state):
        """Update internal state from shot history."""
        # Clear previous state (we rebuild from scratch each time for simplicity)
        self.opponent_board = [[None] * self.board_size for _ in range(self.board_size)]
        self.hit_cells.clear()
        self.miss_cells.clear()
        self.active_targets.clear()
        self.shot_history = state['shot_history']
        
        # Process all previous shots
        for shot in state['shot_history']:
            coord = shot['coord']
            result = shot['result']
            r, c = coord
            
            if result == 'HIT':
                self.opponent_board[r][c] = True
                self.hit_cells.add(coord)
            else:  # MISS
                self.opponent_board[r][c] = False
                self.miss_cells.add(coord)
        
        # Identify active hit segments (consecutive hits in straight lines)
        self._identify_segments()
    
    def _identify_segments(self):
        """Group hits into contiguous segments (potential ship parts)."""
        visited = set()
        
        for hit in self.hit_cells:
            if hit in visited:
                continue
                
            # Try to extend horizontally
            h_segment = self._extend_segment(hit, 'horizontal', visited)
            if len(h_segment) > 1:
                self.active_targets.append({
                    'cells': h_segment,
                    'orientation': 'horizontal',
                    'length': len(h_segment)
                })
                continue
                
            # Try to extend vertically
            v_segment = self._extend_segment(hit, 'vertical', visited)
            if len(v_segment) > 1:
                self.active_targets.append({
                    'cells': v_segment,
                    'orientation': 'vertical',
                    'length': len(v_segment)
                })
                continue
            
            # Single hit (no adjacent hits)
            visited.add(hit)
    
    def _extend_segment(self, start, orientation, visited):
        """Extend from a hit in given orientation to find contiguous hits."""
        r, c = start
        segment = {start}
        visited.add(start)
        
        if orientation == 'horizontal':
            # Extend left
            cur_c = c - 1
            while cur_c >= 0 and (r, cur_c) in self.hit_cells and (r, cur_c) not in visited:
                segment.add((r, cur_c))
                visited.add((r, cur_c))
                cur_c -= 1
            # Extend right
            cur_c = c + 1
            while cur_c < self.board_size and (r, cur_c) in self.hit_cells and (r, cur_c) not in visited:
                segment.add((r, cur_c))
                visited.add((r, cur_c))
                cur_c += 1
        else:  # vertical
            # Extend up
            cur_r = r - 1
            while cur_r >= 0 and (cur_r, c) in self.hit_cells and (cur_r, c) not in visited:
                segment.add((cur_r, c))
                visited.add((cur_r, c))
                cur_r -= 1
            # Extend down
            cur_r = r + 1
            while cur_r < self.board_size and (cur_r, c) in self.hit_cells and (cur_r, c) not in visited:
                segment.add((cur_r, c))
                visited.add((cur_r, c))
                cur_r += 1
        
        return segment
    
    def _extend_active_hits(self):
        """Try to extend the most promising active hit segment."""
        if not self.active_targets:
            return None
        
        # Sort targets by priority: longer segments first, then by number of possible extensions
        targets = sorted(self.active_targets, 
                        key=lambda x: (x['length'], -self._count_possible_extensions(x)),
                        reverse=True)
        
        for target in targets:
            extensions = self._get_possible_extensions(target)
            if extensions:
                return random.choice(extensions)
        
        return None
    
    def _count_possible_extensions(self, target):
        """Count valid extension directions for a segment."""
        cells = target['cells']
        orientation = target['orientation']
        count = 0
        
        if orientation == 'horizontal':
            # Find min and max column
            cols = [c for _, c in cells]
            min_c, max_c = min(cols), max(cols)
            rows = list(set(r for r, _ in cells))
            r = rows[0]  # all same row
            
            # Check left extension
            if min_c - 1 >= 0 and self.opponent_board[r][min_c - 1] is None:
                count += 1
            # Check right extension
            if max_c + 1 < self.board_size and self.opponent_board[r][max_c + 1] is None:
                count += 1
        else:  # vertical
            # Find min and max row
            rows = [r for r, _ in cells]
            min_r, max_r = min(rows), max(rows)
            cols = list(set(c for _, c in cells))
            c = cols[0]  # all same column
            
            # Check up extension
            if min_r - 1 >= 0 and self.opponent_board[min_r - 1][c] is None:
                count += 1
            # Check down extension
            if max_r + 1 < self.board_size and self.opponent_board[max_r + 1][c] is None:
                count += 1
        
        return count
    
    def _get_possible_extensions(self, target):
        """Get list of valid extension cells for a segment."""
        cells = target['cells']
        orientation = target['orientation']
        extensions = []
        
        if orientation == 'horizontal':
            cols = [c for _, c in cells]
            min_c, max_c = min(cols), max(cols)
            rows = list(set(r for r, _ in cells))
            r = rows[0]
            
            if min_c - 1 >= 0 and self.opponent_board[r][min_c - 1] is None:
                extensions.append((r, min_c - 1))
            if max_c + 1 < self.board_size and self.opponent_board[r][max_c + 1] is None:
                extensions.append((r, max_c + 1))
        else:
            rows = [r for r, _ in cells]
            min_r, max_r = min(rows), max(rows)
            cols = list(set(c for _, c in cells))
            c = cols[0]
            
            if min_r - 1 >= 0 and self.opponent_board[min_r - 1][c] is None:
                extensions.append((min_r - 1, c))
            if max_r + 1 < self.board_size and self.opponent_board[max_r + 1][c] is None:
                extensions.append((max_r + 1, c))
        
        return extensions
    
    def _probability_targeting(self):
        """Calculate probability map and select best target."""
        # Initialize probability grid
        prob_grid = [[0] * self.board_size for _ in range(self.board_size)]
        
        # For each remaining ship (we don't know which are sunk, so consider all)
        for ship_len in self.ships:
            if ship_len in self.sunk_ships:
                continue
                
            # Count valid placements for this ship length
            for orientation in ['horizontal', 'vertical']:
                if orientation == 'horizontal':
                    for r in range(self.board_size):
                        for c in range(self.board_size - ship_len + 1):
                            if self._is_valid_placement(r, c, orientation, ship_len):
                                for i in range(ship_len):
                                    prob_grid[r][c + i] += 1
                else:
                    for r in range(self.board_size - ship_len + 1):
                        for c in range(self.board_size):
                            if self._is_valid_placement(r, c, orientation, ship_len):
                                for i in range(ship_len):
                                    prob_grid[r + i][c] += 1
        
        # Apply bonuses for cells adjacent to hits
        for r, c in self.hit_cells:
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if self.opponent_board[nr][nc] is None:  # unknown cell
                        prob_grid[nr][nc] += 10  # significant bonus
        
        # Find cell with maximum probability (excluding already shot cells)
        max_prob = -1
        best_cells = []
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.opponent_board[r][c] is None:  # only consider unknown cells
                    if prob_grid[r][c] > max_prob:
                        max_prob = prob_grid[r][c]
                        best_cells = [(r, c)]
                    elif prob_grid[r][c] == max_prob:
                        best_cells.append((r, c))
        
        if best_cells:
            return random.choice(best_cells)
        
        # Fallback: random unknown cell
        unknown_cells = [(r, c) for r in range(self.board_size) 
                        for c in range(self.board_size) 
                        if self.opponent_board[r][c] is None]
        if unknown_cells:
            return random.choice(unknown_cells)
        
        # Last resort: any cell (shouldn't happen)
        return (random.randint(0, self.board_size - 1), 
                random.randint(0, self.board_size - 1))
    
    def _is_valid_placement(self, start_r, start_c, orientation, length):
        """Check if a hypothetical ship placement is valid given current knowledge."""
        if orientation == 'horizontal':
            if start_c + length > self.board_size:
                return False
            for i in range(length):
                r, c = start_r, start_c + i
                if self.opponent_board[r][c] is False:  # miss
                    return False
        else:
            if start_r + length > self.board_size:
                return False
            for i in range(length):
                r, c = start_r + i, start_c
                if self.opponent_board[r][c] is False:  # miss
                    return False
        return True
