"""
Agent Code: A1-Battleship
Model: qwen/qwen3.5-plus-02-15
Run: 1
Generated: 2026-02-16 18:33:07
"""


import random
from collections import deque

class BattleshipAgent:
    """
    Smart Battleship Agent with strategic placement and bombing logic.
    Uses checkerboard hunting pattern and targeted sinking after hits.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.shot_history = []
        self.hit_stack = []  # Stack for tracking hits to sink ships
        self.placement_attempts = 0
        
    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].
        """
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        """
        Strategic ship placement avoiding clustering and preferring edges.
        """
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Collect all valid placement positions with scores
        valid_placements = []
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                for orientation in ['horizontal', 'vertical']:
                    if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                        score = self._calculate_placement_score(my_board, row, col, ship_length, orientation)
                        valid_placements.append((score, row, col, orientation))
        
        if valid_placements:
            # Sort by score (higher is better) and pick best
            valid_placements.sort(key=lambda x: x[0], reverse=True)
            # Add some randomness among top choices to avoid predictability
            top_count = min(5, len(valid_placements))
            choice = random.choice(valid_placements[:top_count])
            _, row, col, orientation = choice
        else:
            # Fallback: random valid placement
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
    
    def _is_valid_placement(self, board, row, col, length, orientation):
        """Check if ship can be placed at given position."""
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
    
    def _calculate_placement_score(self, board, row, col, length, orientation):
        """
        Score placement based on strategic factors:
        - Prefer edges and corners (harder to find)
        - Avoid placing near other ships (harder to deduce)
        - Spread ships across the board
        """
        score = 0
        
        # Bonus for edges and corners
        if row == 0 or row == self.board_size - 1:
            score += 15
        if col == 0 or col == self.board_size - 1:
            score += 15
        if (row == 0 or row == self.board_size - 1) and (col == 0 or col == self.board_size - 1):
            score += 20  # Corner bonus
        
        # Penalize proximity to other placed ships
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == 'S':
                    # Calculate minimum distance from this ship cell to new ship
                    if orientation == 'horizontal':
                        min_row_dist = min(abs(r - row) for _ in range(length))
                        min_col_dist = min(abs(c - (col + i)) for i in range(length))
                    else:
                        min_row_dist = min(abs(r - (row + i)) for i in range(length))
                        min_col_dist = min(abs(c - col) for _ in range(length))
                    
                    min_dist = min(min_row_dist, min_col_dist)
                    if min_dist <= 1:
                        score -= 30  # Strong penalty for adjacency
                    elif min_dist <= 2:
                        score -= 10  # Moderate penalty for proximity
        
        # Slight preference for center to avoid edge-only clustering
        center_dist = abs(row - self.board_size // 2) + abs(col - self.board_size // 2)
        score -= center_dist
        
        return score
    
    def _bomb(self, state):
        """
        Smart bombing strategy:
        - Use checkerboard pattern for hunting (guarantees hitting ships of min length 3)
        - After hit, target adjacent cells to sink the ship
        - Track shot history to avoid wasting shots
        """
        shot_history = state.get('shot_history', [])
        last_result = state.get('last_shot_result')
        last_coord = state.get('last_shot_coord')
        turn_continues = state.get('turn_continues', False)
        
        # Build set of already shot coordinates
        shot_coords = set(entry['coord'] for entry in shot_history)
        
        # If we hit and get another turn, continue targeting adjacent cells
        if last_result == 'HIT' and turn_continues and last_coord:
            target = self._target_adjacent_to_sink(last_coord, shot_coords)
            if target:
                return {'target': target}
        
        # If we have hits in stack from previous turns, continue targeting
        if self.hit_stack:
            target = self._continue_sinking(shot_coords)
            if target:
                return {'target': target}
        
        # Hunt mode: use checkerboard pattern
        target = self._checkerboard_hunt(shot_coords)
        if target:
            return {'target': target}
        
        # Fallback: any unshot cell
        target = self._random_valid_target(shot_coords)
        return {'target': target}
    
    def _target_adjacent_to_sink(self, hit_coord, shot_coords):
        """
        After a hit, target adjacent cells to find ship orientation and sink it.
        Prioritize cells that could extend the ship.
        """
        row, col = hit_coord
        adjacent = [
            (row - 1, col), (row + 1, col),
            (row, col - 1), (row, col + 1)
        ]
        
        # Filter valid adjacent cells
        valid_adjacent = []
        for adj in adjacent:
            if (0 <= adj[0] < self.board_size and 
                0 <= adj[1] < self.board_size and 
                adj not in shot_coords):
                valid_adjacent.append(adj)
        
        if valid_adjacent:
            # Add to hit stack for continued targeting
            for adj in valid_adjacent:
                if adj not in [h[0] for h in self.hit_stack]:
                    self.hit_stack.append((adj, hit_coord))
            return valid_adjacent[0]
        
        return None
    
    def _continue_sinking(self, shot_coords):
        """
        Continue targeting from hit stack to sink identified ships.
        """
        while self.hit_stack:
            target, origin = self.hit_stack.pop(0)
            if target not in shot_coords:
                return target
        
        return None
    
    def _checkerboard_hunt(self, shot_coords):
        """
        Use checkerboard pattern for hunting.
        Since minimum ship length is 3, hitting every other cell guarantees finding ships.
        """
        # Try checkerboard pattern (even sum of coordinates)
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row + col) % 2 == 0 and (row, col) not in shot_coords:
                    return (row, col)
        
        # If all checkerboard cells exhausted, try remaining cells
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in shot_coords:
                    return (row, col)
        
        return None
    
    def _random_valid_target(self, shot_coords):
        """
        Fallback: return any unshot cell randomly.
        """
        available = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in shot_coords:
                    available.append((row, col))
        
        if available:
            return random.choice(available)
        
        # Should not happen in normal gameplay
        return (0, 0)