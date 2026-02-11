"""
Agent Code: A1-Battleship
Model: z-ai/glm-5@preset/fp8
Run: 1
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
    
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)
    
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        valid = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if c + ship_length <= self.board_size:
                    if all(board[r][c+i] == 'O' for i in range(ship_length)):
                        valid.append((r, c, 'horizontal'))
                if r + ship_length <= self.board_size:
                    if all(board[r+i][c] == 'O' for i in range(ship_length)):
                        valid.append((r, c, 'vertical'))
        
        if not valid:
            return {'ship_length': ship_length, 'start': (0, 0), 'orientation': 'horizontal'}
        
        def score(pos):
            r, c, ori = pos
            s = 0
            if ori == 'horizontal':
                for i in range(ship_length):
                    s += min(c+i, self.board_size-1-(c+i)) + min(r, self.board_size-1-r)
            else:
                for i in range(ship_length):
                    s += min(r+i, self.board_size-1-(r+i)) + min(c, self.board_size-1-c)
            return s + random.random() * 2
        
        valid.sort(key=score, reverse=True)
        r, c, ori = random.choice(valid[:max(1, len(valid)//4)])
        
        return {'ship_length': ship_length, 'start': (r, c), 'orientation': ori}
    
    def _bomb(self, state):
        history = state.get('shot_history', [])
        
        shots, hits, misses = set(), set(), set()
        for shot in history:
            coord = shot['coord']
            shots.add(coord)
            if shot['result'] == 'HIT':
                hits.add(coord)
            else:
                misses.add(coord)
        
        # Target mode: prioritize cells adjacent to hits
        adjacent = []
        for h in hits:
            r, c = h
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) not in shots:
                    score = self._line_score(nr, nc, hits)
                    adjacent.append((score, nr, nc))
        
        if adjacent:
            adjacent.sort(reverse=True)
            return {'target': (adjacent[0][1], adjacent[0][2])}
        
        # Hunt mode: probability density
        return {'target': self._hunt(shots, misses, hits)}
    
    def _line_score(self, r, c, hits):
        score = 0
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            count = 0
            nr, nc = r + dr, c + dc
            while (nr, nc) in hits:
                count += 1
                nr += dr
                nc += dc
            score += count * count
        return score
    
    def _hunt(self, shots, misses, hits):
        probs = [[0] * self.board_size for _ in range(self.board_size)]
        remaining = self._get_remaining_ships(hits)
        
        for ship_len in remaining:
            for r in range(self.board_size):
                for c in range(self.board_size - ship_len + 1):
                    hit_count = 0
                    valid = True
                    for i in range(ship_len):
                        coord = (r, c + i)
                        if coord in misses:
                            valid = False
                            break
                        if coord in hits:
                            hit_count += 1
                    if valid:
                        weight = 1 + hit_count * 5
                        for i in range(ship_len):
                            if (r, c + i) not in shots:
                                probs[r][c + i] += weight
            
            for r in range(self.board_size - ship_len + 1):
                for c in range(self.board_size):
                    hit_count = 0
                    valid = True
                    for i in range(ship_len):
                        coord = (r + i, c)
                        if coord in misses:
                            valid = False
                            break
                        if coord in hits:
                            hit_count += 1
                    if valid:
                        weight = 1 + hit_count * 5
                        for i in range(ship_len):
                            if (r + i, c) not in shots:
                                probs[r + i][c] += weight
        
        best, max_p = [], 0
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in shots:
                    if probs[r][c] > max_p:
                        max_p = probs[r][c]
                        best = [(r, c)]
                    elif probs[r][c] == max_p and max_p > 0:
                        best.append((r, c))
        
        if best:
            return random.choice(best)
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in shots:
                    return (r, c)
        return (0, 0)
    
    def _get_remaining_ships(self, hits):
        visited = set()
        sunk_sizes = []
        
        for h in hits:
            if h in visited:
                continue
            group, stack = [], [h]
            while stack:
                coord = stack.pop()
                if coord in visited:
                    continue
                visited.add(coord)
                group.append(coord)
                r, c = coord
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in hits and (nr, nc) not in visited:
                        stack.append((nr, nc))
            
            if len(group) >= 3:
                rows = [g[0] for g in group]
                cols = [g[1] for g in group]
                if len(set(rows)) == 1:
                    size = max(cols) - min(cols) + 1
                    if size == len(group) and size in self.ships:
                        sunk_sizes.append(size)
                elif len(set(cols)) == 1:
                    size = max(rows) - min(rows) + 1
                    if size == len(group) and size in self.ships:
                        sunk_sizes.append(size)
        
        remaining = list(self.ships)
        for s in sunk_sizes:
            if s in remaining:
                remaining.remove(s)
        return remaining if remaining else self.ships
