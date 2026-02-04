"""
Agent Code: A1-Battleship
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-04 16:22:40
"""

from collections import deque

class BattleshipAgent:
    """
    Your agent implementation goes here.
    Implement smart bombing logic to beat your opponent.
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        # Initialize state
        self.available_moves = set((r, c) for r in range(board_size) for c in range(board_size))
        self.hits_set = set()
        self.remaining_ships = list(ships_config)  # Will remove ships as they are sunk
        self.target_queue = deque()
        self.in_target_queue = set()

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        sunk_coords = []  # For the previous shot (if it sank a ship)
        
        # Update state based on last shot result
        if last_shot_result is not None:
            if last_shot_result == 'HIT':
                # Add to hits set
                self.hits_set.add(last_shot_coord)
                # Check if this hit sunk a ship
                sunk_coords = self.check_sunk(last_shot_coord)
                if not sunk_coords:
                    # If not sunk, add neighbors to target queue for follow-up
                    self.add_neighbors_to_target_queue(last_shot_coord)
            # For 'MISS', no action needed beyond state update (already handled by available_moves)
        
        # Choose next move
        if self.target_queue:
            move = self.target_queue.popleft()
            self.in_target_queue.discard(move)
        else:
            move = self.choose_hunting_move()
        
        # Remove the chosen move from available moves
        self.available_moves.discard(move)
        
        return (move, sunk_coords)

    def check_sunk(self, coord):
        """Check if the hit at coord caused a ship to sink. If so, return the ship's coordinates."""
        r, c = coord
        # Check horizontal extent
        left = c
        while left > 0 and (r, left-1) in self.hits_set:
            left -= 1
        right = c
        while right < self.board_size - 1 and (r, right+1) in self.hits_set:
            right += 1
        horizontal_length = right - left + 1
        
        # Check vertical extent
        up = r
        while up > 0 and (up-1, c) in self.hits_set:
            up -= 1
        down = r
        while down < self.board_size - 1 and (down+1, c) in self.hits_set:
            down += 1
        vertical_length = down - up + 1
        
        # Check if horizontal_length matches a remaining ship
        if horizontal_length in self.remaining_ships:
            sunk_coords = [(r, i) for i in range(left, right+1)]
            # Remove these hits from active hits and update remaining ships
            for sc in sunk_coords:
                self.hits_set.discard(sc)
            self.remaining_ships.remove(horizontal_length)
            return sunk_coords
        
        # Check if vertical_length matches a remaining ship
        if vertical_length in self.remaining_ships:
            sunk_coords = [(i, c) for i in range(up, down+1)]
            for sc in sunk_coords:
                self.hits_set.discard(sc)
            self.remaining_ships.remove(vertical_length)
            return sunk_coords
        
        return []

    def add_neighbors_to_target_queue(self, coord):
        """Add valid, unqueued neighbors of coord to the target queue."""
        r, c = coord
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Right, Left, Down, Up
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                neighbor = (nr, nc)
                if neighbor in self.available_moves and neighbor not in self.in_target_queue:
                    self.target_queue.append(neighbor)
                    self.in_target_queue.add(neighbor)

    def choose_hunting_move(self):
        """Choose the best move when not in target mode (no active hits to follow up)."""
        best_score = -1
        best_cell = None
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                cell = (r, c)
                if cell not in self.available_moves:
                    continue
                
                score = 0
                # Count valid placements for each remaining ship that cover (r, c)
                for ship_len in self.remaining_ships:
                    # Horizontal placements
                    start_col_min = max(0, c - ship_len + 1)
                    start_col_max = min(c, self.board_size - ship_len)
                    for start_col in range(start_col_min, start_col_max + 1):
                        valid = True
                        for i in range(ship_len):
                            if (r, start_col + i) not in self.available_moves:
                                valid = False
                                break
                        if valid:
                            score += 1
                    
                    # Vertical placements
                    start_row_min = max(0, r - ship_len + 1)
                    start_row_max = min(r, self.board_size - ship_len)
                    for start_row in range(start_row_min, start_row_max + 1):
                        valid = True
                        for i in range(ship_len):
                            if (start_row + i, c) not in self.available_moves:
                                valid = False
                                break
                        if valid:
                            score += 1
                
                if score > best_score:
                    best_score = score
                    best_cell = cell
        
        # Fallback: if no cell found (unlikely), pick randomly from available moves
        if best_cell is None:
            best_cell = random.choice(list(self.available_moves))
        return best_cell
