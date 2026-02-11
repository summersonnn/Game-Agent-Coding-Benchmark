"""
Agent Code: A1-Battleship
Model: anthropic/claude-opus-4.6
Run: 1
Generated: 2026-02-11 19:27:04
"""

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.shots_fired = set()
        self.hits = set()
        self.misses = set()
        self.hit_queue = []
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
        for row in range(bs):
            for col in range(bs):
                for ori in ['horizontal', 'vertical']:
                    if ori == 'horizontal':
                        if col + ship_length > bs:
                            continue
                        cells = [(row, col + i) for i in range(ship_length)]
                    else:
                        if row + ship_length > bs:
                            continue
                        cells = [(row + i, col) for i in range(ship_length)]
                    if all(board[r][c] == 'O' for r, c in cells):
                        edge_score = sum(1 for r, c in cells if r == 0 or r == bs-1 or c == 0 or c == bs-1)
                        best_placements.append((edge_score, row, col, ori))

        if not best_placements:
            return {'ship_length': ship_length, 'start': (0, 0), 'orientation': 'horizontal'}

        random.shuffle(best_placements)
        _, row, col, ori = min(best_placements, key=lambda x: x[0])

        return {'ship_length': ship_length, 'start': (row, col), 'orientation': ori}

    def _bomb(self, state):
        self._update_state(state)
        self._detect_sunk_ships()

        target = self._get_target_mode()
        if target:
            self.shots_fired.add(target)
            return {'target': target}

        target = self._hunt()
        self.shots_fired.add(target)
        return {'target': target}

    def _update_state(self, state):
        for entry in state.get('shot_history', []):
            coord = tuple(entry['coord'])
            self.shots_fired.add(coord)
            if entry['result'] == 'HIT':
                self.hits.add(coord)
            else:
                self.misses.add(coord)

    def _neighbors(self, r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                yield nr, nc

    def _detect_sunk_ships(self):
        unsunk_hits = self.hits - self.sunk_cells
        if not unsunk_hits:
            return

        groups = []
        visited = set()
        for h in unsunk_hits:
            if h in visited:
                continue
            group = []
            stack = [h]
            while stack:
                cell = stack.pop()
                if cell in visited or cell not in unsunk_hits:
                    continue
                visited.add(cell)
                group.append(cell)
                for nr, nc in self._neighbors(cell[0], cell[1]):
                    if (nr, nc) in unsunk_hits and (nr, nc) not in visited:
                        stack.append((nr, nc))
            groups.append(group)

        for group in groups:
            glen = len(group)
            if glen not in self.remaining_ships:
                continue
            is_line = self._is_line(group)
            if not is_line:
                continue
            if self._is_fully_bounded(group):
                self.sunk_cells.update(group)
                self.remaining_ships.remove(glen)

    def _is_line(self, group):
        if len(group) == 1:
            return True
        rows = {r for r, c in group}
        cols = {c for r, c in group}
        if len(rows) == 1:
            cols_sorted = sorted(cols)
            return cols_sorted[-1] - cols_sorted[0] == len(group) - 1
        if len(cols) == 1:
            rows_sorted = sorted(rows)
            return rows_sorted[-1] - rows_sorted[0] == len(group) - 1
        return False

    def _is_fully_bounded(self, group):
        rows = {r for r, c in group}
        cols = {c for r, c in group}
        group_set = set(group)
        if len(rows) == 1:
            row = list(rows)[0]
            min_c, max_c = min(cols), max(cols)
            before = (row, min_c - 1)
            after = (row, max_c + 1)
        elif len(cols) == 1:
            col = list(cols)[0]
            min_r, max_r = min(rows), max(rows)
            before = (min_r - 1, col)
            after = (max_r + 1, col)
        else:
            return False

        for endpoint in [before, after]:
            r, c = endpoint
            if 0 <= r < self.board_size and 0 <= c < self.board_size:
                if endpoint not in self.shots_fired:
                    return False
        return True

    def _get_target_mode(self):
        unsunk_hits = self.hits - self.sunk_cells
        if not unsunk_hits:
            return None

        groups = []
        visited = set()
        for h in unsunk_hits:
            if h in visited:
                continue
            group = []
            stack = [h]
            while stack:
                cell = stack.pop()
                if cell in visited or cell not in unsunk_hits:
                    continue
                visited.add(cell)
                group.append(cell)
                for nr, nc in self._neighbors(cell[0], cell[1]):
                    if (nr, nc) in unsunk_hits and (nr, nc) not in visited:
                        stack.append((nr, nc))
            groups.append(sorted(group))

        candidates = []
        for group in groups:
            if len(group) >= 2:
                rows = {r for r, c in group}
                cols = {c for r, c in group}
                if len(rows) == 1:
                    row = list(rows)[0]
                    min_c, max_c = min(cols), max(cols)
                    for c in [min_c - 1, max_c + 1]:
                        if 0 <= c < self.board_size and (row, c) not in self.shots_fired:
                            candidates.append((row, c))
                elif len(cols) == 1:
                    col = list(cols)[0]
                    min_r, max_r = min(rows), max(rows)
                    for r in [min_r - 1, max_r + 1]:
                        if 0 <= r < self.board_size and (r, col) not in self.shots_fired:
                            candidates.append((r, col))
            else:
                r, c = group[0]
                for nr, nc in self._neighbors(r, c):
                    if (nr, nc) not in self.shots_fired:
                        candidates.append((nr, nc))

        if candidates:
            return self._best_candidate(candidates)
        return None

    def _best_candidate(self, candidates):
        min_ship = min(self.remaining_ships) if self.remaining_ships else 1
        best = None
        best_score = -1
        for r, c in candidates:
            score = 0
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                length = 0
                nr, nc = r + dr, c + dc
                while 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) not in self.misses and (nr, nc) not in self.sunk_cells:
                    length += 1
                    nr += dr
                    nc += dc
                score += length
            if score > best_score:
                best_score = score
                best = (r, c)
        return best

    def _hunt(self):
        bs = self.board_size
        min_ship = min(self.remaining_ships) if self.remaining_ships else 1

        best = None
        best_score = -1

        for r in range(bs):
            for c in range(bs):
                if (r, c) in self.shots_fired:
                    continue
                if not self._can_fit_ship(r, c, min_ship):
                    continue
                score = self._cell_probability(r, c)
                if score > best_score:
                    best_score = score
                    best = (r, c)

        if best:
            return best
        for r in range(bs):
            for c in range(bs):
                if (r, c) not in self.shots_fired:
                    return (r, c)
        return (0, 0)

    def _can_fit_ship(self, r, c, min_len):
        for dr, dc in [(0,1),(1,0)]:
            for start in range(min_len):
                sr, sc = r - dr*start, c - dc*start
                fits = True
                for i in range(min_len):
                    nr, nc = sr + dr*i, sc + dc*i
                    if not (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                        fits = False
                        break
                    if (nr, nc) in self.misses or (nr, nc) in self.sunk_cells:
                        fits = False
                        break
                if fits:
                    return True
        return False

    def _cell_probability(self, r, c):
        score = 0
        for ship_len in self.remaining_ships:
            for dr, dc in [(0,1),(1,0)]:
                for start in range(ship_len):
                    sr, sc = r - dr*start, c - dc*start
                    valid = True
                    for i in range(ship_len):
                        nr, nc = sr + dr*i, sc + dc*i
                        if not (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                            valid = False
                            break
                        if (nr, nc) in self.misses or (nr, nc) in self.sunk_cells:
                            valid = False
                            break
                        if (nr, nc) in self.shots_fired and (nr, nc) not in self.hits:
                            valid = False
                            break
                    if valid:
                        score += 1
        return score