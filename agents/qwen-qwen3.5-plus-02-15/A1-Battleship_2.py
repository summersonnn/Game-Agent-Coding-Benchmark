"""
Agent Code: A1-Battleship
Model: qwen/qwen3.5-plus-02-15
Run: 2
Generated: 2026-02-16 18:33:07
"""



import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships.copy() if ships else []
        self.target_stack = []
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        """Strategic ship placement to make ships harder to find."""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        valid_placements = []
        
        for orientation in ['horizontal', 'vertical']:
            if orientation == 'horizontal':
                max_row = self.board_size - 1
                max_col = self.board_size - ship_length
            else:
                max_row = self.board_size - ship_length
                max_col = self.board_size - 1
            
            for row in range(max_row + 1):
                for col in range(max_col + 1):
                    if self._can_place_ship(my_board, row, col, ship_length, orientation):
                        score = self._score_placement(my_board, row, col, ship_length, orientation)
                        valid_placements.append((score, row, col, orientation))
        
        if valid_placements:
            valid_placements.sort(key=lambda x: x[0], reverse=True)
            top_count = max(1, len(valid_placements) // 4)
            choice = random.choice(valid_placements[:top_count])
            return {
                'ship_length': ship_length,
                'start': (choice[1], choice[2]),
                'orientation': choice[3]
            }
        
        return self._random_place(ship_length, my_board)
    
    def _can_place_ship(self, board, row, col, length, orientation):
        """Validate ship placement."""
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            for c in range(col, col + length):
                if board[row][c] != 'O':
                    return False
        else:
            if row + length > self.board_size:
                return False
            for r in range(row, row + length):
                if board[r][col] != 'O':
                    return False
        return True
    
    def _score_placement(self, board, row, col, length, orientation):
        """Score a placement (higher = better)."""
        score = 0.0
        
        # Prefer edges and corners
        if row == 0 or row == self.board_size - 1:
            score += 3.0
        if col == 0 or col == self.board_size - 1:
            score += 3.0
        
        # Penalize near other ships (avoid clustering)
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if board[nr][nc] == 'S':
                        score -= 5.0
        
        # Add randomness to avoid predictability
        score += random.random() * 2.0
        
        return score
    
    def _random_place(self, ship_length, board):
        """Random valid placement fallback."""
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            if self._can_place_ship(board, row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }
    
    def _bomb(self, state):
        """Intelligent bombing strategy with hunt and target modes."""
        shot_history = state.get('shot_history', [])
        last_result = state.get('last_shot_result', None)
        last_coord = state.get('last_shot_coord', None)
        
        shot_set = set(s['coord'] for s in shot_history)
        
        # Process last shot result
        if last_coord and last_result == 'HIT':
            self._add_adjacent(last_coord, shot_set)
        
        # Try target mode first (after hits)
        target = self._pop_target(shot_set)
        if target:
            return {'target': target}
        
        # Hunt mode with checkerboard pattern
        return {'target': self._hunt(shot_set)}
    
    def _add_adjacent(self, coord, shot_set):
        """Add adjacent cells to target stack."""
        row, col = coord
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if (0 <= nr < self.board_size and 
                0 <= nc < self.board_size and 
                (nr, nc) not in shot_set):
                self.target_stack.append((nr, nc))
    
    def _pop_target(self, shot_set):
        """Get next target from stack."""
        while self.target_stack:
            target = self.target_stack.pop()
            if target not in shot_set:
                return target
        return None
    
    def _hunt(self, shot_set):
        """Hunt mode with checkerboard pattern for efficiency."""
        # Try parity patterns (covers all cells with ~50% shots)
        for parity in [0, 1]:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if (row + col) % 2 == parity:
                        if (row, col) not in shot_set:
                            return (row, col)
        
        # Fallback: any unshot cell
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in shot_set:
                    return (row, col)
        
        # Last resort
        return (random.randint(0, self.board_size - 1),
                random.randint(0, self.board_size - 1))
