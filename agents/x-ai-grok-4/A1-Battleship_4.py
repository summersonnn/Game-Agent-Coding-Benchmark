"""
Agent Code: A1-Battleship
Model: x-ai/grok-4
Run: 4
Generated: 2026-02-04 17:06:44
"""

from collections import defaultdict, Counter

from collections import defaultdict, Counter

class BattleshipAgent:
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.remaining_ships = sorted(ships_config, reverse=True)
        self.positions = {}
        for length in self.ships_config:
            pos_list = []
            # Horizontal
            for r in range(self.board_size):
                for c in range(self.board_size - length + 1):
                    pos_list.append((length, r, c, True))
            # Vertical
            for c in range(self.board_size):
                for r in range(self.board_size - length + 1):
                    pos_list.append((length, r, c, False))
            self.positions[length] = pos_list
        self.grid = [['U'] * self.board_size for _ in range(self.board_size)]
        self.possible_targets = set((i, j) for i in range(self.board_size) for j in range(self.board_size))
        self.hit_cells = set()
        self.miss_cells = set()

    def get_cells(self, pos):
        length, r, c, horiz = pos
        return [(r + i if not horiz else r, c if not horiz else c + i) for i in range(length)]

    def get_prob_data(self):
        count = defaultdict(int)
        total = 0
        pos_counters = {l: Counter() for l in self.remaining_ships}

        def recurse(curr_occ, remain, path):
            nonlocal total
            if not remain:
                if self.hit_cells.issubset(curr_occ):
                    total += 1
                    for cell in curr_occ:
                        count[cell] += 1
                    for l, p in path.items():
                        pos_counters[l][p] += 1
                return
            l = remain[0]
            for p in self.positions[l]:
                cells = self.get_cells(p)
                new_set = set(cells)
                if new_set.isdisjoint(curr_occ) and new_set.isdisjoint(self.miss_cells):
                    recurse(curr_occ | new_set, remain[1:], {**path, l: p})

        recurse(set(), self.remaining_ships, {})
        return count, total, pos_counters

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        if last_shot_coord is not None:
            r, c = last_shot_coord
            self.possible_targets.discard((r, c))
            if last_shot_result == 'HIT':
                self.grid[r][c] = 'H'
                self.hit_cells.add((r, c))
            else:
                self.grid[r][c] = 'M'
                self.miss_cells.add((r, c))

        sunk_coords = []
        updated = True
        count = defaultdict(int)
        total = 0
        while updated:
            updated = False
            count, total, pos_counters = self.get_prob_data()
            for l in list(self.remaining_ships):
                counter = pos_counters.get(l, Counter())
                if counter:
                    most_common_pos, num = counter.most_common(1)[0]
                    if num == total and total > 0:
                        cells = self.get_cells(most_common_pos)
                        if all(self.grid[cr][cc] == 'H' for cr, cc in cells):
                            sunk_coords.extend(cells)
                            for cr, cc in cells:
                                self.grid[cr][cc] = 'S'
                                self.hit_cells.discard((cr, cc))
                            self.remaining_ships.remove(l)
                            updated = True
                            break

        probs = {cell: (count[cell] / total if total > 0 else 0) for cell in self.possible_targets}
        if not probs:
            return None, sunk_coords
        max_p = max(probs.values())
        candidates = [c for c, p in probs.items() if p == max_p]
        target = random.choice(candidates)
        return target, sunk_coords
