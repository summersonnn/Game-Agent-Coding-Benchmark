"""
Agent Code: A1-Battleship
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 4
Generated: 2026-02-04 16:22:40
"""



import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.possible_moves = set((i, j) for i in range(board_size) for j in range(board_size))
        self.hits_set = set()
        self.misses_set = set()
        self.remaining_ships = list(ships_config)
        self.hunt_segment = []
        self.pending_sunk = None

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        if last_shot_result is not None:
            if last_shot_result == 'HIT':
                self.hits_set.add(last_shot_coord)
                if not self.hunt_segment:
                    self.hunt_segment = [last_shot_coord]
                else:
                    self.hunt_segment.append(last_shot_coord)
                sunk_ship = self.check_for_sunk_ship(last_shot_coord)
                if sunk_ship is not None:
                    self.pending_sunk = sunk_ship
                    for coord in sunk_ship:
                        self.hits_set.discard(coord)
                    self.hunt_segment = []
            else:
                self.misses_set.add(last_shot_coord)
            
            if not self.hunt_segment and self.hits_set:
                hit = next(iter(self.hits_set))
                self.hunt_segment = [hit]
        
        if self.hunt_segment:
            move = self.choose_hunt_move()
        else:
            move = self.choose_search_move()
        
        if move in self.possible_moves:
            self.possible_moves.remove(move)
        
        sunk_coords = self.pending_sunk
        self.pending_sunk = None
        return (move, sunk_coords)

    def choose_hunt_move(self):
        if len(self.hunt_segment) == 1:
            r, c = self.hunt_segment[0]
            directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) in self.possible_moves:
                    return (nr, nc)
            self.hunt_segment = []
            return self.choose_search_move()
        else:
            r0, c0 = self.hunt_segment[0]
            is_horizontal = True
            for r, c in self.hunt_segment[1:]:
                if r != r0:
                    is_horizontal = False
                    break
            if is_horizontal:
                cols = sorted([c for (r, c) in self.hunt_segment])
                r = r0
                min_col = cols[0]
                max_col = cols[-1]
                candidates = []
                if min_col - 1 >= 0 and (r, min_col - 1) in self.possible_moves:
                    candidates.append((r, min_col - 1))
                if max_col + 1 < self.board_size and (r, max_col + 1) in self.possible_moves:
                    candidates.append((r, max_col + 1))
                if candidates:
                    return candidates[0]
            else:
                rows = sorted([r for (r, c) in self.hunt_segment])
                c = c0
                min_row = rows[0]
                max_row = rows[-1]
                candidates = []
                if min_row - 1 >= 0 and (min_row - 1, c) in self.possible_moves:
                    candidates.append((min_row - 1, c))
                if max_row + 1 < self.board_size and (max_row + 1, c) in self.possible_moves:
                    candidates.append((max_row + 1, c))
                if candidates:
                    return candidates[0]
            self.hunt_segment = []
            return self.choose_search_move()

    def choose_search_move(self):
        best_score = -1
        best_moves = []
        for cell in self.possible_moves:
            score = 0
            for L in self.remaining_ships:
                score += self.count_placements(cell, L)
            if score > best_score:
                best_score = score
                best_moves = [cell]
            elif score == best_score:
                best_moves.append(cell)
        if best_moves:
            return random.choice(best_moves)
        return random.choice(list(self.possible_moves)) if self.possible_moves else (0, 0)

    def count_placements(self, cell, L):
        i, j = cell
        count = 0
        low_s = max(0, j - L + 1)
        high_s = min(j, self.board_size - L)
        for s in range(low_s, high_s + 1):
            valid = True
            for k in range(L):
                if (i, s + k) in self.misses_set:
                    valid = False
                    break
            if valid:
                count += 1
        low_s = max(0, i - L + 1)
        high_s = min(i, self.board_size - L)
        for s in range(low_s, high_s + 1):
            valid = True
            for k in range(L):
                if (s + k, j) in self.misses_set:
                    valid = False
                    break
            if valid:
                count += 1
        return count

    def check_for_sunk_ship(self, last_hit):
        r, c = last_hit
        left = c
        while left - 1 >= 0 and (r, left - 1) in self.hits_set:
            left -= 1
        right = c
        while right + 1 < self.board_size and (r, right + 1) in self.hits_set:
            right += 1
        seg_hor = [(r, i) for i in range(left, right + 1)]
        if len(seg_hor) in self.remaining_ships:
            return seg_hor
        
        up = r
        while up - 1 >= 0 and (up - 1, c) in self.hits_set:
            up -= 1
        down = r
        while down + 1 < self.board_size and (down + 1, c) in self.hits_set:
            down += 1
        seg_ver = [(i, c) for i in range(up, down + 1)]
        if len(seg_ver) in self.remaining_ships:
            return seg_ver
        return None
