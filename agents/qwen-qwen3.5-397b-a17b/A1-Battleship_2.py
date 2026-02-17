"""
Agent Code: A1-Battleship
Model: qwen/qwen3.5-397b-a17b
Run: 2
Generated: 2026-02-16 18:03:23
"""

import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Find all valid placements with scores
        placements = []
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                for orientation in ['horizontal', 'vertical']:
                    if self._can_place(my_board, row, col, ship_length, orientation):
                        score = self._placement_score(my_board, row, col, ship_length, orientation)
                        placements.append((score, row, col, orientation))
        
        if placements:
            # Choose best scored placement
            placements.sort(reverse=True)
            _, row, col, orientation = placements[0]
        else:
            # Fallback random valid placement
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                max_col = self.board_size - ship_length
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, max_col) if max_col >= 0 else 0
            else:
                max_row = self.board_size - ship_length
                row = random.randint(0, max_row) if max_row >= 0 else 0
                col = random.randint(0, self.board_size - 1)
            
            # Ensure valid placement
            attempts = 0
            while not self._can_place(my_board, row, col, ship_length, orientation) and attempts < 100:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    max_col = self.board_size - ship_length
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, max_col) if max_col >= 0 else 0
                else:
                    max_row = self.board_size - ship_length
                    row = random.randint(0, max_row) if max_row >= 0 else 0
                    col = random.randint(0, self.board_size - 1)
                attempts += 1
        
        return {
            'ship_length': ship_length,
            'start': (row, col),
            'orientation': orientation
        }
    
    def _can_place(self, board, row, col, length, orientation):
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for c in range(col, col + length):
                if board[row][c] == 'S':
                    return False
        else:  # vertical
            if row + length > self.board_size:
                return False
            for r in range(row, row + length):
                if board[r][col] == 'S':
                    return False
        return True
    
    def _placement_score(self, board, row, col, length, orientation):
        score = 0
        
        if orientation == 'horizontal':
            cells = [(row, c) for c in range(col, col + length)]
        else:
            cells = [(r, col) for r in range(row, row + length)]
        
        for r, c in cells:
            # Prefer positions away from edges
            edge_dist = min(r, c, self.board_size - 1 - r, self.board_size - 1 - c)
            score += edge_dist * 0.5
            
            # Penalize proximity to other ships (with buffer)
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if board[nr][nc] == 'S':
                            score -= 8
        
        return score
    
    def _bomb(self, state):
        # Extract knowledge from state
        shot_history = state.get('shot_history', [])
        
        # Build sets of hits and all shots fired
        hits = []
        shots_fired = set()
        
        for shot in shot_history:
            coord = shot['coord']
            result = shot['result']
            shots_fired.add(coord)
            if result == 'HIT':
                hits.append(coord)
        
        # Target mode: if we have hits, try to sink ships
        if hits:
            target = self._find_target_from_hits(hits, shots_fired)
            if target:
                return {'target': target}
        
        # Hunting mode: checkerboard pattern (efficient for ships >= 2 length)
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in shots_fired:
                    if (row + col) % 2 == 0:
                        return {'target': (row, col)}
        
        # Exhausted checkerboard, try remaining cells
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in shots_fired:
                    return {'target': (row, col)}
        
        # Fallback (shouldn't reach here in normal gameplay)
        return {'target': (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))}
    
    def _find_target_from_hits(self, hits, shots_fired):
        if len(hits) == 1:
            # Try adjacent cells around single hit
            hit = hits[0]
            row, col = hit
            adjacent = [
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1)
            ]
            random.shuffle(adjacent)
            for adj in adjacent:
                if self._is_valid(adj) and adj not in shots_fired:
                    return adj
        
        elif len(hits) >= 2:
            # Determine direction from first two hits
            h1, h2 = hits[0], hits[1]
            
            if h1[0] == h2[0]:  # Horizontal ship
                row = h1[0]
                cols = sorted([h[1] for h in hits])
                # Try extending left
                left = (row, cols[0] - 1)
                if self._is_valid(left) and left not in shots_fired:
                    return left
                # Try extending right
                right = (row, cols[-1] + 1)
                if self._is_valid(right) and right not in shots_fired:
                    return right
            
            elif h1[1] == h2[1]:  # Vertical ship
                col = h1[1]
                rows = sorted([h[0] for h in hits])
                # Try extending up
                up = (rows[0] - 1, col)
                if self._is_valid(up) and up not in shots_fired:
                    return up
                # Try extending down
                down = (rows[-1] + 1, col)
                if self._is_valid(down) and down not in shots_fired:
                    return down
            
            # If hits don't align perfectly, try all adjacent to all hits
            for hit in hits:
                row, col = hit
                adjacent = [
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1)
                ]
                random.shuffle(adjacent)
                for adj in adjacent:
                    if self._is_valid(adj) and adj not in shots_fired:
                        return adj
        
        return None
    
    def _is_valid(self, coord):
        row, col = coord
        return 0 <= row < self.board_size and 0 <= col < self.board_size