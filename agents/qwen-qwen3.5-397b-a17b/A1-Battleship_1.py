"""
Agent Code: A1-Battleship
Model: qwen/qwen3.5-397b-a17b
Run: 1
Generated: 2026-02-16 18:03:23
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = list(ships)
        self.shots_fired = set()
        self.target_queue = deque()
        self.hunt_mode = True
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        # Find best placement with good spacing
        best = None
        best_score = -float('inf')
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                for orient in ['horizontal', 'vertical']:
                    if self._valid_placement(my_board, ship_length, (row, col), orient):
                        score = self._placement_score(my_board, ship_length, (row, col), orient)
                        if score > best_score:
                            best_score = score
                            best = {'ship_length': ship_length, 'start': (row, col), 'orientation': orient}
        
        if best:
            return best
        
        # Fallback random valid placement
        for _ in range(100):
            orient = random.choice(['horizontal', 'vertical'])
            if orient == 'horizontal':
                if ship_length <= self.board_size:
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    continue
            else:
                if ship_length <= self.board_size:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                else:
                    continue
            
            if self._valid_placement(my_board, ship_length, (row, col), orient):
                return {'ship_length': ship_length, 'start': (row, col), 'orientation': orient}
        
        return {'ship_length': ship_length, 'start': (0, 0), 'orientation': 'horizontal'}
    
    def _valid_placement(self, board, length, start, orient):
        row, col = start
        if orient == 'horizontal':
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
    
    def _placement_score(self, board, length, start, orient):
        row, col = start
        score = 0
        
        # Edge/corner preference (harder to find)
        if row == 0 or row == self.board_size - 1:
            score += 20
        if col == 0 or col == self.board_size - 1:
            score += 20
        
        # Penalize proximity to other ships
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == 'S':
                    dist = abs(r - row) + abs(c - col)
                    if dist < 2:
                        score -= 50
                    elif dist < 4:
                        score -= 20
        
        # Larger ships benefit more from edge placement
        score += length * 3
        
        # Add randomness to avoid predictability
        score += random.uniform(0, 10)
        
        return score
    
    def _bomb(self, state):
        # Sync shots_fired with shot_history from state
        self.shots_fired = set(shot['coord'] for shot in state.get('shot_history', []))
        
        last_result = state.get('last_shot_result')
        last_coord = state.get('last_shot_coord')
        
        # Process hit - add adjacent cells to target queue
        if last_result == 'HIT' and last_coord:
            for adj in self._adjacent(last_coord):
                if adj not in self.shots_fired and adj not in self.target_queue:
                    self.target_queue.append(adj)
            self.hunt_mode = False
        
        # Use target queue first (cells adjacent to hits)
        while self.target_queue:
            target = self.target_queue.popleft()
            if target not in self.shots_fired and self._in_bounds(target):
                self.shots_fired.add(target)
                return {'target': target}
        
        # Hunt mode - use checkerboard pattern
        self.hunt_mode = True
        target = self._hunt()
        if target:
            self.shots_fired.add(target)
            return {'target': target}
        
        # Fallback - any unshot cell
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.shots_fired:
                    self.shots_fired.add((r, c))
                    return {'target': (r, c)}
        
        return {'target': (0, 0)}
    
    def _adjacent(self, coord):
        row, col = coord
        adj = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                adj.append((nr, nc))
        random.shuffle(adj)  # Randomize to avoid predictability
        return adj
    
    def _in_bounds(self, coord):
        r, c = coord
        return 0 <= r < self.board_size and 0 <= c < self.board_size
    
    def _hunt(self):
        best = None
        best_score = -1
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.shots_fired:
                    score = self._cell_score(r, c)
                    if score > best_score:
                        best_score = score
                        best = (r, c)
        
        return best
    
    def _cell_score(self, row, col):
        score = 0
        
        # Checkerboard pattern (ships need 2+ consecutive cells)
        if (row + col) % 2 == 0:
            score += 25
        
        # Score based on how many ships could fit through this cell
        for ship_len in self.ships:
            # Horizontal fit
            fit = True
            for off in range(ship_len):
                if col + off >= self.board_size or (row, col + off) in self.shots_fired:
                    fit = False
                    break
            if fit:
                score += 5
            
            # Vertical fit
            fit = True
            for off in range(ship_len):
                if row + off >= self.board_size or (row + off, col) in self.shots_fired:
                    fit = False
                    break
            if fit:
                score += 5
        
        # Prefer center cells early (higher ship density probability)
        center = self.board_size // 2
        score += (self.board_size - abs(row - center) - abs(col - center))
        
        return score
