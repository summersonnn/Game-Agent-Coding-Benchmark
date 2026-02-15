"""
Agent Code: A1-Battleship
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-14 16:15:50
"""



class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = list(ships)

        # Precompute all placements for each ship length for speed.
        self._placements_by_len = {}
        for L in set(self.ships):
            self._placements_by_len[L] = self._all_placements(L)

    # ------------------------ Core Interface ------------------------

    def make_move(self, state, feedback):
        phase = state.get("phase")
        if phase == "placement":
            return self._place_ship(state)
        # phase == "bombing"
        return self._bomb(state)

    # ------------------------ Placement ------------------------

    def _place_ship(self, state):
        N = state["board_size"]
        board = state["my_board"]
        ship_length = state["ships_to_place"][0]

        existing = []
        for r in range(N):
            for c in range(N):
                if board[r][c] == "S":
                    existing.append((r, c))

        best = None
        best_score = None

        for placement in self._placements_by_len.get(ship_length, self._all_placements(ship_length)):
            # Validate (must not overlap).
            ok = True
            for (r, c) in placement:
                if board[r][c] != "O":
                    ok = False
                    break
            if not ok:
                continue

            score = self._placement_score(placement, existing, N)
            if best is None or score > best_score:
                best = placement
                best_score = score
            elif score == best_score and random.random() < 0.25:
                # Small randomness to avoid being predictable.
                best = placement

        # Convert best placement cells into (start, orientation).
        # Precomputed placements are generated from a start + orientation, but we can reconstruct easily.
        if best is None:
            # Extremely unlikely unless board is inconsistent; fall back to a safe default.
            return {"ship_length": ship_length, "start": (0, 0), "orientation": "horizontal"}

        start, orient = self._placement_to_start_orientation(best)
        return {"ship_length": ship_length, "start": start, "orientation": orient}

    def _placement_score(self, placement, existing_ship_cells, N):
        # Prefer edges + spacing ships apart (no-touch is a preference, not a rule).
        # Edge preference helps against many probability-based bombers that overweight center cells.
        edge_bonus = 0.0
        for (r, c) in placement:
            dist_to_edge = min(r, c, N - 1 - r, N - 1 - c)
            if dist_to_edge == 0:
                edge_bonus += 2.0
            elif dist_to_edge == 1:
                edge_bonus += 0.7
            else:
                edge_bonus += 0.0

        separation_bonus = 0.0
        if existing_ship_cells:
            # Maximize minimum Chebyshev distance to existing ships (diagonals count).
            min_d = 999
            for (r, c) in placement:
                for (er, ec) in existing_ship_cells:
                    d = max(abs(r - er), abs(c - ec))
                    if d < min_d:
                        min_d = d
            # Reward spacing more strongly for very close placements.
            separation_bonus = min(6.0, 1.5 * float(min_d))

        # Mild randomness to avoid identical layouts across games.
        noise = random.random() * 0.05
        return edge_bonus + separation_bonus + noise

    def _placement_to_start_orientation(self, placement):
        # placement is a list of (r,c) cells in either row-constant or col-constant order.
        rows = [p[0] for p in placement]
        cols = [p[1] for p in placement]
        if all(r == rows[0] for r in rows):
            r = rows[0]
            c = min(cols)
            return (r, c), "horizontal"
        # else vertical
        c = cols[0]
        r = min(rows)
        return (r, c), "vertical"

    # ------------------------ Bombing (Hunt/Target + Probability) ------------------------

    def _bomb(self, state):
        N = state["board_size"]
        history = state.get("shot_history", [])

        knowledge, hits, misses = self._build_knowledge(N, history)

        # Infer (conservatively) some sunk ship lengths to improve hunt probabilities.
        remaining_lengths = self._infer_remaining_lengths(N, knowledge)

        # Build hit clusters.
        clusters = self._hit_clusters(N, hits)

        # TARGET MODE: if there are any clusters with adjacent unknown candidates, prioritize them.
        best_target = None
        best_score = -1

        all_hit_set = set(hits)
        for cluster in clusters:
            cluster_set = set(cluster)
            candidates = self._cluster_candidates(N, knowledge, cluster)
            if not candidates:
                continue

            other_hits = all_hit_set - cluster_set
            for cand in candidates:
                score = self._score_candidate_for_cluster(
                    N, knowledge, cand, cluster_set, other_hits, remaining_lengths
                )
                if score > best_score:
                    best_score = score
                    best_target = cand
                elif score == best_score and score > -1 and random.random() < 0.30:
                    best_target = cand

        if best_target is not None:
            return {"target": best_target}

        # HUNT MODE: probability density over all unknown cells, filtered by parity.
        target = self._hunt_target(N, knowledge, remaining_lengths)
        return {"target": target}

    def _build_knowledge(self, N, shot_history):
        # knowledge: 0 unknown, 1 miss, 2 hit
        knowledge = [[0 for _ in range(N)] for _ in range(N)]

        # If a cell was ever a HIT, keep it HIT even if later "MISS" due to re-targeting.
        best = {}
        for entry in shot_history:
            (r, c) = entry["coord"]
            res = entry["result"]
            prev = best.get((r, c))
            if prev == "HIT":
                continue
            if res == "HIT":
                best[(r, c)] = "HIT"
            else:
                best[(r, c)] = "MISS"

        hits = []
        misses = []
        for (r, c), res in best.items():
            if res == "HIT":
                knowledge[r][c] = 2
                hits.append((r, c))
            else:
                knowledge[r][c] = 1
                misses.append((r, c))

        return knowledge, hits, misses

    def _hit_clusters(self, N, hits):
        hit_set = set(hits)
        seen = set()
        clusters = []

        for cell in hits:
            if cell in seen:
                continue
            stack = [cell]
            seen.add(cell)
            cluster = []
            while stack:
                r, c = stack.pop()
                cluster.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < N and 0 <= nc < N and (nr, nc) in hit_set and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            clusters.append(cluster)

        # Prefer larger clusters first (usually more informative).
        clusters.sort(key=len, reverse=True)
        return clusters

    def _cluster_candidates(self, N, knowledge, cluster):
        # Return unknown cells that are most plausible next shots for this hit cluster.
        cluster_set = set(cluster)
        candidates = set()

        if len(cluster) >= 2:
            rows = [r for r, _ in cluster]
            cols = [c for _, c in cluster]
            same_row = all(r == rows[0] for r in rows)
            same_col = all(c == cols[0] for c in cols)

            if same_row:
                r = rows[0]
                minc, maxc = min(cols), max(cols)
                left = (r, minc - 1)
                right = (r, maxc + 1)
                for (rr, cc) in (left, right):
                    if 0 <= rr < N and 0 <= cc < N and knowledge[rr][cc] == 0:
                        candidates.add((rr, cc))
                return candidates

            if same_col:
                c = cols[0]
                minr, maxr = min(rows), max(rows)
                up = (minr - 1, c)
                down = (maxr + 1, c)
                for (rr, cc) in (up, down):
                    if 0 <= rr < N and 0 <= cc < N and knowledge[rr][cc] == 0:
                        candidates.add((rr, cc))
                return candidates
            # Non-linear cluster (ships can touch); fall through to neighbor probing.

        # Single hit or non-linear: probe all orthogonal neighbors.
        for r, c in cluster:
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < N and 0 <= nc < N and knowledge[nr][nc] == 0:
                    candidates.add((nr, nc))
        return candidates

    def _infer_remaining_lengths(self, N, knowledge):
        # Conservative: only mark a cluster as sunk if it is linear and BOTH ends are blocked
        # by boundary or a MISS (not another HIT).
        hits = [(r, c) for r in range(N) for c in range(N) if knowledge[r][c] == 2]
        clusters = self._hit_clusters(N, hits)

        sunk_lengths = []
        for cluster in clusters:
            if len(cluster) < 2:
                continue
            rows = [r for r, _ in cluster]
            cols = [c for _, c in cluster]
            same_row = all(r == rows[0] for r in rows)
            same_col = all(c == cols[0] for c in cols)
            if not (same_row or same_col):
                continue

            if same_row:
                r = rows[0]
                minc, maxc = min(cols), max(cols)
                left = (r, minc - 1)
                right = (r, maxc + 1)
                left_blocked = not (0 <= left[1] < N) or (knowledge[left[0]][left[1]] == 1)
                right_blocked = not (0 <= right[1] < N) or (knowledge[right[0]][right[1]] == 1)
                if left_blocked and right_blocked:
                    sunk_lengths.append(len(cluster))
            else:
                c = cols[0]
                minr, maxr = min(rows), max(rows)
                up = (minr - 1, c)
                down = (maxr + 1, c)
                up_blocked = not (0 <= up[0] < N) or (knowledge[up[0]][up[1]] == 1)
                down_blocked = not (0 <= down[0] < N) or (knowledge[down[0]][down[1]] == 1)
                if up_blocked and down_blocked:
                    sunk_lengths.append(len(cluster))

        remaining = list(self.ships)
        for L in sunk_lengths:
            if L in remaining:
                remaining.remove(L)
        return remaining if remaining else list(self.ships)

    def _score_candidate_for_cluster(self, N, knowledge, cand, cluster_set, other_hits, remaining_lengths):
        # Count how many ship placements could explain the cluster and include cand.
        # Constraints:
        # - must include all hits in this cluster
        # - must include cand
        # - must NOT include any MISS
        # - must NOT include HITs from other clusters (ships don't overlap)
        r0, c0 = cand
        if not (0 <= r0 < N and 0 <= c0 < N) or knowledge[r0][c0] != 0:
            return -1

        miss_set = {(r, c) for r in range(N) for c in range(N) if knowledge[r][c] == 1}
        other_hits_set = set(other_hits)

        cluster_len = len(cluster_set)
        score = 0
        for L in remaining_lengths:
            if L < cluster_len:
                continue
            for placement in self._placements_by_len.get(L, []):
                if cand not in placement:
                    continue
                # quick reject: must cover all cluster hits
                ok = True
                for h in cluster_set:
                    if h not in placement:
                        ok = False
                        break
                if not ok:
                    continue
                # must avoid misses and other hits
                for cell in placement:
                    if cell in miss_set or cell in other_hits_set:
                        ok = False
                        break
                if ok:
                    score += 1
        return score

    def _hunt_target(self, N, knowledge, remaining_lengths):
        targeted = {(r, c) for r in range(N) for c in range(N) if knowledge[r][c] != 0}

        # Parity filter based on smallest remaining ship length (checkerboard for L>=2).
        minL = min(remaining_lengths) if remaining_lengths else 2
        use_parity = (minL >= 2)

        best_cells = []
        best_score = -1

        for r in range(N):
            for c in range(N):
                if knowledge[r][c] != 0:
                    continue
                if use_parity and ((r + c) & 1):
                    continue

                s = 0
                for L in remaining_lengths:
                    for placement in self._placements_by_len.get(L, []):
                        if (r, c) not in placement:
                            continue
                        ok = True
                        for cell in placement:
                            if cell in targeted:
                                ok = False
                                break
                        if ok:
                            s += 1

                # If parity filtered too aggressively late-game, allow any unknown cell.
                if s > best_score:
                    best_score = s
                    best_cells = [(r, c)]
                elif s == best_score:
                    best_cells.append((r, c))

        if best_cells:
            return random.choice(best_cells)

        # Fallback: any unknown cell.
        unknown = [(r, c) for r in range(N) for c in range(N) if knowledge[r][c] == 0]
        return random.choice(unknown) if unknown else (0, 0)

    # ------------------------ Placement Enumeration ------------------------

    def _all_placements(self, L):
        N = self.board_size
        placements = []

        # Horizontal
        for r in range(N):
            for c in range(N - L + 1):
                placements.append([(r, c + k) for k in range(L)])

        # Vertical
        for c in range(N):
            for r in range(N - L + 1):
                placements.append([(r + k, c) for k in range(L)])

        return placements
