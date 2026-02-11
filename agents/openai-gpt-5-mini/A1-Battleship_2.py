"""
Agent Code: A1-Battleship
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-11 19:24:56
"""



class BattleshipAgent:
    """
    Smart Battleship agent implementing:
    - Constrained, non-overlapping ship placement with spacing heuristic
    - Hunt + Target bombing strategy with a probability heatmap (hunt)
      and focused adjacency targeting (target)
    """

    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = list(ships)[:]              # original ship list
        self.remaining_ships = list(ships)[:]    # track ships not yet deduced sunk (lengths)
        # Opponent board view: 'U' = unknown, 'M' = miss, 'H' = hit, 'S' = sunk (deduced)
        self.opp_board = [['U' for _ in range(board_size)] for _ in range(board_size)]
        # Track sunk coordinates so we don't re-process
        self.sunk_cells = set()
        # Use a deterministic random seed derived from name for reproducible behavior
        try:
            seed = abs(hash(name)) % (2**32)
        except Exception:
            seed = None
        self.rand = random.Random(seed)
        # convenience
        self.DIRS = [(-1, 0), (0, 1), (1, 0), (0, -1)]

    # --------------------
    # Public entrypoint
    # --------------------
    def make_move(self, state, feedback):
        phase = state.get('phase')
        if phase == 'placement':
            return self._place_ship(state)
        elif phase == 'bombing':
            return self._bomb(state)
        else:
            # Fallback (shouldn't happen)
            return {'target': (self.rand.randint(0, self.board_size - 1),
                               self.rand.randint(0, self.board_size - 1))}

    # --------------------
    # Placement logic
    # --------------------
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state.get('my_board')
        N = self.board_size

        # Gather coordinates already occupied by our ships
        placed = [(r, c) for r in range(N) for c in range(N) if my_board[r][c] == 'S']

        # Build list of all valid placements (start, orientation)
        candidates = []
        # Horizontal placements
        for r in range(N):
            for c in range(N - ship_length + 1):
                cells = [(r, c + k) for k in range(ship_length)]
                if any(my_board[cr][cc] == 'S' for cr, cc in cells):
                    continue
                candidates.append((r, c, 'horizontal', cells))
        # Vertical placements
        for r in range(N - ship_length + 1):
            for c in range(N):
                cells = [(r + k, c) for k in range(ship_length)]
                if any(my_board[cr][cc] == 'S' for cr, cc in cells):
                    continue
                candidates.append((r, c, 'vertical', cells))

        # If no candidates (unlikely), fallback to a random valid position ignoring spacing
        if not candidates:
            orientation = self.rand.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = self.rand.randint(0, N - 1)
                col = self.rand.randint(0, N - ship_length)
            else:
                row = self.rand.randint(0, N - ship_length)
                col = self.rand.randint(0, N - 1)
            return {'ship_length': ship_length, 'start': (row, col), 'orientation': orientation}

        # Score placements to spread ships out: maximize minimum Manhattan distance to existing ships
        def placement_score(cells):
            if not placed:
                # Prefer edges slightly for the first ship (to avoid easy predictable center)
                avg_r = sum(r for r, _ in cells) / len(cells)
                avg_c = sum(c for _, c in cells) / len(cells)
                center_r = (N - 1) / 2.0
                center_c = (N - 1) / 2.0
                dist_to_center = abs(avg_r - center_r) + abs(avg_c - center_c)
                return dist_to_center  # prefer away from center slightly
            # compute minimal distance from any candidate cell to any placed cell
            min_dist = min(
                abs(cr - pr) + abs(cc - pc)
                for cr, cc in cells
                for pr, pc in placed
            )
            return min_dist

        # Score and pick top candidates (with some randomness among top choice)
        scored = []
        best_score = None
        for r, c, orient, cells in candidates:
            sc = placement_score(cells)
            scored.append((sc, (r, c, orient)))
            if best_score is None or sc > best_score:
                best_score = sc

        top_choices = [entry for sc, entry in scored if sc >= best_score]
        start_r, start_c, orientation = self.rand.choice(top_choices)

        return {
            'ship_length': ship_length,
            'start': (start_r, start_c),
            'orientation': orientation
        }

    # --------------------
    # Bombing logic
    # --------------------
    def _bomb(self, state):
        N = self.board_size

        # Update opponent board from shot_history
        history = state.get('shot_history', [])
        # Use the shot_history as authoritative and update our opp_board
        for shot in history:
            (r, c) = shot['coord']
            res = shot['result']
            if res == 'HIT':
                self.opp_board[r][c] = 'H'
            else:
                self.opp_board[r][c] = 'M'

        # Also ensure last_shot_coord/result synchronized if present (safe, idempotent)
        last_coord = state.get('last_shot_coord')
        last_res = state.get('last_shot_result')
        if last_coord is not None and last_res is not None:
            lr, lc = last_coord
            if last_res == 'HIT':
                self.opp_board[lr][lc] = 'H'
            else:
                # Could be 'MISS' or if they report 'HIT' only; treat any non-HIT as MISS
                self.opp_board[lr][lc] = 'M'

        # Try to detect sunk ships from hit clusters and update remaining_ships
        self._detect_and_mark_sunk()

        # If there are live hits (H) not marked as sunk, enter target mode to finish them
        target = self._target_mode_choice()
        if target is None:
            # Hunt mode: use probability heatmap over remaining ships
            target = self._hunt_mode_choice()

        # Final safety: if still None (all cells targeted or unforeseen case), pick a random unknown
        if target is None:
            unknowns = [(r, c) for r in range(N) for c in range(N) if self.opp_board[r][c] == 'U']
            if unknowns:
                target = self.rand.choice(unknowns)
            else:
                # As last resort pick any cell (should not happen)
                target = (self.rand.randint(0, N - 1), self.rand.randint(0, N - 1))

        return {'target': target}

    # --------------------
    # Helper: detect sunk clusters
    # --------------------
    def _detect_and_mark_sunk(self):
        N = self.board_size
        visited = [[False] * N for _ in range(N)]

        # utility to check if a placement (straight segment) of length L starting at (r,c) horizontal/vertical
        def placement_fits_segment(cells, L, orient):
            # cells is list of coordinates of cluster; check whether exists a start such that segment of length L covers them
            if orient == 'horizontal':
                r = cells[0][0]
                cols = sorted([c for _, c in cells])
                min_col, max_col = cols[0], cols[-1]
                # possible start columns that cover cluster
                start_min = max(0, max_col - L + 1)
                start_max = min(min_col, N - L)
                for start_c in range(start_min, start_max + 1):
                    ok = True
                    for k in range(L):
                        rr, cc = r, start_c + k
                        val = self.opp_board[rr][cc]
                        if val == 'M' or val == 'S':  # can't include miss or already sunk cell
                            ok = False
                            break
                    if ok:
                        return True
                return False
            else:  # vertical
                c = cells[0][1]
                rows = sorted([r for r, _ in cells])
                min_row, max_row = rows[0], rows[-1]
                start_min = max(0, max_row - L + 1)
                start_max = min(min_row, N - L)
                for start_r in range(start_min, start_max + 1):
                    ok = True
                    for k in range(L):
                        rr, cc = start_r + k, c
                        val = self.opp_board[rr][cc]
                        if val == 'M' or val == 'S':
                            ok = False
                            break
                    if ok:
                        return True
                return False

        # gather components of 'H'
        for r in range(N):
            for c in range(N):
                if self.opp_board[r][c] != 'H' or visited[r][c]:
                    continue
                # BFS/DFS to get connected component of Hs
                stack = [(r, c)]
                comp = []
                visited[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in self.DIRS:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < N and 0 <= nc < N and not visited[nr][nc] and self.opp_board[nr][nc] == 'H':
                            visited[nr][nc] = True
                            stack.append((nr, nc))

                comp_set = set(comp)
                # Skip if we already marked these as sunk earlier
                if comp_set & self.sunk_cells:
                    continue

                comp_len = len(comp)
                # Determine orientation possibility (horizontal/vertical/unknown)
                rows = set(r0 for r0, _ in comp)
                cols = set(c0 for _, c0 in comp)
                orient_candidates = []
                if len(rows) == 1:
                    orient_candidates.append('horizontal')
                if len(cols) == 1:
                    orient_candidates.append('vertical')
                if not orient_candidates:
                    # ambiguous (e.g., touching ships), consider both orientations as possibilities
                    orient_candidates = ['horizontal', 'vertical']

                # Check if this component could still be part of any remaining (unsunk) ship
                possible = False
                for L in self.remaining_ships:
                    if L < comp_len:
                        continue
                    for orient in orient_candidates:
                        if placement_fits_segment(comp, L, orient):
                            possible = True
                            break
                    if possible:
                        break

                # If no possible placement for any remaining ship, component must be sunk
                if not possible:
                    # mark sunk cells
                    for (sr, sc) in comp:
                        self.opp_board[sr][sc] = 'S'
                        self.sunk_cells.add((sr, sc))
                    # Attempt to remove the ship of this size from remaining_ships.
                    # Prefer exact match by length if available.
                    removed = False
                    if comp_len in self.remaining_ships:
                        self.remaining_ships.remove(comp_len)
                        removed = True
                    else:
                        # fallback: try to remove any ship equal to the component length (rare); otherwise remove largest ship <= comp_len
                        cand = None
                        for L in sorted(self.remaining_ships):
                            if L <= comp_len:
                                cand = L
                        if cand is not None:
                            try:
                                self.remaining_ships.remove(cand)
                                removed = True
                            except ValueError:
                                removed = False
                    # If we couldn't find an appropriate length, don't modify remaining_ships (conservative)

    # --------------------
    # Target mode: finish off detected hits
    # --------------------
    def _target_mode_choice(self):
        N = self.board_size
        # find current clusters of 'H' not marked sunk
        visited = [[False] * N for _ in range(N)]
        clusters = []
        for r in range(N):
            for c in range(N):
                if self.opp_board[r][c] == 'H' and not visited[r][c]:
                    stack = [(r, c)]
                    visited[r][c] = True
                    comp = []
                    while stack:
                        cr, cc = stack.pop()
                        comp.append((cr, cc))
                        for dr, dc in self.DIRS:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < N and 0 <= nc < N and not visited[nr][nc] and self.opp_board[nr][nc] == 'H':
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                    clusters.append(comp)

        if not clusters:
            return None

        # evaluate candidate adjacent cells for each cluster
        candidates = []  # list of tuples (score, (r,c))
        for comp in clusters:
            comp_set = set(comp)
            # Determine orientation if possible
            rows = set(r0 for r0, _ in comp)
            cols = set(c0 for _, c0 in comp)
            if len(rows) == 1:
                orientation = 'horizontal'
            elif len(cols) == 1:
                orientation = 'vertical'
            else:
                orientation = None  # unknown

            if orientation == 'horizontal':
                r0 = comp[0][0]
                cols_sorted = sorted(c for _, c in comp)
                left = cols_sorted[0] - 1
                right = cols_sorted[-1] + 1
                ends = []
                if 0 <= left < N and self.opp_board[r0][left] == 'U':
                    ends.append((r0, left))
                if 0 <= right < N and self.opp_board[r0][right] == 'U':
                    ends.append((r0, right))
                for (er, ec) in ends:
                    score = self._direction_free_run(er, ec, (0, 1 if ec > cols_sorted[0] else -1))
                    candidates.append((score + 100 * len(comp), (er, ec)))  # prefer longer clusters
            elif orientation == 'vertical':
                c0 = comp[0][1]
                rows_sorted = sorted(r for r, _ in comp)
                top = rows_sorted[0] - 1
                bottom = rows_sorted[-1] + 1
                ends = []
                if 0 <= top < N and self.opp_board[top][c0] == 'U':
                    ends.append((top, c0))
                if 0 <= bottom < N and self.opp_board[bottom][c0] == 'U':
                    ends.append((bottom, c0))
                for (er, ec) in ends:
                    score = self._direction_free_run(er, ec, (1 if er > rows_sorted[0] else -1, 0))
                    candidates.append((score + 100 * len(comp), (er, ec)))
            else:
                # single or ambiguous hits: try all four neighbors
                (hr, hc) = comp[0]
                for dr, dc in self.DIRS:
                    nr, nc = hr + dr, hc + dc
                    if 0 <= nr < N and 0 <= nc < N and self.opp_board[nr][nc] == 'U':
                        score = self._direction_free_run(nr, nc, (dr, dc))
                        candidates.append((score + 100 * len(comp), (nr, nc)))

        # choose best candidate by score; tie-break randomly
        if not candidates:
            return None
        # sort candidates and pick top score group
        candidates.sort(reverse=True, key=lambda x: x[0])
        top_score = candidates[0][0]
        top_choices = [coord for sc, coord in candidates if sc == top_score]
        return self.rand.choice(top_choices)

    # helper to estimate free run length in a specific direction starting at (r,c)
    def _direction_free_run(self, r, c, direction):
        dr, dc = direction
        N = self.board_size
        run = 0
        rr, cc = r, c
        while 0 <= rr < N and 0 <= cc < N:
            if self.opp_board[rr][cc] == 'U':
                run += 1
            elif self.opp_board[rr][cc] == 'H':
                # treat H as free (may already be part of cluster)
                run += 1
            else:
                break
            rr += dr
            cc += dc
        return run

    # --------------------
    # Hunt mode: compute probability heatmap
    # --------------------
    def _hunt_mode_choice(self):
        N = self.board_size
        # create heatmap counts
        counts = [[0] * N for _ in range(N)]

        # If no remaining ships (edge case), just pick random unknown
        if not self.remaining_ships:
            unknowns = [(r, c) for r in range(N) for c in range(N) if self.opp_board[r][c] == 'U']
            return self.rand.choice(unknowns) if unknowns else None

        for L in self.remaining_ships:
            # horizontal placements
            for r in range(N):
                for c in range(N - L + 1):
                    ok = True
                    for k in range(L):
                        val = self.opp_board[r][c + k]
                        if val == 'M' or val == 'S':
                            ok = False
                            break
                    if not ok:
                        continue
                    # placement valid => add to counts for unknown cells (and hits if any)
                    for k in range(L):
                        if self.opp_board[r][c + k] == 'U':
                            counts[r][c + k] += 1
            # vertical placements
            for c in range(N):
                for r in range(N - L + 1):
                    ok = True
                    for k in range(L):
                        val = self.opp_board[r + k][c]
                        if val == 'M' or val == 'S':
                            ok = False
                            break
                    if not ok:
                        continue
                    for k in range(L):
                        if self.opp_board[r + k][c] == 'U':
                            counts[r + k][c] += 1

        # choose the unknown cell with maximum count
        max_count = 0
        best_cells = []
        for r in range(N):
            for c in range(N):
                if self.opp_board[r][c] != 'U':
                    continue
                if counts[r][c] > max_count:
                    max_count = counts[r][c]
                    best_cells = [(r, c)]
                elif counts[r][c] == max_count:
                    best_cells.append((r, c))

        if best_cells and max_count > 0:
            return self.rand.choice(best_cells)
        # If all counts zero (rare), fallback to parity-based heuristic to spread shots:
        # Use pattern based on smallest remaining ship length to maximize chance
        smallest = min(self.remaining_ships) if self.remaining_ships else 2
        candidates = []
        for r in range(N):
            for c in range(N):
                if self.opp_board[r][c] != 'U':
                    continue
                if ((r + c) % smallest) == 0:
                    candidates.append((r, c))
        if candidates:
            return self.rand.choice(candidates)
        # final fallback: any unknown
        unknowns = [(r, c) for r in range(N) for c in range(N) if self.opp_board[r][c] == 'U']
        return self.rand.choice(unknowns) if unknowns else None
