"""
Agent Code: A1-Battleship
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-11 19:24:56
"""



class BattleshipAgent:
    """Smart Battleship agent with strategic placement and intelligent bombing."""
    
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)
        
        # Bombing state
        self.last_history_len = 0
        self.search_queue = deque()
        self.queued = set()
    
    def make_move(self, state, feedback):
        """Main decision function for placement and bombing phases."""
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb_target(state)
    
    def _place_ship(self, state):
        """Place a ship strategically on the board."""
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        # Attempt random placements first (spreads ships naturally)
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            if self._is_valid_placement(board, row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Systematic search if random fails
        for orientation in ['horizontal', 'vertical']:
            if orientation == 'horizontal':
                for row in range(self.board_size):
                    for col in range(self.board_size - ship_length + 1):
                        if self._is_valid_placement(board, row, col, ship_length, orientation):
                            return {
                                'ship_length': ship_length,
                                'start': (row, col),
                                'orientation': orientation
                            }
            else:
                for row in range(self.board_size - ship_length + 1):
                    for col in range(self.board_size):
                        if self._is_valid_placement(board, row, col, ship_length, orientation):
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
        """Verify that a ship placement doesn't overlap with existing ships."""
        if orientation == 'horizontal':
            if col + length > self.board_size:
                return False
            return all(board[row][c] == 'O' for c in range(col, col + length))
        else:
            if row + length > self.board_size:
                return False
            return all(board[r][col] == 'O' for r in range(row, row + length))
    
    def _bomb_target(self, state):
        """Determine the next bombing target using intelligent search."""
        shot_history = state['shot_history']
        targeted = {shot['coord'] for shot in shot_history}
        
        # Process newly discovered hits and queue adjacent cells for exploration
        for shot in shot_history[self.last_history_len:]:
            if shot['result'] == 'HIT':
                self._queue_adjacent_cells(shot['coord'], targeted)
        
        self.last_history_len = len(shot_history)
        
        # Select target: prioritize queue (around hits) or use search pattern
        if self.search_queue:
            target = self.search_queue.popleft()
            self.queued.discard(target)
        else:
            target = self._find_next_search_target(targeted)
        
        return {'target': target}
    
    def _queue_adjacent_cells(self, coord, targeted):
        """Queue cells adjacent to a hit for further investigation."""
        row, col = coord
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                new_coord = (nr, nc)
                if new_coord not in targeted and new_coord not in self.queued:
                    self.search_queue.append(new_coord)
                    self.queued.add(new_coord)
    
    def _find_next_search_target(self, targeted):
        """Find the next target using a checkerboard pattern to guarantee ship detection."""
        # Checkerboard pattern (spacing of 2) ensures finding all ships of size 3+
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in targeted and (row + col) % 2 == 0:
                    return (row, col)
        
        # Fill in remaining cells
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in targeted:
                    return (row, col)
        
        return (0, 0)
