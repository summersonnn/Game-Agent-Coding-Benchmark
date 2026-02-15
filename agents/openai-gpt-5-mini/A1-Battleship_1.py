"""
Agent Code: A1-Battleship
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-14 16:35:39
"""



class BattleshipAgent:
    """
    Battleship agent with:
    - heuristic placement (spreads ships apart)
    - probability-based hunting
    - focused targeting to finish ships after hits
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships_initial = list(ships)[:]  # e.g. [5,4,3]
        # dynamic view of opponent ships (deduced)
        self.remaining_ships = list(self.ships_initial)
        # random generator (uses global random)
        self.rng = __import__('random')
        # Memory of last shot_history length to detect new information (not strictly required)
        self._last_history_len = 0

    # ---------------- Placement helpers ----------------
    def _valid_placements_for_length(self, my_board, length):
        N = self.board_size
        placements = []
        for r in range(N):
            for c in range(N - length + 1):
                ok = True
                for k in range(length):
                    if my_board[r][c + k] != 'O':
                        ok = False
                        break
                if ok:
                    placements.append(((r, c), 'horizontal'))
        for r in range(N - length + 1):
            for c in range(N):
                ok = True
                for k in range(length):
                    if my_board[r + k][c] != 'O':
                        ok = False
                        break
                if ok:
                    placements.append(((r, c), 'vertical'))
        return placements

    def _distance_to_existing_ships(self, cells, existing_cells):
        # return minimal Manhattan distance from any cell in 'cells' to any existing ship cell
        if not existing_cells:
            return None
        best = None
        for (r1, c1) in cells:
            for (r2, c2) in existing_cells:
                d = abs(r1 - r2) + abs(c1 - c2)
                if best is None or d < best:
                    best = d
        return best

    def _choose_placement(self, my_board, ship_length):
        N = self.board_size
        existing = [(r, c) for r in range(N) for c in range(N) if my_board[r][c] == 'S']
        candidates = self._valid_placements_for_length(my_board, ship_length)
        if not candidates:
            # fallback: choose any valid spot by brute force (shouldn't happen)
            orientation = self.rng.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = self.rng.randint(0, N - 1)
                col = self.rng.randint(0, N - ship_length)
            else:
                row = self.rng.randint(0, N - ship_length)
                col = self.rng.randint(0, N - 1)
            return (row, col), orientation

        scored = []
        center_r = (N - 1) / 2.0
        center_c = (N - 1) / 2.0
        for start, orient in candidates:
            r0, c0 = start
            cells = []
            if orient == 'horizontal':
                cells = [(r0, c0 + k) for k in range(ship_length)]
            else:
                cells = [(r0 + k, c0) for k in range(ship_length)]
            dist = self._distance_to_existing_ships(cells, existing)
            if dist is None:
                # no existing ships: score by distance from center (we want spread, so prefer away from center)
                avg_r = sum(r for r, _ in cells) / len(cells)
                avg_c = sum(c for _, c in cells) / len(cells)
                # prefer edges slightly by using distance from center
                score = abs(avg_r - center_r) + abs(avg_c - center_c)
            else:
                score = dist
            # small randomness to break ties
            score += self.rng.random() * 0.1
            scored.append((score, start, orient))
        scored.sort(key=lambda x: -x[0])
        top_score = scored[0][0]
        top_choices = [s for s in scored if abs(s[0] - top_score) < 1e-6 or s[0] >= top_score - 0.05]
        _, start, orient = self.rng.choice(top_choices)
        return start, orient

    # ---------------- Bombing helpers ----------------
    def _reconstruct_board_from_history(self, shot_history):
        N = self.board_size
        board = [['U' for _ in range(N)] for _ in range(N)]
        for entry in shot_history:
            (r, c) = entry['coord']
            if entry['result'] == 'HIT':
                board[r][c] = 'H'
            else:
                board[r][c] = 'M'
        return board

    def _deduce_sunk_ships(self, board, ships_list):
        """
        From current board 'H' and 'M' marks, attempt to deduce which ships are sunk.
        Returns (remaining_ships_list, sunk_cells_set)
        """
        N = self.board_size
        ships_remaining = list(ships_list[:])
        hits = {(r, c) for r in range(N) for c in range(N) if board[r][c] == 'H'}
        visited = set()
        sunk_cells = set()

        for (r, c) in sorted(hits):
            if (r, c) in visited:
                continue
            # find horizontal run
            left = c
            while left - 1 >= 0 and board[r][left - 1] == 'H':
                left -= 1
            right = c
            while right + 1 < N and board[r][right + 1] == 'H':
                right += 1
            horiz_len = right - left + 1
            horiz_cells = [(r, cc) for cc in range(left, right + 1)]

            # find vertical run
            up = r
            while up - 1 >= 0 and board[up - 1][c] == 'H':
                up -= 1
            down = r
            while down + 1 < N and board[down + 1][c] == 'H':
                down += 1
            vert_len = down - up + 1
            vert_cells = [(rr, c) for rr in range(up, down + 1)]

            # choose longer orientation (prefer horizontal on ties)
            if horiz_len >= vert_len:
                seg_cells = horiz_cells
                seg_len = horiz_len
                nei1 = (r, left - 1)
                nei2 = (r, right + 1)
            else:
                seg_cells = vert_cells
                seg_len = vert_len
                nei1 = (up - 1, c)
                nei2 = (down + 1, c)

            for cell in seg_cells:
                visited.add(cell)

            def blocked(nei):
                rr, cc = nei
                if rr < 0 or rr >= N or cc < 0 or cc >= N:
                    return True
                val = board[rr][cc]
                # treat misses or already-sunk inferred cells as blocking
                return val == 'M' or val == 'S'

            if blocked(nei1) and blocked(nei2):
                # cannot extend in this orientation -> if length matches a remaining ship, mark it sunk
                if seg_len in ships_remaining:
                    # remove one instance
                    ships_remaining.remove(seg_len)
                    for cell in seg_cells:
                        sunk_cells.add(cell)
        return ships_remaining, sunk_cells

    def _compute_probability_map(self, board, ships_remaining):
        N = self.board_size
        prob = [[0 for _ in range(N)] for _ in range(N)]
        # For each ship, simulate all placements that don't conflict with misses or known sunk cells.
        for length in ships_remaining:
            # horizontal placements
            for r in range(N):
                for c in range(0, N - length + 1):
                    valid = True
                    for k in range(length):
                        v = board[r][c + k]
                        if v == 'M' or v == 'S':
                            valid = False
                            break
                    if not valid:
                        continue
                    # This placement is possible; add weight
                    for k in range(length):
                        prob[r][c + k] += 1
            # vertical placements
            for c in range(N):
                for r in range(0, N - length + 1):
                    valid = True
                    for k in range(length):
                        v = board[r + k][c]
                        if v == 'M' or v == 'S':
                            valid = False
                            break
                    if not valid:
                        continue
                    for k in range(length):
                        prob[r + k][c] += 1
        return prob

    def _find_hit_clusters(self, board):
        N = self.board_size
        hits = {(r, c) for r in range(N) for c in range(N) if board[r][c] == 'H'}
        visited = set()
        clusters = []
        for cell in hits:
            if cell in visited:
                continue
            comp = set()
            stack = [cell]
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                comp.add(cur)
                r, c = cur
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < N and 0 <= nc < N and (nr, nc) in hits and (nr, nc) not in visited:
                        stack.append((nr, nc))
            clusters.append(comp)
        return clusters

    def _candidates_from_cluster(self, board, cluster):
        N = self.board_size
        candidates = []
        rows = {r for r, _ in cluster}
        cols = {c for _, c in cluster}
        # Determine orientation if possible
        if len(rows) == 1:
            # horizontal cluster
            r = next(iter(rows))
            minc = min(c for _, c in cluster)
            maxc = max(c for _, c in cluster)
            left = (r, minc - 1)
            right = (r, maxc + 1)
            for nr, nc in (left, right):
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 'U':
                    candidates.append((nr, nc))
            return candidates
        if len(cols) == 1:
            # vertical
            c = next(iter(cols))
            minr = min(r for r, _ in cluster)
            maxr = max(r for r, _ in cluster)
            up = (minr - 1, c)
            down = (maxr + 1, c)
            for nr, nc in (up, down):
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 'U':
                    candidates.append((nr, nc))
            return candidates
        # ambiguous cluster (hits touching but not in a line) -> target unknown neighbors around cells
        for (r, c) in cluster:
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 'U':
                    candidates.append((nr, nc))
        # remove duplicates while preserving order-ish
        uniq = []
        seen = set()
        for x in candidates:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _choose_target_from_probability(self, board, prob):
        # choose unknown cell with highest probability. Break ties randomly.
        N = self.board_size
        best_score = -1
        best_cells = []
        for r in range(N):
            for c in range(N):
                if board[r][c] != 'U':
                    continue
                score = prob[r][c]
                if score > best_score:
                    best_score = score
                    best_cells = [(r, c)]
                elif score == best_score:
                    best_cells.append((r, c))
        if not best_cells:
            # fallback to any unknown
            unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 'U']
            if unknowns:
                return self.rng.choice(unknowns)
            else:
                return (0, 0)
        return self.rng.choice(best_cells)

    # ---------------- Main move function ----------------
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            my_board = state.get('my_board')
            # Pick a spread-out placement
            start, orient = self._choose_placement(my_board, ship_length)
            orientation = 'horizontal' if orient == 'horizontal' else 'vertical'
            return {
                'ship_length': ship_length,
                'start': start,
                'orientation': orientation
            }

        # Bombing phase
        shot_history = state.get('shot_history', [])
        board = self._reconstruct_board_from_history(shot_history)

        # Deduce sunk ships and mark sunk cells as 'S' to block them from future placement calculations
        remaining, sunk_cells = self._deduce_sunk_ships(board, self.ships_initial)
        self.remaining_ships = remaining
        for (r, c) in sunk_cells:
            board[r][c] = 'S'

        # Build probability map
        prob = self._compute_probability_map(board, self.remaining_ships)

        # If there are active hits (not sunk), form target candidates
        clusters = self._find_hit_clusters(board)
        # Exclude clusters that are already fully marked as sunk via sunk_cells
        active_clusters = []
        for cluster in clusters:
            if not cluster.issubset(sunk_cells):
                # cluster has at least one active hit
                active_clusters.append(cluster)

        candidate_targets = []
        # prioritize the most recently created or largest cluster: pick cluster with most hits
        if active_clusters:
            # sort by size desc, then by recency isn't directly available, so just largest
            active_clusters.sort(key=lambda c: -len(c))
            # consider top two clusters as potential targets
            for cluster in active_clusters[:2]:
                candidate_targets.extend(self._candidates_from_cluster(board, cluster))

        # Score candidate targets by probability map and pick best if any
        chosen = None
        if candidate_targets:
            best_score = -1
            best_cells = []
            for (r, c) in candidate_targets:
                if board[r][c] != 'U':
                    continue
                score = prob[r][c]
                if score > best_score:
                    best_score = score
                    best_cells = [(r, c)]
                elif score == best_score:
                    best_cells.append((r, c))
            if best_cells:
                chosen = self.rng.choice(best_cells)

        # Fall back to highest-probability unknown cell
        if chosen is None:
            chosen = self._choose_target_from_probability(board, prob)

        return {'target': chosen}
