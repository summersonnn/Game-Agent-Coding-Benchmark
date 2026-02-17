"""
Agent Code: A1-Battleship
Model: qwen/qwen3.5-plus-02-15
Run: 3
Generated: 2026-02-16 18:33:07
"""

import random

class BattleshipAgent:
    """
    Smart Battleship Agent with strategic placement and bombing logic.
    Uses checkerboard hunting pattern and targeted sinking after hits.
    """
    
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.shot_history = set()
        self.potential_targets = []
        self.mode = 'hunt'  # 'hunt' or 'target'
        self.last_hit = None
        self.hits_on_current_ship = 0
        self.ship_direction = None
        
    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].
        """
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        """Strategic ship placement avoiding clustering."""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Find all valid placements with scores
        valid_placements = []
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                for orientation in ['horizontal', 'vertical']:
                    if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                        score = self._score_placement(my_board, row, col, ship_length, orientation)
                        valid_placements.append((score, row, col, orientation))
        
        if valid_placements:
            # Sort by score and pick from top options for variety
            valid_placements.sort(key=lambda x: x[0], reverse=True)
            top_count = max(1, len(valid_placements) // 3)
            _, row, col, orientation = random.choice(valid_placements[:top_count])
        else:
            # Fallback to random valid placement
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
        """Check if ship placement is valid."""
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
    
    def _score_placement(self, board, row, col, length, orientation):
        """Score placement based on spacing from edges and other ships."""
        score = 0
        
        # Prefer positions away from edges (harder to find)
        if orientation == 'horizontal':
            score += min(row, self.board_size - 1 - row) * 3
            score += min(col, self.board_size - 1 - (col + length - 1)) * 3
        else:
            score += min(row, self.board_size - 1 - (row + length - 1)) * 3
            score += min(col, self.board_size - 1 - col) * 3
        
        # Penalize proximity to existing ships
        cells = []
        if orientation == 'horizontal':
            cells = [(row, col + i) for i in range(length)]
        else:
            cells = [(row + i, col) for i in range(length)]
        
        for r, c in cells:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if board[nr][nc] == 'S':
                            score -= 10  # Strong penalty for being near other ships
        
        return score
    
    def _bomb(self, state):
        """Smart bombing with hunt and target modes."""
        shot_history = state.get('shot_history', [])
        last_result = state.get('last_shot_result', None)
        last_coord = state.get('last_shot_coord', None)
        
        # Update shot history from state
        for shot in shot_history:
            self.shot_history.add(shot['coord'])
        
        # Process last shot result
        if last_coord and last_result:
            if last_result == 'HIT':
                self._process_hit(last_coord)
            else:
                self._process_miss(last_coord)
        
        # Choose target based on mode
        if self.mode == 'target' and self.potential_targets:
            target = self._get_target_shot()
        else:
            target = self._get_hunt_shot()
        
        # Ensure target hasn't been shot (safety check)
        attempts = 0
        while target in self.shot_history and attempts < 100:
            if self.mode == 'target' and self.potential_targets:
                if target in self.potential_targets:
                    self.potential_targets.remove(target)
                if self.potential_targets:
                    target = self._get_target_shot()
                else:
                    self.mode = 'hunt'
                    target = self._get_hunt_shot()
            else:
                self.mode = 'hunt'
                target = self._get_hunt_shot()
            attempts += 1
        
        self.shot_history.add(target)
        
        return {'target': target}
    
    def _process_hit(self, coord):
        """Process a hit and add adjacent cells as potential targets."""
        self.mode = 'target'
        self.last_hit = coord
        self.hits_on_current_ship += 1
        
        row, col = coord
        adjacent = [
            (row - 1, col),  # up
            (row + 1, col),  # down
            (row, col - 1),  # left
            (row, col + 1)   # right
        ]
        
        for adj in adjacent:
            if 0 <= adj[0] < self.board_size and 0 <= adj[1] < self.board_size:
                if adj not in self.shot_history and adj not in self.potential_targets:
                    self.potential_targets.append(adj)
    
    def _process_miss(self, coord):
        """Process a miss and clean up potential targets."""
        if coord in self.potential_targets:
            self.potential_targets.remove(coord)
        
        # If no more potential targets, return to hunt mode
        if not self.potential_targets:
            self.mode = 'hunt'
            self.last_hit = None
            self.hits_on_current_ship = 0
            self.ship_direction = None
    
    def _get_target_shot(self):
        """Get next target when sinking a ship."""
        if self.potential_targets:
            return self.potential_targets.pop(0)
        return None
    
    def _get_hunt_shot(self):
        """Get next hunt shot using checkerboard pattern for efficiency."""
        # Checkerboard pattern - hits every other cell
        # This guarantees hitting all ships (minimum length 3) efficiently
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row + col) % 2 == 0:
                    if (row, col) not in self.shot_history:
                        return (row, col)
        
        # If checkerboard exhausted, try all remaining cells
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.shot_history:
                    return (row, col)
        
        # Fallback (shouldn't happen in normal gameplay)
        return (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))