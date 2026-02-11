"""
Agent Code: A1-Battleship
Model: z-ai/glm-5@preset/fp8
Run: 2
Generated: 2026-02-11 21:33:53
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)
        self.unsunk_ships = sorted(list(ships), reverse=True)
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        
        valid_placements = []
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                # Horizontal
                if c + ship_length <= self.board_size:
                    if all(my_board[r][c+i] == 'O' for i in range(ship_length)):
                        valid_placements.append(('horizontal', r, c))
                # Vertical
                if r + ship_length <= self.board_size:
                    if all(my_board[r+i][c] == 'O' for i in range(ship_length)):
                        valid_placements.append(('vertical', r, c))
        
        if valid_placements:
            orient, r, c = random.choice(valid_placements)
            return {
                'ship_length': ship_length,
                'start': (r, c),
                'orientation': orient
            }
        
        # Fallback
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
    
    def _bomb(self, state):
        shot_history = state.get('shot_history', [])
        
        hits = set()
        misses = set()
        for shot in shot_history:
            coord = shot['coord']
            if shot['result'] == 'HIT':
                hits.add(coord)
            else:
                misses.add(coord)
        
        self._update_sunk_ships(hits, misses)
        
        target = self._get_target(hits, misses)
        return {'target': target}
    
    def _update_sunk_ships(self, hits, misses):
        for ship_len in list(self.unsunk_ships):
            for hit in hits:
                r, c = hit
                
                # Check horizontal
                if c + ship_len <= self.board_size:
                    cells = [(r, c+i) for i in range(ship_len)]
                    if all(cell in hits for cell in cells):
                        left = (r, c-1) if c > 0 else None
                        right = (r, c+ship_len) if c+ship_len < self.board_size else None
                        left_blocked = left is None or left in misses
                        right_blocked = right is None or right in misses
                        if left_blocked and right_blocked:
                            if ship_len in self.unsunk_ships:
                                self.unsunk_ships.remove(ship_len)
                            break
                
                # Check vertical
                if r + ship_len <= self.board_size:
                    cells = [(r+i, c) for i in range(ship_len)]
                    if all(cell in hits for cell in cells):
                        top = (r-1, c) if r > 0 else None
                        bottom = (r+ship_len, c) if r+ship_len < self.board_size else None
                        top_blocked = top is None or top in misses
                        bottom_blocked = bottom is None or bottom in misses
                        if top_blocked and bottom_blocked:
                            if ship_len in self.unsunk_ships:
                                self.unsunk_ships.remove(ship_len)
                            break
    
    def _get_target(self, hits, misses):
        active_hits = self._get_active_hits(hits, misses)
        
        if active_hits:
            return self._extend_streak(active_hits, hits, misses)
        
        return self._hunt(hits, misses)
    
    def _get_active_hits(self, hits, misses):
        active = set()
        for hit in hits:
            r, c = hit
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if (nr, nc) not in hits and (nr, nc) not in misses:
                        active.add(hit)
                        break
        return active
    
    def _extend_streak(self, active_hits, hits, misses):
        streaks = self._find_streaks(active_hits)
        
        for streak in streaks:
            streak_list = sorted(streak)
            
            if len(streak_list) == 1:
                r, c = streak_list[0]
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if (nr, nc) not in hits and (nr, nc) not in misses:
                            return (nr, nc)
            else:
                r1, c1 = streak_list[0]
                r2, c2 = streak_list[-1]
                
                if r1 == r2:  # Horizontal
                    nc = c1 - 1
                    if nc >= 0 and (r1, nc) not in hits and (r1, nc) not in misses:
                        return (r1, nc)
                    nc = c2 + 1
                    if nc < self.board_size and (r2, nc) not in hits and (r2, nc) not in misses:
                        return (r2, nc)
                else:  # Vertical
                    nr = r1 - 1
                    if nr >= 0 and (nr, c1) not in hits and (nr, c1) not in misses:
                        return (nr, c1)
                    nr = r2 + 1
                    if nr < self.board_size and (nr, c2) not in hits and (nr, c2) not in misses:
                        return (nr, c2)
        
        return self._hunt(hits, misses)
    
    def _find_streaks(self, hits):
        remaining = set(hits)
        streaks = []
        
        while remaining:
            start = remaining.pop()
            streak = {start}
            queue = deque([start])
            
            while queue:
                r, c = queue.popleft()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in remaining:
                        remaining.remove((nr, nc))
                        streak.add((nr, nc))
                        queue.append((nr, nc))
            
            streaks.append(streak)
        
        return streaks
    
    def _hunt(self, hits, misses):
        probs = [[0] * self.board_size for _ in range(self.board_size)]
        
        ships_to_find = self.unsunk_ships if self.unsunk_ships else self.ships
        
        for ship_len in ships_to_find:
            # Horizontal placements
            for r in range(self.board_size):
                for c in range(self.board_size - ship_len + 1):
                    cells = [(r, c+i) for i in range(ship_len)]
                    if any(cell in misses for cell in cells):
                        continue
                    for cr, cc in cells:
                        if (cr, cc) not in hits:
                            probs[cr][cc] += 1
            
            # Vertical placements
            for r in range(self.board_size - ship_len + 1):
                for c in range(self.board_size):
                    cells = [(r+i, c) for i in range(ship_len)]
                    if any(cell in misses for cell in cells):
                        continue
                    for cr, cc in cells:
                        if (cr, cc) not in hits:
                            probs[cr][cc] += 1
        
        max_prob = 0
        best = []
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in hits and (r, c) not in misses:
                    if probs[r][c] > max_prob:
                        max_prob = probs[r][c]
                        best = [(r, c)]
                    elif probs[r][c] == max_prob and max_prob > 0:
                        best.append((r, c))
        
        if best:
            return random.choice(best)
        
        # Fallback - any untried cell
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in hits and (r, c) not in misses:
                    return (r, c)
        
        return (0, 0)
