"""
Agent Code: A1-Battleship
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-14 16:15:50
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.reset()
    
    def reset(self):
        self.remaining_ships = sorted(self.ships, reverse=True)
        self.shots = set()
        self.hits = set()
        self.misses = set()
    
    def update_state(self, state):
        self.shots = set()
        self.hits = set()
        self.misses = set()
        for shot in state.get('shot_history', []):
            coord = shot['coord']
            self.shots.add(coord)
            if shot['result'] == 'HIT':
                self.hits.add(coord)
            else:
                self.misses.add(coord)
        self._detect_sunk_ships()
    
    def _detect_sunk_ships(self):
        visited = set()
        hits_to_remove = set()
        
        for hit in list(self.hits):
            if hit in visited:
                continue
            
            component = []
            queue = deque([hit])
            while queue:
                curr = queue.popleft()
                if curr in visited:
                    continue
                visited.add(curr)
                component.append(curr)
                r, c = curr
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in self.hits and (nr, nc) not in visited:
                        queue.append((nr, nc))
            
            if len(component) < 2:
                continue
                
            rows = [h[0] for h in component]
            cols = [h[1] for h in component]
            is_horizontal = len(set(rows)) == 1
            is_vertical = len(set(cols)) == 1
            
            if not (is_horizontal or is_vertical):
                continue
            
            if is_horizontal:
                r = rows[0]
                min_c, max_c = min(cols), max(cols)
                left = (r, min_c - 1)
                right = (r, max_c + 1)
            else:
                c = cols[0]
                min_r, max_r = min(rows), max(rows)
                left = (min_r - 1, c)
                right = (max_r + 1, c)
            
            left_blocked = (left[0] < 0 or left[0] >= self.board_size or 
                          left[1] < 0 or left[1] >= self.board_size or 
                          left in self.misses)
            right_blocked = (right[0] < 0 or right[0] >= self.board_size or 
                           right[1] < 0 or right[1] >= self.board_size or 
                           right in self.misses)
            
            if left_blocked and right_blocked:
                length = len(component)
                if length in self.remaining_ships:
                    self.remaining_ships.remove(length)
                    for h in component:
                        hits_to_remove.add(h)
        
        self.hits -= hits_to_remove
    
    def _place_ship_strategy(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        best_placement = None
        best_score = -1000
        
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                r = random.randint(0, self.board_size - 1)
                c = random.randint(0, self.board_size - ship_length)
            else:
                r = random.randint(0, self.board_size - ship_length)
                c = random.randint(0, self.board_size - 1)
            
            valid = True
            cells = []
            for i in range(ship_length):
                if orientation == 'horizontal':
                    cell = (r, c + i)
                else:
                    cell = (r + i, c)
                if board[cell[0]][cell[1]] != 'O':
                    valid = False
                    break
                cells.append(cell)
            
            if not valid:
                continue
            
            score = 0
            for (cr, cc) in cells:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            if board[nr][nc] == 'S':
                                score -= 1
            
            if score > best_score:
                best_score = score
                best_placement = {
                    'ship_length': ship_length,
                    'start': (r, c),
                    'orientation': orientation
                }
                if score == 0:
                    break
        
        if best_placement:
            return best_placement
        
        for orientation in ['horizontal', 'vertical']:
            for r in range(self.board_size):
                for c in range(self.board_size):
                    valid = True
                    for i in range(ship_length):
                        if orientation == 'horizontal':
                            if c + i >= self.board_size or board[r][c + i] != 'O':
                                valid = False
                                break
                        else:
                            if r + i >= self.board_size or board[r + i][c] != 'O':
                                valid = False
                                break
                    if valid:
                        return {
                            'ship_length': ship_length,
                            'start': (r, c),
                            'orientation': orientation
                        }
        
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }
    
    def _get_target_strategy(self):
        if self.hits:
            for hit in list(self.hits):
                r, c = hit
                h_line = [h for h in self.hits if h[0] == r]
                if len(h_line) >= 2:
                    h_line.sort(key=lambda x: x[1])
                    left = h_line[0][1] - 1
                    if left >= 0 and (r, left) not in self.shots:
                        return (r, left)
                    right = h_line[-1][1] + 1
                    if right < self.board_size and (r, right) not in self.shots:
                        return (r, right)
                
                v_line = [h for h in self.hits if h[1] == c]
                if len(v_line) >= 2:
                    v_line.sort(key=lambda x: x[0])
                    up = v_line[0][0] - 1
                    if up >= 0 and (up, c) not in self.shots:
                        return (up, c)
                    down = v_line[-1][0] + 1
                    if down < self.board_size and (down, c) not in self.shots:
                        return (down, c)
            
            for hit in self.hits:
                r, c = hit
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if (nr, nc) not in self.shots:
                            return (nr, nc)
        
        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.shots and (r + c) % 2 == 0:
                    candidates.append((r, c))
        
        if candidates:
            return random.choice(candidates)
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in self.shots:
                    return (r, c)
        
        return (0, 0)
    
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship_strategy(state)
        else:
            self.update_state(state)
            target = self._get_target_strategy()
            return {'target': target}
