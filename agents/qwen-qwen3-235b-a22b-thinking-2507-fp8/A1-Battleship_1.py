"""
Agent Code: A1-Battleship
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-04 16:22:40
"""

from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.unfired = set((i, j) for i in range(board_size) for j in range(board_size))
        self.missed_shots = set()
        self.sunk_cells = set()
        self.active_groups = []
        self.remaining_ships = sorted(ships_config, reverse=True)
        self.sunk_this_turn = None

    def process_hit(self, coord):
        new_group = set([coord])
        adjacent_groups = []
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = coord[0] + dr, coord[1] + dc
            for group in self.active_groups:
                if (nr, nc) in group:
                    if group not in adjacent_groups:
                        adjacent_groups.append(group)
                    break
        for group in adjacent_groups:
            new_group |= group
            self.active_groups.remove(group)
        self.active_groups.append(new_group)
        size = len(new_group)
        if size in self.remaining_ships:
            self.remaining_ships.remove(size)
            self.active_groups.remove(new_group)
            self.sunk_cells |= new_group
            self.sunk_this_turn = list(new_group)
        else:
            self.sunk_this_turn = None

    def hunt_mode(self):
        if not self.remaining_ships:
            return random.choice(list(self.unfired)) if self.unfired else (0, 0)
        obstacles = self.sunk_cells | self.missed_shots
        density = [[0] * self.board_size for _ in range(self.board_size)]
        for ship_length in self.remaining_ships:
            for r in range(self.board_size):
                for c in range(self.board_size - ship_length + 1):
                    valid = True
                    for i in range(ship_length):
                        if (r, c + i) in obstacles:
                            valid = False
                            break
                    if valid:
                        for i in range(ship_length):
                            density[r][c + i] += 1
            for c in range(self.board_size):
                for r in range(self.board_size - ship_length + 1):
                    valid = True
                    for i in range(ship_length):
                        if (r + i, c) in obstacles:
                            valid = False
                            break
                    if valid:
                        for i in range(ship_length):
                            density[r + i][c] += 1
        best_cells = []
        max_density = -1
        for (i, j) in self.unfired:
            d = density[i][j]
            if d > max_density:
                max_density = d
                best_cells = [(i, j)]
            elif d == max_density:
                best_cells.append((i, j))
        return random.choice(best_cells) if best_cells else (random.choice(list(self.unfired)) if self.unfired else (0, 0))

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        if last_shot_result == 'HIT':
            self.process_hit(last_shot_coord)
        elif last_shot_result == 'MISS':
            self.missed_shots.add(last_shot_coord)
        
        sunk_coords = self.sunk_this_turn if self.sunk_this_turn is not None else []
        self.sunk_this_turn = None
        
        if self.active_groups:
            candidates = []
            for group in self.active_groups:
                rows = [coord[0] for coord in group]
                cols = [coord[1] for coord in group]
                if all(r == rows[0] for r in rows):
                    min_col, max_col = min(cols), max(cols)
                    r = rows[0]
                    if min_col > 0 and (r, min_col - 1) in self.unfired:
                        candidates.append((r, min_col - 1))
                    if max_col < self.board_size - 1 and (r, max_col + 1) in self.unfired:
                        candidates.append((r, max_col + 1))
                elif all(c == cols[0] for c in cols):
                    min_row, max_row = min(rows), max(rows)
                    c = cols[0]
                    if min_row > 0 and (min_row - 1, c) in self.unfired:
                        candidates.append((min_row - 1, c))
                    if max_row < self.board_size - 1 and (max_row + 1, c) in self.unfired:
                        candidates.append((max_row + 1, c))
                else:
                    if len(group) == 1:
                        r, c = next(iter(group))
                        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) in self.unfired:
                                candidates.append((nr, nc))
            if candidates:
                next_shot = random.choice(candidates)
            else:
                next_shot = self.hunt_mode()
        else:
            next_shot = self.hunt_mode()
        
        if next_shot in self.unfired:
            self.unfired.remove(next_shot)
        elif self.unfired:
            next_shot = random.choice(list(self.unfired))
            self.unfired.remove(next_shot)
        
        return next_shot, sunk_coords
