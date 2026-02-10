"""
Agent Code: A1-Battleship
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-10 16:22:20
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Advanced Battleship Agent with strategic placement and adaptive targeting.
    Uses probability-based placement and target tracking with hunt/target phases.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.reset_game_state()
        
    def reset_game_state(self):
        """Reset all game state for a new match"""
        self.placement_attempts = 0
        self.current_ship_index = 0
        
        # Bombing phase state
        self.shot_history = []          # List of {'coord': (r,c), 'result': 'HIT'/'MISS'}
        self.hits = set()              # Set of coordinates that were hits
        self.sunk_ships = set()         # Set of ship lengths that have been sunk
        self.potential_targets = deque()  # Queue of cells to check near hits
        self.board_probabilities = None   # Probability map for hunting phase
        self.phase = 'placement'
        self.last_shot = None
        
        # Initialize probability map for hunting (checkerboard pattern)
        self._init_probability_map()
    
    def _init_probability_map(self):
        """Initialize probability map for hunting phase (checkerboard pattern)"""
        self.board_probabilities = [[0 for _ in range(self.board_size)] 
                                   for _ in range(self.board_size)]
        # Checkerboard pattern: ships must cover both colors
        for r in range(self.board_size):
            for c in range(self.board_size):
                # Prioritize cells that are more likely to contain ship segments
                # Based on ship lengths and board edges
                prob = 1
                if (r + c) % 2 == 0:  # One color in checkerboard
                    prob = 2
                # Edge cells are slightly more likely (ships can't go out of bounds)
                if r == 0 or r == self.board_size-1 or c == 0 or c == self.board_size-1:
                    prob *= 1.5
                self.board_probabilities[r][c] = prob
    
    def _update_probability_map(self, shot_coord, result):
        """Update probability map based on shot result"""
        r, c = shot_coord
        if result == 'MISS':
            # Set probability to 0 for this cell
            self.board_probabilities[r][c] = 0
            # Reduce probability for nearby cells (ships can't be adjacent to misses)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        self.board_probabilities[nr][nc] *= 0.5
        elif result == 'HIT':
            # Increase probability for adjacent cells (ship likely continues)
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    self.board_probabilities[nr][nc] += 10
    
    def _get_adjacent_cells(self, coord):
        """Get valid adjacent cells (up, down, left, right)"""
        r, c = coord
        adjacent = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                adjacent.append((nr, nc))
        return adjacent
    
    def _can_place_ship(self, board, ship_length, start, orientation):
        """Check if ship can be placed at given position"""
        r, c = start
        if orientation == 'horizontal':
            if c + ship_length > self.board_size:
                return False
            for i in range(ship_length):
                if board[r][c + i] != 'O':
                    return False
        else:  # vertical
            if r + ship_length > self.board_size:
                return False
            for i in range(ship_length):
                if board[r + i][c] != 'O':
                    return False
        return True
    
    def _place_ship_on_board(self, board, ship_length, start, orientation):
        """Place ship on board (for simulation)"""
        r, c = start
        new_board = [row[:] for row in board]
        if orientation == 'horizontal':
            for i in range(ship_length):
                new_board[r][c + i] = 'S'
        else:
            for i in range(ship_length):
                new_board[r + i][c] = 'S'
        return new_board
    
    def _evaluate_placement(self, board, ship_length, start, orientation):
        """
        Evaluate placement quality (higher score = better).
        Considers: edge placement, clustering, and symmetry.
        """
        score = 0
        r, c = start
        
        # Edge bonus (ships on edges are harder to find)
        if orientation == 'horizontal':
            if c == 0 or c + ship_length == self.board_size:
                score += 3
            if r == 0 or r == self.board_size - 1:
                score += 2
        else:
            if r == 0 or r + ship_length == self.board_size:
                score += 3
            if c == 0 or c == self.board_size - 1:
                score += 2
        
        # Corner bonus
        if (r == 0 or r == self.board_size - 1) and (c == 0 or c == self.board_size - 1):
            score += 2
        
        # Clustering penalty (spread out ships are harder to hit)
        # Check nearby cells for other ships
        cluster_radius = 2
        for dr in range(-cluster_radius, cluster_radius + 1):
            for dc in range(-cluster_radius, cluster_radius + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if board[nr][nc] == 'S':
                        score -= 1
        
        return score
    
    def make_move(self, state, feedback):
        """Main decision function for both placement and bombing phases"""
        
        # Reset state for new game if needed
        if not hasattr(self, 'game_started'):
            self.reset_game_state()
            self.game_started = True
        
        if state['phase'] == 'placement':
            return self._placement_strategy(state, feedback)
        else:  # bombing phase
            return self._bombing_strategy(state)
    
    def _placement_strategy(self, state, feedback):
        """Strategic ship placement with validation and optimization"""
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        # If we have feedback about previous attempt, use it to adjust
        if feedback and 'error_code' in feedback:
            self.placement_attempts += 1
        else:
            self.placement_attempts = 0
        
        # Generate all valid placements
        valid_placements = []
        for orientation in ['horizontal', 'vertical']:
            if orientation == 'horizontal':
                for r in range(self.board_size):
                    for c in range(self.board_size - ship_length + 1):
                        if self._can_place_ship(board, ship_length, (r, c), orientation):
                            score = self._evaluate_placement(board, ship_length, (r, c), orientation)
                            valid_placements.append((score, r, c, orientation))
            else:
                for r in range(self.board_size - ship_length + 1):
                    for c in range(self.board_size):
                        if self._can_place_ship(board, ship_length, (r, c), orientation):
                            score = self._evaluate_placement(board, ship_length, (r, c), orientation)
                            valid_placements.append((score, r, c, orientation))
        
        if valid_placements:
            # Choose placement with highest score (best strategy)
            valid_placements.sort(reverse=True)  # Highest score first
            # Add some randomness to avoid predictable patterns
            top_n = min(5, len(valid_placements))
            chosen = random.choice(valid_placements[:top_n])
            _, row, col, orientation = chosen
            return {
                'ship_length': ship_length,
                'start': (row, col),
                'orientation': orientation
            }
        else:
            # No valid placement found - will be placed randomly by game
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
    
    def _bombing_strategy(self, state):
        """Adaptive bombing strategy with hunt/target phases"""
        # Update state from last shot if available
        if state['last_shot_coord'] is not None:
            last_shot = state['last_shot_coord']
            last_result = state['last_shot_result']
            
            # Record shot
            self.shot_history.append({'coord': last_shot, 'result': last_result})
            self.last_shot = last_shot
            
            if last_result == 'HIT':
                self.hits.add(last_shot)
                # Add adjacent cells to potential targets
                for adj in self._get_adjacent_cells(last_shot):
                    if adj not in self.hits and adj not in self.potential_targets:
                        self.potential_targets.append(adj)
            elif last_result == 'MISS':
                # Remove from potential targets if present
                if last_shot in self.potential_targets:
                    # Note: can't remove from deque while iterating, handle differently
                    pass
        
        # Remove any potential targets that have already been shot
        self.potential_targets = deque([t for t in self.potential_targets 
                                       if t not in self.hits and t not in [s['coord'] for s in self.shot_history]])
        
        # Choose target
        if self.potential_targets:
            # Target phase: shoot adjacent to hits
            target = self.potential_targets.popleft()
        else:
            # Hunt phase: use probability map
            target = self._choose_hunt_target()
        
        # Update probability map
        if state['last_shot_coord'] is not None:
            self._update_probability_map(state['last_shot_coord'], state['last_shot_result'])
        
        return {'target': target}
    
    def _choose_hunt_target(self):
        """Choose target during hunt phase using probability map"""
        # Find cell with highest probability that hasn't been shot
        max_prob = -1
        best_cells = []
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                coord = (r, c)
                if coord in self.hits or any(s['coord'] == coord for s in self.shot_history):
                    continue
                prob = self.board_probabilities[r][c]
                if prob > max_prob:
                    max_prob = prob
                    best_cells = [coord]
                elif prob == max_prob:
                    best_cells.append(coord)
        
        if best_cells:
            return random.choice(best_cells)
        else:
            # Fallback: random unshot cell
            all_cells = [(r, c) for r in range(self.board_size) for c in range(self.board_size)]
            unshot = [cell for cell in all_cells 
                     if cell not in self.hits and 
                     cell not in [s['coord'] for s in self.shot_history]]
            return random.choice(unshot) if unshot else (0, 0)
