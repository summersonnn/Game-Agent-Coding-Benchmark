"""
Agent Code: A1-Battleship
Model: z-ai/glm-5@preset/fp8
Run: 1
Generated: 2026-02-11 21:33:53
"""

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.original_ships = sorted(ships)
    
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._handle_placement(state)
        else:
            return self._handle_bombing(state)
    
    def _handle_placement(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        valid_placements = []
        
        for row in range(self.board_size):
            for col in range(self.board_size - ship_length + 1):
                if all(my_board[row][col + i] == 'O' for i in range(ship_length)):
                    valid_placements.append({'start': (row, col), 'orientation': 'horizontal'})
        
        for row in range(self.board_size - ship_length + 1):
            for col in range(self.board_size):
                if all(my_board[row + i][col] == 'O' for i in range(ship_length)):
                    valid_placements.append({'start': (row, col), 'orientation': 'vertical'})
        
        if valid_placements:
            placement = random.choice(valid_placements)
            return {'ship_length': ship_length, 'start': placement['start'], 'orientation': placement['orientation']}
        
        orientation = random.choice(['horizontal', 'vertical'])
        if orientation == 'horizontal':
            row, col = random.randint(0, self.board_size - 1), random.randint(0, self.board_size - ship_length)
        else:
            row, col = random.randint(0, self.board_size - ship_length), random.randint(0, self.board_size - 1)
        return {'ship_length': ship_length, 'start': (row, col), 'orientation': orientation}
    
    def _handle_bombing(self, state):
        hits, misses = set(), set()
        for shot in state['shot_history']:
            coord = shot['coord']
            (hits if shot['result'] == 'HIT' else misses).add(coord)
        
        target = self._find_target(hits, misses)
        return {'target': target if target else self._hunt_mode(hits, misses)}
    
    def _find_target(self, hits, misses):
        if not hits:
            return None
        
        groups = self._find_connected_groups(hits)
        remaining_ships = self._get_remaining_ships(groups)
        
        for group in groups:
            if self._is_complete_ship(group, remaining_ships):
                continue
            
            line_dir = self._get_line_direction(group)
            if line_dir:
                target = self._extend_line(group, line_dir, hits, misses)
                if target:
                    return target
            
            for coord in group:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = coord[0] + dr, coord[1] + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if (nr, nc) not in hits and (nr, nc) not in misses:
                            return (nr, nc)
        return None
    
    def _find_connected_groups(self, hits):
        unvisited, groups = set(hits), []
        while unvisited:
            start = unvisited.pop()
            group, queue = {start}, deque([start])
            while queue:
                row, col = queue.popleft()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    adj = (row + dr, col + dc)
                    if adj in unvisited:
                        unvisited.remove(adj)
                        group.add(adj)
                        queue.append(adj)
            groups.append(group)
        return groups
    
    def _get_line_direction(self, group):
        if len(group) == 1:
            return None
        rows, cols = [c[0] for c in group], [c[1] for c in group]
        if len(set(rows)) == 1:
            sc = sorted(cols)
            if all(sc[i] + 1 == sc[i+1] for i in range(len(sc) - 1)):
                return 'horizontal'
        elif len(set(cols)) == 1:
            sr = sorted(rows)
            if all(sr[i] + 1 == sr[i+1] for i in range(len(sr) - 1)):
                return 'vertical'
        return None
    
    def _extend_line(self, group, direction, hits, misses):
        rows, cols = [c[0] for c in group], [c[1] for c in group]
        if direction == 'horizontal':
            row, min_c, max_c = rows[0], min(cols), max(cols)
            if min_c > 0 and (row, min_c - 1) not in misses | hits:
                return (row, min_c - 1)
            if max_c < self.board_size - 1 and (row, max_c + 1) not in misses | hits:
                return (row, max_c + 1)
        else:
            col, min_r, max_r = cols[0], min(rows), max(rows)
            if min_r > 0 and (min_r - 1, col) not in misses | hits:
                return (min_r - 1, col)
            if max_r < self.board_size - 1 and (max_r + 1, col) not in misses | hits:
                return (max_r + 1, col)
        return None
    
    def _is_complete_ship(self, group, remaining_ships):
        return len(group) in remaining_ships and self._get_line_direction(group) is not None
    
    def _get_remaining_ships(self, groups):
        remaining = list(self.original_ships)
        for group in groups:
            if self._get_line_direction(group):
                if len(group) in remaining:
                    remaining.remove(len(group))
        return remaining if remaining else [min(self.original_ships)]
    
    def _hunt_mode(self, hits, misses):
        remaining_ships = self._get_remaining_ships(self._find_connected_groups(hits))
        prob = [[0] * self.board_size for _ in range(self.board_size)]
        
        for ship_len in remaining_ships:
            for row in range(self.board_size):
                for col in range(self.board_size - ship_len + 1):
                    if all((row, col + i) not in misses for i in range(ship_len)):
                        for i in range(ship_len):
                            if (row, col + i) not in hits:
                                prob[row][col + i] += 1
            for row in range(self.board_size - ship_len + 1):
                for col in range(self.board_size):
                    if all((row + i, col) not in misses for i in range(ship_len)):
                        for i in range(ship_len):
                            if (row + i, col) not in hits:
                                prob[row + i][col] += 1
        
        max_prob, best = 0, []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in hits | misses:
                    if prob[row][col] > max_prob:
                        max_prob, best = prob[row][col], [(row, col)]
                    elif prob[row][col] == max_prob and max_prob > 0:
                        best.append((row, col))
        
        if best:
            return random.choice(best)
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in hits | misses:
                    return (row, col)
        return (0, 0)