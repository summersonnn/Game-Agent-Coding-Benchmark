"""
Agent Code: A1-Battleship
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-13 14:03:41
"""

import random
from collections import deque

class BattleshipAgent:
    """
    Smart Battleship agent with strategic ship placement and efficient bombing logic.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)  # [5, 4, 3]
        
        # Bombing phase state tracking
        self.shots_taken = set()      # All coordinates already shot at
        self.hit_locations = []       # Chronological list of hit coordinates
        self.hunt_queue = deque()     # Priority targets around known hits
        self.search_pattern = None    # Precomputed efficient search pattern
    
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:  # bombing phase
            return self._bomb_target(state)
    
    def _place_ship(self, state):
        """Strategically place ships with spacing to avoid adjacency vulnerabilities."""
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Generate all valid placements with spacing preference
        candidates = []
        
        # Horizontal placements
        for row in range(self.board_size):
            for col in range(self.board_size - ship_length + 1):
                if self._is_valid_placement(my_board, ship_length, (row, col), 'horizontal'):
                    score = self._placement_score(my_board, ship_length, (row, col), 'horizontal')
                    candidates.append((score, (row, col), 'horizontal'))
        
        # Vertical placements
        for row in range(self.board_size - ship_length + 1):
            for col in range(self.board_size):
                if self._is_valid_placement(my_board, ship_length, (row, col), 'vertical'):
                    score = self._placement_score(my_board, ship_length, (row, col), 'vertical')
                    candidates.append((score, (row, col), 'vertical'))
        
        # Select highest scoring placement (or random if none found)
        if candidates:
            candidates.sort(reverse=True)  # Higher score first
            _, start, orientation = candidates[0]
        else:
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
            start = (row, col)
        
        return {
            'ship_length': ship_length,
            'start': start,
            'orientation': orientation
        }
    
    def _is_valid_placement(self, board, length, start, orientation):
        """Check if ship placement is valid (within bounds, no overlap)."""
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
    
    def _placement_score(self, board, length, start, orientation):
        """
        Score placement based on:
        1. Distance from existing ships (prefer spacing)
        2. Edge proximity (smaller ships prefer edges)
        3. Center avoidance for large ships
        """
        row, col = start
        score = 0
        
        # Calculate minimum distance to existing ships (including diagonals)
        min_dist = float('inf')
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == 'S':
                    # Chebyshev distance (covers diagonal adjacency)
                    dist = max(abs(r - (row if orientation == 'vertical' else r)), 
                              abs(c - (col if orientation == 'horizontal' else c)))
                    # More precisely: check distance to any ship segment
                    if orientation == 'horizontal':
                        for dc in range(length):
                            ship_r, ship_c = row, col + dc
                            dist = max(abs(r - ship_r), abs(c - ship_c))
                            min_dist = min(min_dist, dist)
                    else:
                        for dr in range(length):
                            ship_r, ship_c = row + dr, col
                            dist = max(abs(r - ship_r), abs(c - ship_c))
                            min_dist = min(min_dist, dist)
        
        if min_dist == float('inf'):  # First ship placement
            min_dist = 5  # High default score
        
        # Prefer spacing (higher min_dist = better)
        score += min_dist * 10
        
        # Edge preference for smaller ships
        edge_dist = min(row, col, self.board_size - 1 - row, self.board_size - 1 - col)
        if length <= 3:
            score += (3 - edge_dist) * 5  # Prefer edges for small ships
        
        # Center avoidance for large ships
        if length >= 4:
            center_dist = abs(row + (length//2 if orientation == 'vertical' else 0) - self.board_size//2) + \
                         abs(col + (length//2 if orientation == 'horizontal' else 0) - self.board_size//2)
            score += center_dist * 3
        
        return score
    
    def _bomb_target(self, state):
        """Smart bombing strategy: hunt around hits first, then systematic search."""
        # Initialize search pattern on first bombing turn
        if self.search_pattern is None:
            self._initialize_search_pattern()
        
        # Process last shot result to update hunt queue
        if state['last_shot_coord'] is not None:
            coord = state['last_shot_coord']
            self.shots_taken.add(coord)
            
            if state['last_shot_result'] == 'HIT':
                self.hit_locations.append(coord)
                # Add adjacent unshot cells to hunt queue (prioritize completing ships)
                self._add_adjacent_targets(coord)
        
        # Clear hunt queue of already-shot targets
        while self.hunt_queue and self.hunt_queue[0] in self.shots_taken:
            self.hunt_queue.popleft()
        
        # Priority 1: Hunt around known hits (if we have queued targets)
        if self.hunt_queue:
            target = self.hunt_queue.popleft()
            while target in self.shots_taken and self.hunt_queue:
                target = self.hunt_queue.popleft()
            if target not in self.shots_taken:
                self.shots_taken.add(target)
                return {'target': target}
        
        # Priority 2: Systematic search using parity optimization
        # (Checkerboard pattern guarantees hitting all ships of length >= 2)
        for cell in self.search_pattern:
            if cell not in self.shots_taken:
                self.shots_taken.add(cell)
                return {'target': cell}
        
        # Fallback: Any remaining unshot cell (should rarely happen)
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.shots_taken:
                    self.shots_taken.add((r, c))
                    return {'target': (r, c)}
        
        # Final fallback (should never reach here)
        return {'target': (0, 0)}
    
    def _initialize_search_pattern(self):
        """Create efficient search pattern using checkerboard parity optimization."""
        # Phase 1: Target cells where (row + col) is even (covers all ships efficiently)
        phase1 = [(r, c) for r in range(self.board_size) 
                          for c in range(self.board_size) 
                          if (r + c) % 2 == 0]
        # Phase 2: Remaining cells
        phase2 = [(r, c) for r in range(self.board_size) 
                          for c in range(self.board_size) 
                          if (r + c) % 2 == 1]
        
        # Shuffle within phases for unpredictability while maintaining efficiency
        random.shuffle(phase1)
        random.shuffle(phase2)
        self.search_pattern = phase1 + phase2
    
    def _add_adjacent_targets(self, hit_coord):
        """Add orthogonal neighbors of a hit to hunt queue (prioritize ship completion)."""
        row, col = hit_coord
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
        
        # Prioritize directions that extend existing hit lines
        # Check for horizontal line
        if (row, col - 1) in self.hit_locations or (row, col + 1) in self.hit_locations:
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Prioritize horizontal
        # Check for vertical line
        elif (row - 1, col) in self.hit_locations or (row + 1, col) in self.hit_locations:
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Prioritize vertical
        
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                neighbor = (nr, nc)
                if neighbor not in self.shots_taken and neighbor not in self.hunt_queue:
                    self.hunt_queue.append(neighbor)