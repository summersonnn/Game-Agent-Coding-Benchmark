"""
Agent Code: A1-Battleship
Model: openai/gpt-5.2-codex
Run: 1
Generated: 2026-02-11 19:37:45
"""



class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = list(ships)
        self.dirs = [(1,0), (-1,0), (0,1), (0,-1)]

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)

    # ----------------- Placement ----------------- #
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        n = self.board_size
        placements = []

        # Collect all valid placements and score them
        for orientation in ['horizontal', 'vertical']:
            if orientation == 'horizontal':
                for r in range(n):
                    for c in range(n - ship_length + 1):
                        cells = [(r, c+i) for i in range(ship_length)]
                        if all(board[r][c+i] == 'O' for i in range(ship_length)):
                            adj = self._adjacency_score(board, cells)
                            placements.append((r, c, orientation, adj))
            else:
                for r in range(n - ship_length + 1):
                    for c in range(n):
                        cells = [(r+i, c) for i in range(ship_length)]
                        if all(board[r+i][c] == 'O' for i in range(ship_length)):
                            adj = self._adjacency_score(board, cells)
                            placements.append((r, c, orientation, adj))

        if not placements:
            # Fallback (shouldn't happen)
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                r = random.randint(0, n-1)
                c = random.randint(0, n-ship_length)
            else:
                r = random.randint(0, n-ship_length)
                c = random.randint(0, n-1)
            return {'ship_length': ship_length, 'start': (r, c), 'orientation': orientation}

        min_adj = min(p[3] for p in placements)
        best = [p for p in placements if p[3] == min_adj]
        r, c, orientation, _ = random.choice(best)

        return {'ship_length': ship_length, 'start': (r, c), 'orientation': orientation}

    def _adjacency_score(self, board, cells):
        # Prefer placements not adjacent (even diagonally) to existing ships
        n = self.board_size
        score = 0
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 'S':
                        score += 1
        return score

    # ----------------- Bombing ----------------- #
    def _bomb(self, state):
        shot_history = state['shot_history']
        hits, misses = self._build_sets(shot_history)
        shot_set = hits | misses

        clusters = self._find_clusters(hits)
        remaining = list(self.ships)
        sunk_hits = set()
        active_clusters = []

        for cluster in clusters:
            orientation = self._cluster_orientation(cluster)
            candidates = self._cluster_candidates(cluster, orientation, shot_set)
            if candidates:
                active_clusters.append((cluster, orientation, candidates))
            else:
                if self._is_cluster_closed(cluster, orientation, shot_set):
                    size = len(cluster)
                    if size in remaining:
                        remaining.remove(size)
                        sunk_hits.update(cluster)

        if active_clusters:
            target = self._choose_from_active(active_clusters, hits, misses, remaining)
        else:
            target = self._hunt_target(remaining, hits, misses, shot_set, sunk_hits)

        return {'target': target}

    def _build_sets(self, shot_history):
        hits = set()
        misses = set()
        for shot in shot_history:
            coord = tuple(shot['coord'])
            if shot['result'] == 'HIT':
                hits.add(coord)
                if coord in misses:
                    misses.remove(coord)
            else:
                if coord not in hits:
                    misses.add(coord)
        return hits, misses

    def _find_clusters(self, hits):
        clusters = []
        unvisited = set(hits)
        while unvisited:
            start = unvisited.pop()
            stack = [start]
            cluster = {start}
            while stack:
                r, c = stack.pop()
                for dr, dc in self.dirs:
                    nb = (r + dr, c + dc)
                    if nb in unvisited:
                        unvisited.remove(nb)
                        stack.append(nb)
                        cluster.add(nb)
            clusters.append(cluster)
        return clusters

    def _cluster_orientation(self, cluster):
        if len(cluster) <= 1:
            return None
        rows = {r for r, c in cluster}
        cols = {c for r, c in cluster}
        if len(rows) == 1:
            return 'horizontal'
        if len(cols) == 1:
            return 'vertical'
        return None  # ambiguous / non-linear

    def _cluster_candidates(self, cluster, orientation, shot_set):
        n = self.board_size
        candidates = set()
        if orientation == 'horizontal':
            row = next(iter({r for r, c in cluster}))
            cols = [c for r, c in cluster]
            min_c, max_c = min(cols), max(cols)
            if min_c - 1 >= 0 and (row, min_c - 1) not in shot_set:
                candidates.add((row, min_c - 1))
            if max_c + 1 < n and (row, max_c + 1) not in shot_set:
                candidates.add((row, max_c + 1))
        elif orientation == 'vertical':
            col = next(iter({c for r, c in cluster}))
            rows = [r for r, c in cluster]
            min_r, max_r = min(rows), max(rows)
            if min_r - 1 >= 0 and (min_r - 1, col) not in shot_set:
                candidates.add((min_r - 1, col))
            if max_r + 1 < n and (max_r + 1, col) not in shot_set:
                candidates.add((max_r + 1, col))
        else:
            for r, c in cluster:
                for dr, dc in self.dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in shot_set:
                        candidates.add((nr, nc))
        return list(candidates)

    def _is_cluster_closed(self, cluster, orientation, shot_set):
        n = self.board_size
        if orientation == 'horizontal':
            row = next(iter({r for r, c in cluster}))
            cols = [c for r, c in cluster]
            min_c, max_c = min(cols), max(cols)
            left_open = (min_c - 1 >= 0 and (row, min_c - 1) not in shot_set)
            right_open = (max_c + 1 < n and (row, max_c + 1) not in shot_set)
            return not (left_open or right_open)
        elif orientation == 'vertical':
            col = next(iter({c for r, c in cluster}))
            rows = [r for r, c in cluster]
            min_r, max_r = min(rows), max(rows)
            up_open = (min_r - 1 >= 0 and (min_r - 1, col) not in shot_set)
            down_open = (max_r + 1 < n and (max_r + 1, col) not in shot_set)
            return not (up_open or down_open)
        else:
            if len(cluster) == 1:
                r, c = next(iter(cluster))
                for dr, dc in self.dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in shot_set:
                        return False
                return True
            return False

    def _count_open(self, r, c, dr, dc, blocked):
        n = self.board_size
        count = 0
        nr, nc = r, c
        while 0 <= nr < n and 0 <= nc < n and (nr, nc) not in blocked:
            count += 1
            nr += dr
            nc += dc
        return count

    def _choose_from_active(self, active_clusters, hits, misses, remaining):
        best_score = -1
        best_targets = []

        for cluster, orientation, candidates in active_clusters:
            cluster_size = len(cluster)
            blocked = set(misses)
            blocked.update(hits - cluster)

            if orientation == 'horizontal':
                row = next(iter({r for r, c in cluster}))
                cols = [c for r, c in cluster]
                min_c, max_c = min(cols), max(cols)
                left_space = self._count_open(row, min_c - 1, 0, -1, blocked)
                right_space = self._count_open(row, max_c + 1, 0, 1, blocked)
                max_len = cluster_size + left_space + right_space
                fit = sum(1 for L in remaining if cluster_size <= L <= max_len)

                for cand in candidates:
                    space = left_space if cand[1] < min_c else right_space
                    score = 100 + cluster_size * 10 + space * 2 + fit
                    if score > best_score:
                        best_score = score
                        best_targets = [cand]
                    elif score == best_score:
                        best_targets.append(cand)

            elif orientation == 'vertical':
                col = next(iter({c for r, c in cluster}))
                rows = [r for r, c in cluster]
                min_r, max_r = min(rows), max(rows)
                up_space = self._count_open(min_r - 1, col, -1, 0, blocked)
                down_space = self._count_open(max_r + 1, col, 1, 0, blocked)
                max_len = cluster_size + up_space + down_space
                fit = sum(1 for L in remaining if cluster_size <= L <= max_len)

                for cand in candidates:
                    space = up_space if cand[0] < min_r else down_space
                    score = 100 + cluster_size * 10 + space * 2 + fit
                    if score > best_score:
                        best_score = score
                        best_targets = [cand]
                    elif score == best_score:
                        best_targets.append(cand)
            else:
                for cand in candidates:
                    best_line = 0
                    for hr, hc in cluster:
                        if abs(hr - cand[0]) + abs(hc - cand[1]) == 1:
                            if hr == cand[0]:
                                line_len = 1 + self._count_open(hr, hc - 1, 0, -1, blocked) + \
                                           self._count_open(hr, hc + 1, 0, 1, blocked)
                            else:
                                line_len = 1 + self._count_open(hr - 1, hc, -1, 0, blocked) + \
                                           self._count_open(hr + 1, hc, 1, 0, blocked)
                            best_line = max(best_line, line_len)
                    score = cluster_size * 5 + best_line
                    if score > best_score:
                        best_score = score
                        best_targets = [cand]
                    elif score == best_score:
                        best_targets.append(cand)

        if best_targets:
            return random.choice(best_targets)

        # Fallback random
        all_unknown = [(r, c) for r in range(self.board_size) for c in range(self.board_size)]
        return random.choice(all_unknown)

    def _hunt_target(self, remaining, hits, misses, shot_set, sunk_hits):
        n = self.board_size
        blocked = set(misses) | set(sunk_hits)

        if not remaining:
            # No ships left; just pick any unknown
            unknown = [(r, c) for r in range(n) for c in range(n) if (r, c) not in shot_set]
            return random.choice(unknown) if unknown else (0, 0)

        probs = [[0 for _ in range(n)] for _ in range(n)]

        for L in remaining:
            # Horizontal placements
            for r in range(n):
                for c in range(n - L + 1):
                    if any((r, c+i) in blocked for i in range(L)):
                        continue
                    for i in range(L):
                        probs[r][c+i] += 1
            # Vertical placements
            for r in range(n - L + 1):
                for c in range(n):
                    if any((r+i, c) in blocked for i in range(L)):
                        continue
                    for i in range(L):
                        probs[r+i][c] += 1

        best_score = -1
        best = []
        for r in range(n):
            for c in range(n):
                if (r, c) in shot_set:
                    continue
                score = probs[r][c]
                if score > best_score:
                    best_score = score
                    best = [(r, c)]
                elif score == best_score:
                    best.append((r, c))

        if not best:
            unknown = [(r, c) for r in range(n) for c in range(n) if (r, c) not in shot_set]
            return random.choice(unknown) if unknown else (0, 0)

        # Optional parity filter
        min_len = min(remaining) if remaining else 1
        if min_len > 1:
            parity_best = [coord for coord in best if (coord[0] + coord[1]) % 2 == 0]
            if parity_best:
                best = parity_best

        return random.choice(best)
