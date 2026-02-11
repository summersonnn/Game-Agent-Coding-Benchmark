"""
Agent Code: A1-Battleship
Model: anthropic/claude-opus-4.6
Run: 2
Generated: 2026-02-11 19:27:56
"""


class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.shots_fired = set()
        self.hits = set()
        self.misses = set()
        self.hit_queue = deque()
        self.sunk_cells = set()
        self.remaining_ships = list(ships)

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)

    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        bs = self.board_size

        best_placements = []
        for r in range(bs):
            for c in range(bs):
                for orient in ['horizontal', 'vertical']:
                    if orient == 'horizontal':
                        if c + ship_length > bs:
                            continue
                        cells = [(r, c + i) for i in range(ship_length)]
                    else:
                        if r + ship_length > bs:
                            continue
                        cells = [(r + i, c) for i in range(ship_length)]
                    if all(board[cr][cc] == 'O' for cr, cc in cells):
                        edge_dist = min(r, c, bs - 1 - r, bs - 1 - c)
                        best_placements.append((edge_dist, orient, r, c))

        if not best_placements:
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                return {'ship_length': ship_length, 'start': (random.randint(0, bs-1), random.randint(0, bs-ship_length)), 'orientation': orientation}
            else:
                return {'ship_length': ship_length, 'start': (random.randint(0, bs-ship_length), random.randint(0, bs-1)), 'orientation': orientation}

        random.shuffle(best_placements)
        best_placements.sort(key=lambda x: -x[0])
        top = best_placements[:max(1, len(best_placements)//3)]
        chosen = random.choice(top)
        return {
            'ship_length': ship_length,
            'start': (chosen[2], chosen[3]),
            'orientation': chosen[1]
        }

    def _bomb(self, state):
        self._sync_history(state)

        target = self._hunt_target()
        if target:
            return {'target': target}

        target = self._probability_target()
        return {'target': target}

    def _sync_history(self, state):
        self.shots_fired.clear()
        self.hits.clear()
        self.misses.clear()
        for entry in state.get('shot_history', []):
            coord = tuple(entry['coord'])
            self.shots_fired.add(coord)
            if entry['result'] == 'HIT':
                self.hits.add(coord)
            else:
                self.misses.add(coord)

        self._detect_sunk_ships()
        unsunk_hits = self.hits - self.sunk_cells

        self.hit_queue.clear()
        for h in unsunk_hits:
            self.hit_queue.append(h)

    def _detect_sunk_ships(self):
        unsunk = self.hits - self.sunk_cells
        if not unsunk:
            return

        groups = self._find_hit_groups(unsunk)
        remaining = list(self.remaining_ships)

        for group in sorted(groups, key=len, reverse=True):
            if len(group) in remaining:
                rows = {r for r, c in group}
                cols = {c for r, c in group}
                is_line = len(rows) == 1 or len(cols) == 1

                if is_line:
                    if len(rows) == 1:
                        cs = sorted(c for _, c in group)
                        r = list(rows)[0]
                        left = cs[0] - 1
                        right = cs[-1] + 1
                        bounded_left = left < 0 or (r, left) in self.misses or (r, left) in self.sunk_cells
                        bounded_right = right >= self.board_size or (r, right) in self.misses or (r, right) in self.sunk_cells
                        if bounded_left and bounded_right:
                            self.sunk_cells.update(group)
                            remaining.remove(len(group))
                    else:
                        rs = sorted(r for r, _ in group)
                        c = list(cols)[0]
                        top = rs[0] - 1
                        bottom = rs[-1] + 1
                        bounded_top = top < 0 or (top, c) in self.misses or (top, c) in self.sunk_cells
                        bounded_bottom = bottom >= self.board_size or (bottom, c) in self.misses or (bottom, c) in self.sunk_cells
                        if bounded_top and bounded_bottom:
                            self.sunk_cells.update(group)
                            remaining.remove(len(group))

        self.remaining_ships = remaining

    def _find_hit_groups(self, hits):
        visited = set()
        groups = []
        for h in hits:
            if h in visited:
                continue
            group = []
            stack = [h]
            while stack:
                cell = stack.pop()
                if cell in visited or cell not in hits:
                    continue
                visited.add(cell)
                group.append(cell)
                r, c = cell
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if (nr, nc) in hits and (nr, nc) not in visited:
                        stack.append((nr, nc))
            groups.append(group)
        return groups

    def _hunt_target(self):
        unsunk = self.hits - self.sunk_cells
        if not unsunk:
            return None

        groups = self._find_hit_groups(unsunk)
        for group in sorted(groups, key=len, reverse=True):
            rows = {r for r, c in group}
            cols = {c for r, c in group}

            targets = []
            if len(group) == 1:
                r, c = group[0]
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) not in self.shots_fired:
                        targets.append((nr, nc))
            elif len(rows) == 1:
                r = list(rows)[0]
                cs = sorted(c for _, c in group)
                for nc in [cs[0]-1, cs[-1]+1]:
                    if 0 <= nc < self.board_size and (r, nc) not in self.shots_fired:
                        targets.append((r, nc))
            elif len(cols) == 1:
                c = list(cols)[0]
                rs = sorted(r for r, _ in group)
                for nr in [rs[0]-1, rs[-1]+1]:
                    if 0 <= nr < self.board_size and (nr, c) not in self.shots_fired:
                        targets.append((nr, c))
            else:
                for r, c in group:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) not in self.shots_fired:
                            targets.append((nr, nc))

            if targets:
                return random.choice(targets)
        return None

    def _probability_target(self):
        bs = self.board_size
        prob = [[0]*bs for _ in range(bs)]

        for ship_len in self.remaining_ships:
            for r in range(bs):
                for c in range(bs):
                    for dr, dc in [(0,1),(1,0)]:
                        cells = []
                        valid = True
                        for i in range(ship_len):
                            nr, nc = r + dr*i, c + dc*i
                            if nr >= bs or nc >= bs or (nr, nc) in self.shots_fired:
                                valid = False
                                break
                            cells.append((nr, nc))
                        if valid:
                            for cr, cc in cells:
                                prob[cr][cc] += 1

        best_score = -1
        best_cells = []
        for r in range(bs):
            for c in range(bs):
                if (r, c) in self.shots_fired:
                    continue
                if prob[r][c] > best_score:
                    best_score = prob[r][c]
                    best_cells = [(r, c)]
                elif prob[r][c] == best_score:
                    best_cells.append((r, c))

        if best_cells:
            return random.choice(best_cells)

        for r in range(bs):
            for c in range(bs):
                if (r, c) not in self.shots_fired:
                    return (r, c)
        return (0, 0)