"""
Agent Code: A1-Battleship
Model: anthropic/claude-haiku-4.5
Run: 1
Generated: 2026-02-11 19:24:56
"""



class BattleshipAgent:
    """
    Intelligent Battleship agent with strategic placement and bombing.
    Uses checkerboard search pattern for initial discovery and
    BFS-based hit extension to efficiently locate and sink ships.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)
        self.search_queue = deque()
        self.queued = set()
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb_target(state)
    
    def _place_ship(self, state):
        """Place ships strategically without overlaps."""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Try random valid placements
        for _ in range(500):
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            if self._is_valid_placement(my_board, row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Fallback
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }
    
    def _is_valid_placement(self, board, row, col, length, orientation):
        """Check if ship placement is valid (no overlaps)."""
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            return all(board[row][c] == 'O' for c in range(col, col + length))
        else:
            if row + length > self.board_size:
                return False
            return all(board[r][col] == 'O' for r in range(row, row + length))
    
    def _bomb_target(self, state):
        """Execute smart bombing strategy."""
        shot_history = state['shot_history']
        last_result = state['last_shot_result']
        last_coord = state['last_shot_coord']
        
        # Parse history
        shot_set = {s['coord'] for s in shot_history}
        hits = [s['coord'] for s in shot_history if s['result'] == 'HIT']
        
        # Queue adjacent cells if we just hit
        if last_result == 'HIT' and last_coord:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = last_coord[0] + dr, last_coord[1] + dc
                if (0 <= nr < self.board_size and 
                    0 <= nc < self.board_size and
                    (nr, nc) not in shot_set and
                    (nr, nc) not in self.queued):
                    self.search_queue.append((nr, nc))
                    self.queued.add((nr, nc))
        
        # Priority 1: Drain queue (cells adjacent to hits)
        while self.search_queue:
            target = self.search_queue.popleft()
            self.queued.discard(target)
            if target not in shot_set:
                return {'target': target}
        
        # Priority 2: Extend along a line of hits
        if len(hits) >= 2:
            line_target = self._get_line_target(hits, shot_set)
            if line_target:
                return {'target': line_target}
        
        # Priority 3: Checkerboard pattern for efficient initial search
        pattern_target = self._get_checkerboard_target(shot_set)
        if pattern_target:
            return {'target': pattern_target}
        
        # Priority 4: Any untargeted cell
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in shot_set:
                    return {'target': (r, c)}
        
        return {'target': (0, 0)}
    
    def _get_line_target(self, hits, shot_set):
        """Extend along a line of hits by analyzing direction."""
        if len(hits) < 2:
            return None
        
        h_last = hits[-1]
        h_prev = hits[-2]
        
        # Horizontal alignment
        if h_last[0] == h_prev[0]:
            row = h_last[0]
            direction = 1 if h_last[1] > h_prev[1] else -1
            
            # Try extending forward
            next_col = h_last[1] + direction
            if 0 <= next_col < self.board_size and (row, next_col) not in shot_set:
                return (row, next_col)
            
            # Try extending backward
            back_col = h_prev[1] - direction
            if 0 <= back_col < self.board_size and (row, back_col) not in shot_set:
                return (row, back_col)
        
        # Vertical alignment
        elif h_last[1] == h_prev[1]:
            col = h_last[1]
            direction = 1 if h_last[0] > h_prev[0] else -1
            
            # Try extending forward
            next_row = h_last[0] + direction
            if 0 <= next_row < self.board_size and (next_row, col) not in shot_set:
                return (next_row, col)
            
            # Try extending backward
            back_row = h_prev[0] - direction
            if 0 <= back_row < self.board_size and (back_row, col) not in shot_set:
                return (back_row, col)
        
        return None
    
    def _get_checkerboard_target(self, shot_set):
        """Get next checkerboard pattern target for efficient search."""
        # Target cells where (row + col) is even
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r + c) % 2 == 0 and (r, c) not in shot_set:
                    return (r, c)
        
        # Fallback: any remaining cell
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in shot_set:
                    return (r, c)
        
        return None
