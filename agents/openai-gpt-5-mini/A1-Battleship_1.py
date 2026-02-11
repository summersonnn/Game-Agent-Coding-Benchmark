"""
Agent Code: A1-Battleship
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-11 19:24:56
"""



class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = list(ships)
        # remaining ships (lengths) we believe are still afloat on opponent
        self.remaining_ships = list(ships)
        # opponent knowledge grid: 0=unknown, 1=miss, 2=hit
        self.opp_state = [[0 for _ in range(board_size)] for _ in range(board_size)]
        # random generator
        self.rng = random.Random()
        self.rng.seed(time.time_ns() & 0xFFFFFFFF)

    # Utility
    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _neighbors4(self, r, c):
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            rr, cc = r+dr, c+dc
            if self._in_bounds(rr, cc):
                yield (rr, cc)

    # Placement: pick a random valid placement among candidates, bias to spread ships
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']
        candidates = []
        # horizontal placements
        for r in range(self.board_size):
            for c in range(self.board_size - ship_length + 1):
                ok = True
                for i in range(ship_length):
                    if my_board[r][c+i] == 'S':
                        ok = False
                        break
                if ok:
                    candidates.append((r, c, 'horizontal'))
        # vertical placements
        for r in range(self.board_size - ship_length + 1):
            for c in range(self.board_size):
                ok = True
                for i in range(ship_length):
                    if my_board[r+i][c] == 'S':
                        ok = False
                        break
                if ok:
                    candidates.append((r, c, 'vertical'))

        if not candidates:
            # fallback: should be rare, choose a random fit ignoring current board (penalty might occur if invalid)
            orientation = self.rng.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                r = self.rng.randint(0, self.board_size - 1)
                c = self.rng.randint(0, self.board_size - ship_length)
            else:
                r = self.rng.randint(0, self.board_size - ship_length)
                c = self.rng.randint(0, self.board_size - 1)
            return {'ship_length': ship_length, 'start': (r, c), 'orientation': orientation}

        # gather existing ship cells to try to spread ships
        existing = [(r, c) for r in range(self.board_size) for c in range(self.board_size) if my_board[r][c] == 'S']

        if existing:
            # score candidates by their minimal Manhattan distance to any existing ship cell (prefer larger)
            best_score = -1
            best_cands = []
            for (r, c, orient) in candidates:
                # compute candidate cells
                cells = []
                if orient == 'horizontal':
                    cells = [(r, c+i) for i in range(ship_length)]
                else:
                    cells = [(r+i, c) for i in range(ship_length)]
                # minimal distance from any candidate cell to any existing ship cell
                min_dist = min(abs(cr - er) + abs(cc - ec) for (cr,cc) in cells for (er,ec) in existing)
                if min_dist > best_score:
                    best_score = min_dist
                    best_cands = [(r, c, orient)]
                elif min_dist == best_score:
                    best_cands.append((r, c, orient))
            choice = self.rng.choice(best_cands)
        else:
            # no existing ships placed yet -> random candidate but bias away from edges slightly
            # randomly choose among candidates but prefer center positions
            def center_score(r, c, orient):
                if orient == 'horizontal':
                    cells = [(r, c+i) for i in range(ship_length)]
                else:
                    cells = [(r+i, c) for i in range(ship_length)]
                cx = (self.board_size - 1) / 2.0
                cy = (self.board_size - 1) / 2.0
                return -sum((cr - cx)**2 + (cc - cy)**2 for cr,cc in cells)  # prefer less distance -> higher score
            best_score = None
            best_cands = []
            for cand in candidates:
                s = center_score(*cand)
                if best_score is None or s > best_score:
                    best_score = s
                    best_cands = [cand]
                elif s == best_score:
                    best_cands.append(cand)
            choice = self.rng.choice(best_cands)

        r, c, orient = choice
        return {'ship_length': ship_length, 'start': (r, c), 'orientation': orient}

    # Build opponent state from shot_history
    def _rebuild_opp_state(self, shot_history):
        # reset
        self.opp_state = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        for shot in shot_history:
            r, c = shot['coord']
            if shot['result'] == 'HIT':
                self.opp_state[r][c] = 2
            else:
                # MISS (or any other reported miss-like)
                self.opp_state[r][c] = 1

    # get connected components of hits (orthogonally)
    def _get_hit_clusters(self):
        visited = [[False]*self.board_size for _ in range(self.board_size)]
        clusters = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.opp_state[r][c] == 2 and not visited[r][c]:
                    # BFS/DFS
                    stack = [(r, c)]
                    visited[r][c] = True
                    comp = []
                    while stack:
                        cr, cc = stack.pop()
                        comp.append((cr, cc))
                        for nr, nc in self._neighbors4(cr, cc):
                            if self.opp_state[nr][nc] == 2 and not visited[nr][nc]:
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                    clusters.append(comp)
        return clusters

    # deduce sunk ships and update remaining_ships list
    def _update_remaining_ships(self):
        clusters = self._get_hit_clusters()
        # try to deduce sunk ships: if a cluster cannot be extended (both ends blocked by misses or out of bounds)
        removed = []
        for comp in clusters:
            length = len(comp)
            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}
            # determine orientation if possible
            if len(rows) == 1:  # horizontal
                row = next(iter(rows))
                cols_list = sorted(c for _, c in comp)
                left = (row, cols_list[0] - 1)
                right = (row, cols_list[-1] + 1)
                left_blocked = (not self._in_bounds(*left)) or (self.opp_state[left[0]][left[1]] == 1)
                right_blocked = (not self._in_bounds(*right)) or (self.opp_state[right[0]][right[1]] == 1)
                if left_blocked and right_blocked:
                    # cluster cannot be extended
                    if length in self.remaining_ships and length not in removed:
                        removed.append(length)
            elif len(cols) == 1:  # vertical
                col = next(iter(cols))
                rows_list = sorted(r for r, _ in comp)
                up = (rows_list[0] - 1, col)
                down = (rows_list[-1] + 1, col)
                up_blocked = (not self._in_bounds(*up)) or (self.opp_state[up[0]][up[1]] == 1)
                down_blocked = (not self._in_bounds(*down)) or (self.opp_state[down[0]][down[1]] == 1)
                if up_blocked and down_blocked:
                    if length in self.remaining_ships and length not in removed:
                        removed.append(length)
            else:
                # single cell or weird shape: if all four neighbors are blocked, it must be a sunk length-1 (not in our game)
                r0, c0 = comp[0]
                blocked_all = True
                for nr, nc in self._neighbors4(r0, c0):
                    if self.opp_state[nr][nc] != 1:  # if any neighbor isn't a MISS it's not blocked
                        blocked_all = False
                        break
                if blocked_all:
                    if length in self.remaining_ships and length not in removed:
                        removed.append(length)
        # remove deduced sunk ships (only once each)
        for L in removed:
            try:
                self.remaining_ships.remove(L)
            except ValueError:
                pass

    # compute heatmap probabilities based on remaining ship placements
    def _compute_heatmap(self):
        size = self.board_size
        scores = [[0.0 for _ in range(size)] for _ in range(size)]
        # If no ships remaining, return zeroed map
        if not self.remaining_ships:
            return scores
        for L in self.remaining_ships:
            # horizontal placements
            for r in range(size):
                for c in range(size - L + 1):
                    valid = True
                    hits_covered = 0
                    for i in range(L):
                        cell = self.opp_state[r][c+i]
                        if cell == 1:  # MISS -> can't place here
                            valid = False
                            break
                        if cell == 2:
                            hits_covered += 1
                    if not valid:
                        continue
                    # weight placements that include known hits higher (to finish ships faster)
                    weight = 1.0 + 8.0 * hits_covered
                    for i in range(L):
                        if self.opp_state[r][c+i] == 0:
                            scores[r][c+i] += weight
            # vertical placements
            for r in range(size - L + 1):
                for c in range(size):
                    valid = True
                    hits_covered = 0
                    for i in range(L):
                        cell = self.opp_state[r+i][c]
                        if cell == 1:
                            valid = False
                            break
                        if cell == 2:
                            hits_covered += 1
                    if not valid:
                        continue
                    weight = 1.0 + 8.0 * hits_covered
                    for i in range(L):
                        if self.opp_state[r+i][c] == 0:
                            scores[r+i][c] += weight
        return scores

    # pick a target based on heatmap and hit clusters (target mode)
    def _select_target(self, state):
        shot_history = state.get('shot_history', [])
        self._rebuild_opp_state(shot_history)
        # update remaining ship deductions (sunk)
        self._update_remaining_ships()
        scores = self._compute_heatmap()

        # identify hit clusters
        clusters = self._get_hit_clusters()

        # try to pick a target adjacent to an active hit cluster (to finish ships)
        candidate_targets = []
        last_coord = state.get('last_shot_coord')
        # prefer cluster containing last shot coord if there's a hit
        prioritized_cluster = None
        if last_coord is not None:
            lr, lc = last_coord
            if self._in_bounds(lr, lc) and self.opp_state[lr][lc] == 2:
                for comp in clusters:
                    if (lr, lc) in comp:
                        prioritized_cluster = comp
                        break
        if prioritized_cluster is None and clusters:
            # choose the largest cluster (most promising)
            prioritized_cluster = max(clusters, key=lambda c: len(c))

        if prioritized_cluster:
            comp = prioritized_cluster
            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}
            if len(rows) == 1:
                # horizontal cluster: only extend left/right
                row = next(iter(rows))
                minc = min(c for _, c in comp)
                maxc = max(c for _, c in comp)
                ends = [(row, minc-1), (row, maxc+1)]
                for (rr, cc) in ends:
                    if self._in_bounds(rr, cc) and self.opp_state[rr][cc] == 0:
                        candidate_targets.append((rr, cc))
            elif len(cols) == 1:
                # vertical cluster: only extend up/down
                col = next(iter(cols))
                minr = min(r for r, _ in comp)
                maxr = max(r for r, _ in comp)
                ends = [(minr-1, col), (maxr+1, col)]
                for (rr, cc) in ends:
                    if self._in_bounds(rr, cc) and self.opp_state[rr][cc] == 0:
                        candidate_targets.append((rr, cc))
            else:
                # single hit or unusual shape: probe all neighbors
                for (rr, cc) in comp:
                    for nr, nc in self._neighbors4(rr, cc):
                        if self.opp_state[nr][nc] == 0:
                            candidate_targets.append((nr, nc))

            # remove duplicates
            candidate_targets = list({(r, c) for (r, c) in candidate_targets})

        # If no adjacent candidate (no hits or can't extend), use global heatmap
        if not candidate_targets:
            # pick highest score among unknown cells
            best_score = -1.0
            best_cells = []
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self.opp_state[r][c] != 0:
                        continue
                    sc = scores[r][c]
                    if sc > best_score:
                        best_score = sc
                        best_cells = [(r, c)]
                    elif sc == best_score:
                        best_cells.append((r, c))
            if best_cells:
                choice = self.rng.choice(best_cells)
                return {'target': choice}
            else:
                # No scored cells (rare) -> pick any unknown cell (random)
                unknowns = [(r, c) for r in range(self.board_size) for c in range(self.board_size) if self.opp_state[r][c] == 0]
                if not unknowns:
                    # everything has been shot at (shouldn't happen) -> pick random cell
                    return {'target': (self.rng.randint(0, self.board_size-1), self.rng.randint(0, self.board_size-1))}
                return {'target': self.rng.choice(unknowns)}
        else:
            # we have adjacent candidates -> pick the one with highest heatmap score (tie-break random)
            best_score = -1.0
            best_cells = []
            for (r, c) in candidate_targets:
                sc = scores[r][c]
                if sc > best_score:
                    best_score = sc
                    best_cells = [(r, c)]
                elif sc == best_score:
                    best_cells.append((r, c))
            if best_cells:
                return {'target': self.rng.choice(best_cells)}
            else:
                # fallback: choose any candidate
                return {'target': self.rng.choice(candidate_targets)}

    # Main entry
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._select_target(state)
