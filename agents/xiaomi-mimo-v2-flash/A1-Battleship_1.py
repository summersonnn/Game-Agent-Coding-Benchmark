"""
Agent Code: A1-Battleship
Model: xiaomi/mimo-v2-flash
Run: 1
Generated: 2026-02-11 19:24:56
"""



import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            board = state['my_board']
            for _ in range(1000):
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                    valid = True
                    for i in range(ship_length):
                        if board[row][col + i] != 'O':
                            valid = False
                            break
                    if valid:
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                    valid = True
                    for i in range(ship_length):
                        if board[row + i][col] != 'O':
                            valid = False
                            break
                    if valid:
                        return {
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': orientation
                        }
            for orientation in ['horizontal', 'vertical']:
                if orientation == 'horizontal':
                    for row in range(self.board_size):
                        for col in range(self.board_size - ship_length + 1):
                            valid = True
                            for i in range(ship_length):
                                if board[row][col + i] != 'O':
                                    valid = False
                                    break
                            if valid:
                                return {
                                    'ship_length': ship_length,
                                    'start': (row, col),
                                    'orientation': orientation
                                }
                else:
                    for row in range(self.board_size - ship_length + 1):
                        for col in range(self.board_size):
                            valid = True
                            for i in range(ship_length):
                                if board[row + i][col] != 'O':
                                    valid = False
                                    break
                            if valid:
                                return {
                                    'ship_length': ship_length,
                                    'start': (row, col),
                                    'orientation': orientation
                                }
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
        else:
            shot_history = state['shot_history']
            hits = set()
            misses = set()
            for shot in shot_history:
                coord = shot['coord']
                if shot['result'] == 'HIT':
                    hits.add(coord)
                else:
                    misses.add(coord)
            if hits:
                groups = self.get_connected_components(hits)
                potential_targets = set()
                for group in groups:
                    if self.is_horizontal(group):
                        row = next(iter(group))[0]
                        cols = [c for r, c in group]
                        min_col = min(cols)
                        max_col = max(cols)
                        if min_col > 0:
                            coord = (row, min_col - 1)
                            if coord not in hits and coord not in misses:
                                potential_targets.add(coord)
                        if max_col < self.board_size - 1:
                            coord = (row, max_col + 1)
                            if coord not in hits and coord not in misses:
                                potential_targets.add(coord)
                    elif self.is_vertical(group):
                        col = next(iter(group))[1]
                        rows = [r for r, c in group]
                        min_row = min(rows)
                        max_row = max(rows)
                        if min_row > 0:
                            coord = (min_row - 1, col)
                            if coord not in hits and coord not in misses:
                                potential_targets.add(coord)
                        if max_row < self.board_size - 1:
                            coord = (max_row + 1, col)
                            if coord not in hits and coord not in misses:
                                potential_targets.add(coord)
                    else:
                        for hit in group:
                            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                                nr = hit[0] + dr
                                nc = hit[1] + dc
                                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                                    coord = (nr, nc)
                                    if coord not in hits and coord not in misses:
                                        potential_targets.add(coord)
                if potential_targets:
                    return {'target': random.choice(list(potential_targets))}
            available = []
            for r in range(self.board_size):
                for c in range(self.board_size):
                    coord = (r, c)
                    if coord not in hits and coord not in misses:
                        available.append(coord)
            if available:
                available_even = [coord for coord in available if (coord[0] + coord[1]) % 2 == 0]
                available_odd = [coord for coord in available if (coord[0] + coord[1]) % 2 == 1]
                if available_even:
                    return {'target': random.choice(available_even)}
                else:
                    return {'target': random.choice(available_odd)}
            return {'target': (0, 0)}
    
    def get_connected_components(self, hits):
        if not hits:
            return []
        visited = set()
        components = []
        hits_set = set(hits)
        for hit in hits:
            if hit not in visited:
                stack = [hit]
                component = set()
                while stack:
                    node = stack.pop()
                    if node not in visited:
                        visited.add(node)
                        component.add(node)
                        for neighbor in self.get_neighbors(node):
                            if neighbor in hits_set and neighbor not in visited:
                                stack.append(neighbor)
                components.append(component)
        return components

    def get_neighbors(self, coord):
        r, c = coord
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                neighbors.append((nr, nc))
        return neighbors

    def is_horizontal(self, group):
        if not group:
            return False
        rows = set(r for r, c in group)
        return len(rows) == 1

    def is_vertical(self, group):
        if not group:
            return False
        cols = set(c for r, c in group)
        return len(cols) == 1
