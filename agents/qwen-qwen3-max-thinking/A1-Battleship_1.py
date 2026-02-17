"""
Agent Code: A1-Battleship
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-13 14:03:41
"""

import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.target_stack = None  # Stack for target mode in bombing phase (list used as LIFO stack)

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:  # bombing phase
            return self._bomb_target(state)
    
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        valid_placements = []
        
        # Generate all valid horizontal placements
        for row in range(self.board_size):
            for col in range(self.board_size - ship_length + 1):
                if all(my_board[row][col + k] == 'O' for k in range(ship_length)):
                    valid_placements.append(((row, col), 'horizontal'))
        
        # Generate all valid vertical placements
        for row in range(self.board_size - ship_length + 1):
            for col in range(self.board_size):
                if all(my_board[row + k][col] == 'O' for k in range(ship_length)):
                    valid_placements.append(((row, col), 'vertical'))
        
        # If ships already placed, prefer non-adjacent placements (including diagonally)
        if state['ships_placed'] > 0 and valid_placements:
            non_adjacent = []
            for (start, orient) in valid_placements:
                cells = []
                r0, c0 = start
                if orient == 'horizontal':
                    cells = [(r0, c0 + k) for k in range(ship_length)]
                else:
                    cells = [(r0 + k, c0) for k in range(ship_length)]
                
                # Check 8-direction adjacency to existing ships ('S')
                has_adjacency = False
                for r, c in cells:
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                                if my_board[nr][nc] == 'S':
                                    has_adjacency = True
                                    break
                        if has_adjacency:
                            break
                    if has_adjacency:
                        break
                
                if not has_adjacency:
                    non_adjacent.append((start, orient))
            
            if non_adjacent:
                valid_placements = non_adjacent
        
        # Select random valid placement (guaranteed non-empty per game rules)
        start, orient = random.choice(valid_placements)
        return {
            'ship_length': ship_length,
            'start': start,
            'orientation': orient
        }
    
    def _bomb_target(self, state):
        # Initialize bombing state on first call
        if self.target_stack is None:
            self.target_stack = []
        
        # Rebuild opponent grid from shot history (authoritative source)
        grid = [['U'] * self.board_size for _ in range(self.board_size)]
        for shot in state['shot_history']:
            r, c = shot['coord']
            grid[r][c] = 'H' if shot['result'] == 'HIT' else 'M'
        
        # Clean stack: remove already-known cells
        self.target_stack = [
            (r, c) for (r, c) in self.target_stack 
            if 0 <= r < self.board_size and 0 <= c < self.board_size and grid[r][c] == 'U'
        ]
        
        # Process target stack (LIFO for depth-first targeting)
        while self.target_stack:
            r, c = self.target_stack.pop()
            if grid[r][c] == 'U':
                return {'target': (r, c)}
        
        # Generate new targets from unresolved hits (hits with unknown neighbors)
        new_targets = set()
        for i in range(self.board_size):
            for j in range(self.board_size):
                if grid[i][j] == 'H':
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        ni, nj = i + dr, j + dc
                        if 0 <= ni < self.board_size and 0 <= nj < self.board_size and grid[ni][nj] == 'U':
                            new_targets.add((ni, nj))
        
        if new_targets:
            new_targets = list(new_targets)
            random.shuffle(new_targets)  # Avoid deterministic patterns
            self.target_stack = new_targets
            while self.target_stack:
                r, c = self.target_stack.pop()
                if grid[r][c] == 'U':
                    return {'target': (r, c)}
        
        # Hunt mode: prioritize parity pattern for efficiency (covers all ships ≥ length 3)
        candidates = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if grid[i][j] == 'U' and (i + j) % 2 == 0:
                    candidates.append((i, j))
        
        if not candidates:  # Fallback to all unknown cells if parity exhausted
            for i in range(self.board_size):
                for j in range(self.board_size):
                    if grid[i][j] == 'U':
                        candidates.append((i, j))
        
        # Random selection avoids predictability
        return {'target': random.choice(candidates)} if candidates else {'target': (0, 0)}