"""
Agent Code: A1-Battleship
Model: qwen/qwen3-coder-next@preset/fp8
Run: 2
Generated: 2026-02-17 12:25:21
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Your agent implementation goes here.
    Implements smart placement and bombing logic.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # Placement state tracking
        self.placed_ships = []
        # Bombing state tracking
        self.target_queue = deque()
        self.hunt_mode = False
        self.last_hit = None
        self.potential_targets = set()
        self.shot_history = set()
        # Precompute all possible ship positions for probability tracking
        self._precompute_probabilities = None
        self._opponent_board_state = None

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._smart_placement(state)
        else:  # bombing phase
            return self._smart_bombing(state)

    def _smart_placement(self, state):
        """Place ships smartly with a bias toward central and asymmetric patterns."""
        board = [row[:] for row in state['my_board']]  # Copy board
        ships_to_place = state['ships_to_place']
        if not ships_to_place:
            # Shouldn't happen, but fallback
            return self._random_placement(state)
        
        ship_length = ships_to_place[0]
        
        # Try to place in a way that avoids symmetry and clusters ships on one side
        # Prefer corners and edges to leave center open for flexibility
        orientations = ['horizontal', 'vertical']
        
        # Try a few strategic positions first
        for orientation in orientations:
            # Try to place near edges
            edge_attempts = []
            if orientation == 'horizontal':
                edge_attempts.extend([
                    (0, 0), (0, self.board_size - ship_length),
                    (self.board_size - 1, 0), (self.board_size - 1, self.board_size - ship_length)
                ])
            else:
                edge_attempts.extend([
                    (0, 0), (self.board_size - ship_length, 0),
                    (0, self.board_size - 1), (self.board_size - ship_length, self.board_size - 1)
                ])
            
            # Add center-ish positions
            center_row = self.board_size // 2
            center_col = self.board_size // 2
            if orientation == 'horizontal':
                edge_attempts.append((center_row, max(0, center_col - ship_length // 2)))
            else:
                edge_attempts.append((max(0, center_row - ship_length // 2), center_col))
            
            for row, col in edge_attempts:
                if self._can_place_ship(board, row, col, ship_length, orientation):
                    # Place the ship
                    new_board = [r[:] for r in board]
                    self._place_ship_on_board(new_board, row, col, ship_length, orientation)
                    self.placed_ships.append({
                        'length': ship_length,
                        'start': (row, col),
                        'orientation': orientation
                    })
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': orientation
                    }
        
        # If strategic placements failed, try random placement (will be accepted if valid)
        return self._random_placement(state)

    def _random_placement(self, state):
        """Fallback to random placement if strategic placement fails."""
        board = [row[:] for row in state['my_board']]
        ship_length = state['ships_to_place'][0]
        
        for _ in range(200):  # Try up to 200 random positions
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            if self._can_place_ship(board, row, col, ship_length, orientation):
                new_board = [r[:] for r in board]
                self._place_ship_on_board(new_board, row, col, ship_length, orientation)
                self.placed_ships.append({
                    'length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                })
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Final fallback: just return something (engine will handle invalid placement)
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }

    def _can_place_ship(self, board, row, col, length, orientation):
        """Check if a ship can be placed at the given position."""
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

    def _place_ship_on_board(self, board, row, col, length, orientation):
        """Place a ship on the board."""
        if orientation == 'horizontal':
            for c in range(col, col + length):
                board[row][c] = 'S'
        else:
            for r in range(row, row + length):
                board[r][col] = 'S'

    def _smart_bombing(self, state):
        """Implement probability-based and hunt-and-target bombing strategy."""
        board_size = state['board_size']
        last_shot_result = state['last_shot_result']
        last_shot_coord = state['last_shot_coord']
        turn_continues = state['turn_continues']
        shot_history = state['shot_history']
        
        # Update internal state
        if last_shot_coord is not None:
            self.shot_history.add(last_shot_coord)
            if last_shot_result == 'HIT':
                if not self.hunt_mode:
                    # Start hunt mode
                    self.hunt_mode = True
                    self.last_hit = last_shot_coord
                    self._add_adjacent_targets(last_shot_coord)
                else:
                    # Continue building on current hit
                    self._add_adjacent_targets(last_shot_coord)
            elif last_shot_result == 'MISS':
                if self.hunt_mode and turn_continues:
                    # This shouldn't happen on turn_continues, but handle gracefully
                    pass
                elif self.hunt_mode and not turn_continues:
                    # Hunt mode ended without sinking; reset
                    self.hunt_mode = False
                    self.last_hit = None
                    self.potential_targets.clear()
        
        # If we're in hunt mode, use the target queue
        if self.hunt_mode and self.potential_targets:
            # Get next target from queue
            while self.target_queue:
                target = self.target_queue.popleft()
                if target not in self.shot_history:
                    return {'target': target}
            
            # Queue was empty but we still have potential targets
            # Rebuild queue with priority (prefer adjacent to last hit)
            if self.last_hit:
                row, col = self.last_hit
                # Prioritize cells adjacent to last hit
                adjacent = [
                    (row-1, col), (row+1, col),
                    (row, col-1), (row, col+1)
                ]
                for t in adjacent:
                    if (0 <= t[0] < board_size and 0 <= t[1] < board_size and 
                        t not in self.shot_history and t in self.potential_targets):
                        return {'target': t}
            
            # Fallback to any potential target
            for t in sorted(self.potential_targets):
                if t not in self.shot_history:
                    return {'target': t}
        
        # If not in hunt mode, use probability-based targeting
        # Build probability map based on remaining ships and known misses
        if self._precompute_probabilities is None:
            self._precompute_probabilities = self._build_probability_map()
        
        # Get best unshot cell from probability map
        best_target = self._get_best_probability_target()
        if best_target:
            return {'target': best_target}
        
        # Fallback to random unshot cell
        while True:
            row = random.randint(0, board_size - 1)
            col = random.randint(0, board_size - 1)
            if (row, col) not in self.shot_history:
                return {'target': (row, col)}

    def _add_adjacent_targets(self, hit_coord):
        """Add adjacent cells to target queue when in hunt mode."""
        row, col = hit_coord
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if (0 <= new_row < self.board_size and 
                0 <= new_col < self.board_size and
                (new_row, new_col) not in self.shot_history):
                self.potential_targets.add((new_row, new_col))
                self.target_queue.append((new_row, new_col))

    def _build_probability_map(self):
        """Precompute how often each cell is likely to contain a ship."""
        # Initialize probability grid with zeros
        prob_grid = [[0] * self.board_size for _ in range(self.board_size)]
        
        # For each ship length
        for ship_len in self.ships:
            # Try all horizontal placements
            for r in range(self.board_size):
                for c in range(self.board_size - ship_len + 1):
                    valid = True
                    for i in range(ship_len):
                        if (r, c + i) in self.shot_history:
                            valid = False
                            break
                    if valid:
                        for i in range(ship_len):
                            prob_grid[r][c + i] += 1
            
            # Try all vertical placements
            for r in range(self.board_size - ship_len + 1):
                for c in range(self.board_size):
                    valid = True
                    for i in range(ship_len):
                        if (r + i, c) in self.shot_history:
                            valid = False
                            break
                    if valid:
                        for i in range(ship_len):
                            prob_grid[r + i][c] += 1
        
        return prob_grid

    def _get_best_probability_target(self):
        """Get the cell with highest probability of containing a ship."""
        if not self._precompute_probabilities:
            return None
        
        best_target = None
        best_prob = -1
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.shot_history and self._precompute_probabilities[r][c] > best_prob:
                    best_prob = self._precompute_probabilities[r][c]
                    best_target = (r, c)
        
        return best_target
