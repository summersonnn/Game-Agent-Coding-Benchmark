"""
Agent Code: A1-Battleship
Model: openai/gpt-5.2-codex
Run: 2
Generated: 2026-02-11 19:37:45
"""



class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = list(ships)
        self.directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        self.reset()

    def reset(self):
        self.shots = set()
        self.hits = set()
        self.misses = set()
        self.hunt_parity = random.choice([0, 1])

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            if state.get('ships_placed', 0) == 0:
                self.reset()
            ship_length = state['ships_to_place'][0]
            return self._place_ship(state['my_board'], ship_length)
        else:  # bombing phase
            self._update_from_history(state['shot_history'])
            clusters = self._hit_clusters()
            remaining = self._compute_remaining_ships(clusters)
            candidates = self._get_target_candidates(clusters, remaining)
            if candidates:
                target = self._select_candidate(candidates)
            else:
                target = self._hunt_target(remaining)
            return {'target': target}

    # ------------------------ Placement Logic ------------------------ #
    def _place_ship(self, board, length):
        size = self.board_size
        placements = []
        placements_relaxed = []

        for orientation in ('horizontal', 'vertical'):
            if orientation == 'horizontal':
                max_r, max_c = size, size - length + 1
            else:
                max_r, max_c = size - length + 1, size

            for r in range(max_r):
                for c in range(max_c):
                    if orientation == 'horizontal':
                        coords = [(r, c + i) for i in range(length)]
                    else:
                        coords = [(r + i, c) for i in range(length)]

                    if any(board[rr][cc] != 'O' for rr, cc in coords):
                        continue

                    if self._adjacent_conflict(board, coords):
                        placements_relaxed.append((orientation, r, c, coords))
                    else:
                        placements.append((orientation, r, c, coords))

        if placements:
            orientation, r, c = self._choose_placement(placements)
        elif placements_relaxed:
            orientation, r, c = self._choose_placement(placements_relaxed)
        else:
            # Fallback random placement (should rarely happen)
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                r = random.randint(0, size - 1)
                c = random.randint(0, size - length)
            else:
                r = random.randint(0, size - length)
                c = random.randint(0, size - 1)

        return {'ship_length': length, 'start': (r, c), 'orientation': orientation}

    def _adjacent_conflict(self, board, coords):
        size = self.board_size
        for r, c in coords:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < size and 0 <= nc < size:
                        if board[nr][nc] == 'S':
                            return True
        return False

    def _edge_score(self, coords):
        size = self.board_size
        return sum(min(r, size - 1 - r, c, size - 1 - c) for r, c in coords)

    def _choose_placement(self, placements):
        scored = [(self._edge_score(coords), o, r, c) for o, r, c, coords in placements]
        min_score = min(s for s, _, _, _ in scored)
        candidates = [(o, r, c) for s, o, r, c in scored if s <= min_score + 1]
        return random.choice(candidates)

    # ------------------------ Bombing Logic ------------------------ #
    def _update_from_history(self, shot_history):
        self.shots.clear()
        self.hits.clear()
        self.misses.clear()
        for entry in shot_history:
            coord = tuple(entry['coord'])
            self.shots.add(coord)
            if entry['result'] == 'HIT':
                self.hits.add(coord)
            else:
                self.misses.add(coord)

    def _hit_clusters(self):
        clusters = []
        visited = set()
        for cell in self.hits:
            if cell in visited:
                continue
            stack = [cell]
            cluster = []
            visited.add(cell)
            while stack:
                r, c = stack.pop()
                cluster.append((r, c))
                for dr, dc in self.directions:
                    nb = (r + dr, c + dc)
                    if nb in self.hits and nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            clusters.append(cluster)
        return clusters

    def _cluster_orientation(self, cluster):
        if len(cluster) <= 1:
            return None
        rows = {r for r, _ in cluster}
        cols = {c for _, c in cluster}
        if len(rows) == 1:
            return 'horizontal'
        if len(cols) == 1:
            return 'vertical'
        return None

    def _cluster_closed(self, cluster):
        orient = self._cluster_orientation(cluster)
        size = self.board_size
        if orient == 'horizontal':
            row = cluster[0][0]
            cols = [c for _, c in cluster]
            minc, maxc = min(cols), max(cols)
            left_block = (minc - 1 < 0) or ((row, minc - 1) in self.shots)
            right_block = (maxc + 1 >= size) or ((row, maxc + 1) in self.shots)
            return left_block and right_block
        elif orient == 'vertical':
            col = cluster[0][1]
            rows = [r for r, _ in cluster]
            minr, maxr = min(rows), max(rows)
            up_block = (minr - 1 < 0) or ((minr - 1, col) in self.shots)
            down_block = (maxr + 1 >= size) or ((maxr + 1, col) in self.shots)
            return up_block and down_block
        return False

    def _compute_remaining_ships(self, clusters):
        remaining = list(self.ships)
        for cluster in clusters:
            if self._cluster_closed(cluster):
                length = len(cluster)
                if length in remaining:
                    remaining.remove(length)
        return remaining

    def _count_open(self, r, c, dr, dc):
        count = 0
        size = self.board_size
        nr, nc = r + dr, c + dc
        while 0 <= nr < size and 0 <= nc < size and (nr, nc) not in self.misses:
            count += 1
            nr += dr
            nc += dc
        return count

    def _get_target_candidates(self, clusters, remaining):
        candidates = {}
        if not clusters:
            return candidates

        min_len = min(remaining) if remaining else min(self.ships)
        size = self.board_size

        for cluster in clusters:
            orient = self._cluster_orientation(cluster)
            cluster_size = len(cluster)

            if orient == 'horizontal':
                row = cluster[0][0]
                cols = [c for _, c in cluster]
                minc, maxc = min(cols), max(cols)
                left_space = self._count_open(row, minc, 0, -1)
                right_space = self._count_open(row, maxc, 0, 1)

                if minc - 1 >= 0 and (row, minc - 1) not in self.shots:
                    weight = 10 + cluster_size * 2 + left_space
                    candidates[(row, minc - 1)] = candidates.get((row, minc - 1), 0) + weight
                if maxc + 1 < size and (row, maxc + 1) not in self.shots:
                    weight = 10 + cluster_size * 2 + right_space
                    candidates[(row, maxc + 1)] = candidates.get((row, maxc + 1), 0) + weight

            elif orient == 'vertical':
                col = cluster[0][1]
                rows = [r for r, _ in cluster]
                minr, maxr = min(rows), max(rows)
                up_space = self._count_open(minr, col, -1, 0)
                down_space = self._count_open(maxr, col, 1, 0)

                if minr - 1 >= 0 and (minr - 1, col) not in self.shots:
                    weight = 10 + cluster_size * 2 + up_space
                    candidates[(minr - 1, col)] = candidates.get((minr - 1, col), 0) + weight
                if maxr + 1 < size and (maxr + 1, col) not in self.shots:
                    weight = 10 + cluster_size * 2 + down_space
                    candidates[(maxr + 1, col)] = candidates.get((maxr + 1, col), 0) + weight

            else:
                # Single hit or non-linear cluster
                if len(cluster) == 1:
                    r, c = cluster[0]
                    left = self._count_open(r, c, 0, -1)
                    right = self._count_open(r, c, 0, 1)
                    up = self._count_open(r, c, -1, 0)
                    down = self._count_open(r, c, 1, 0)

                    horiz_total = left + 1 + right
                    vert_total = up + 1 + down

                    added = False
                    if horiz_total >= min_len:
                        if c - 1 >= 0 and (r, c - 1) not in self.shots:
                            candidates[(r, c - 1)] = candidates.get((r, c - 1), 0) + (3 + left)
                            added = True
                        if c + 1 < size and (r, c + 1) not in self.shots:
                            candidates[(r, c + 1)] = candidates.get((r, c + 1), 0) + (3 + right)
                            added = True

                    if vert_total >= min_len:
                        if r - 1 >= 0 and (r - 1, c) not in self.shots:
                            candidates[(r - 1, c)] = candidates.get((r - 1, c), 0) + (3 + up)
                            added = True
                        if r + 1 < size and (r + 1, c) not in self.shots:
                            candidates[(r + 1, c)] = candidates.get((r + 1, c), 0) + (3 + down)
                            added = True

                    if not added:
                        for dr, dc in self.directions:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < size and 0 <= nc < size and (nr, nc) not in self.shots:
                                candidates[(nr, nc)] = candidates.get((nr, nc), 0) + 1
                else:
                    for r, c in cluster:
                        for dr, dc in self.directions:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < size and 0 <= nc < size and (nr, nc) not in self.shots:
                                weight = 1 + cluster_size
                                candidates[(nr, nc)] = candidates.get((nr, nc), 0) + weight

        return candidates

    def _select_candidate(self, candidates):
        max_w = max(candidates.values())
        best = [coord for coord, w in candidates.items() if w == max_w]
        return random.choice(best)

    def _hunt_target(self, remaining):
        size = self.board_size
        if not remaining:
            remaining = list(self.ships)

        grid = [[0] * size for _ in range(size)]
        for length in remaining:
            # horizontal placements
            for r in range(size):
                for c in range(size - length + 1):
                    if all((r, c + k) not in self.shots for k in range(length)):
                        for k in range(length):
                            grid[r][c + k] += 1
            # vertical placements
            for c in range(size):
                for r in range(size - length + 1):
                    if all((r + k, c) not in self.shots for k in range(length)):
                        for k in range(length):
                            grid[r + k][c] += 1

        max_val = -1
        best = []
        for r in range(size):
            for c in range(size):
                if (r, c) in self.shots:
                    continue
                val = grid[r][c]
                if val > max_val:
                    max_val = val
                    best = [(r, c)]
                elif val == max_val:
                    best.append((r, c))

        if not best:
            # Fallback random unshot cell
            choices = [(r, c) for r in range(size) for c in range(size) if (r, c) not in self.shots]
            return random.choice(choices) if choices else (0, 0)

        parity_best = [cell for cell in best if (cell[0] + cell[1]) % 2 == self.hunt_parity]
        if parity_best:
            return random.choice(parity_best)
        return random.choice(best)
