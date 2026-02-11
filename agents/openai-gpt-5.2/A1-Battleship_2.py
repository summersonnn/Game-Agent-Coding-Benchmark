"""
Agent Code: A1-Battleship
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-11 19:37:45
"""

import itertools

import itertools

class BattleshipAgent:
    """
    Battleship agent with:
      - Placement: non-overlapping + 1-cell buffer (incl. diagonals) when possible; edge-biased, randomized among top picks.
      - Bombing: hunt/target strategy
          * Target: extend known hit-lines; otherwise probe adjacent to single hits.
          * Hunt: probability heatmap from remaining ship lengths (inferred when a hit-line is capped by MISS/boundary),
                  with light parity bias.
    """

    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = list(ships)

        # Bombing state (reset per game)
        self._new_bombing_game()

        # Placement preference
        self._last_place_orientation = None

    # -------------------------- Public API --------------------------

    def make_move(self, state, feedback):
        phase = state.get("phase")
        if phase == "placement":
            # Reset bombing state at the start of a new game (placement comes before bombing)
            if state.get("ships_placed", 0) == 0:
                self._new_bombing_game()
            return self._place_ship(state)
        else:
            return self._bomb(state)

    # -------------------------- Placement --------------------------

    def _place_ship(self, state):
        N = state["board_size"]
        board = state["my_board"]
        L = state["ships_to_place"][0]

        # Try with buffer first; if impossible, relax.
        placements = self._enumerate_valid_placements(board, L, use_buffer=True)
        if not placements:
            placements = self._enumerate_valid_placements(board, L, use_buffer=False)

        # Should never be empty; but just in case, fall back to a simple safe scan.
        if not placements:
            for r in range(N):
                for c in range(N):
                    if self._is_valid_placement(board, (r, c), "horizontal", L, use_buffer=False):
                        return {"ship_length": L, "start": (r, c), "orientation": "horizontal"}
                    if self._is_valid_placement(board, (r, c), "vertical", L, use_buffer=False):
                        return {"ship_length": L, "start": (r, c), "orientation": "vertical"}
            # Absolute last resort
            return {"ship_length": L, "start": (0, 0), "orientation": "horizontal"}

        # Score placements: prefer edges/corners + dispersion (via buffer) + mild randomness,
        # and avoid always using same orientation.
        center = (N - 1) / 2.0

        def cell_score(r, c):
            edge = (r == 0 or r == N - 1 or c == 0 or c == N - 1)
            corner = (r in (0, N - 1) and c in (0, N - 1))
            dist = abs(r - center) + abs(c - center)
            # Edge/corner bias and a slight preference away from center.
            return (2.5 if edge else 0.0) + (2.0 if corner else 0.0) + (0.35 * dist)

        scored = []
        for start, orient, cells in placements:
            s = sum(cell_score(r, c) for r, c in cells)

            # Slightly prefer alternating orientation to avoid patterns.
            if self._last_place_orientation is not None and orient != self._last_place_orientation:
                s += 0.6

            # Random jitter to avoid predictability.
            s += (0.25 * (random.random() - 0.5))
            scored.append((s, start, orient))

        scored.sort(reverse=True, key=lambda x: x[0])

        # Choose among top few to stay unpredictable.
        top_k = min(6, len(scored))
        _, start, orient = random.choice(scored[:top_k])

        self._last_place_orientation = orient
        return {"ship_length": L, "start": start, "orientation": orient}

    def _enumerate_valid_placements(self, board, L, use_buffer=True):
        N = self.board_size
        out = []
        for orient in ("horizontal", "vertical"):
            if orient == "horizontal":
                for r in range(N):
                    for c in range(N - L + 1):
                        if self._is_valid_placement(board, (r, c), orient, L, use_buffer=use_buffer):
                            cells = [(r, c + i) for i in range(L)]
                            out.append(((r, c), orient, cells))
            else:
                for r in range(N - L + 1):
                    for c in range(N):
                        if self._is_valid_placement(board, (r, c), orient, L, use_buffer=use_buffer):
                            cells = [(r + i, c) for i in range(L)]
                            out.append(((r, c), orient, cells))
        return out

    def _is_valid_placement(self, board, start, orientation, L, use_buffer=True):
        N = self.board_size
        r0, c0 = start

        # Bounds
        if orientation == "horizontal":
            if c0 < 0 or c0 + L > N or r0 < 0 or r0 >= N:
                return False
            cells = [(r0, c0 + i) for i in range(L)]
        else:
            if r0 < 0 or r0 + L > N or c0 < 0 or c0 >= N:
                return False
            cells = [(r0 + i, c0) for i in range(L)]

        # Overlap
        for r, c in cells:
            if board[r][c] != "O":
                return False

        if not use_buffer:
            return True

        # Buffer: no adjacent (including diagonal) to existing ships.
        for r, c in cells:
            for rr in range(r - 1, r + 2):
                for cc in range(c - 1, c + 2):
                    if 0 <= rr < N and 0 <= cc < N:
                        if board[rr][cc] == "S":
                            return False
        return True

    # -------------------------- Bombing --------------------------

    def _new_bombing_game(self):
        self._seen_shots = 0
        self._shot_result = {}          # (r,c) -> "HIT"/"MISS"
        self._hits = set()
        self._misses = set()
        self._resolved_hits = set()     # hits we believe are on sunk ships
        self._remaining_lengths = list(self.ships)
        self._hunt_parity = random.randint(0, 1)

    def _bomb(self, state):
        # Detect new game / reset situations
        hist = state.get("shot_history", [])
        if len(hist) < self._seen_shots:
            self._new_bombing_game()
        if len(hist) == 0 and self._seen_shots > 0:
            self._new_bombing_game()

        self._sync_from_history(hist)
        self._infer_sunk_ships()

        N = state["board_size"]
        untried = [(r, c) for r in range(N) for c in range(N) if (r, c) not in self._shot_result]

        # If no moves left (shouldn't happen), pick something.
        if not untried:
            return {"target": (0, 0)}

        unresolved_hits = self._hits - self._resolved_hits
        frontier_hits = [h for h in unresolved_hits if any(nb in set(untried) for nb in self._neighbors4(*h))]

        # Heatmap for tie-breaking / hunting
        if frontier_hits:
            blocked = set(self._misses)  # allow overlaps with hits (target mode handles the hits)
        else:
            blocked = set(self._misses) | set(self._hits)  # don't count placements through already-hit cells
        heat = self._compute_heatmap(blocked, self._remaining_lengths)

        # TARGET MODE: generate candidates around unresolved hits
        candidates = {}  # coord -> score
        max_ship_len = max(self.ships) if self.ships else 5

        if frontier_hits:
            untried_set = set(untried)

            for (r, c) in frontier_hits:
                # Determine contiguous horizontal segment in unresolved hits
                left = c
                while (r, left - 1) in unresolved_hits:
                    left -= 1
                right = c
                while (r, right + 1) in unresolved_hits:
                    right += 1
                hlen = right - left + 1

                # Determine contiguous vertical segment in unresolved hits
                up = r
                while (up - 1, c) in unresolved_hits:
                    up -= 1
                down = r
                while (down + 1, c) in unresolved_hits:
                    down += 1
                vlen = down - up + 1

                did_line = False

                # Extend strong lines first
                if hlen >= 2 and hlen < max_ship_len:
                    did_line = True
                    for cc, side_bonus in ((left - 1, 0.2), (right + 1, 0.0)):
                        coord = (r, cc)
                        if coord in untried_set and self._in_bounds(*coord):
                            base = 2500 + 150 * hlen
                            candidates[coord] = max(candidates.get(coord, -10**9),
                                                    base + 8 * heat.get(coord, 0) + side_bonus)

                if vlen >= 2 and vlen < max_ship_len:
                    did_line = True
                    for rr, side_bonus in ((up - 1, 0.2), (down + 1, 0.0)):
                        coord = (rr, c)
                        if coord in untried_set and self._in_bounds(*coord):
                            base = 2500 + 150 * vlen
                            candidates[coord] = max(candidates.get(coord, -10**9),
                                                    base + 8 * heat.get(coord, 0) + side_bonus)

                # If no clear line, try adjacent cells
                if not did_line:
                    for nb in self._neighbors4(r, c):
                        if nb in untried_set:
                            base = 1700
                            candidates[nb] = max(candidates.get(nb, -10**9),
                                                 base + 10 * heat.get(nb, 0))

        if candidates:
            best_score = max(candidates.values())
            best = [coord for coord, sc in candidates.items() if sc == best_score]
            return {"target": random.choice(best)}

        # HUNT MODE: pick highest heat, with parity + mild centrality bias
        center = (N - 1) / 2.0
        best_val = -10**18
        best_cells = []

        for (r, c) in untried:
            h = heat.get((r, c), 0)

            # Parity bias (helps reduce search space, but doesn't forbid off-parity picks)
            parity_bonus = 3 if ((r + c) & 1) == self._hunt_parity else 0

            # Prefer more central (more placements typically)
            dist = abs(r - center) + abs(c - center)
            central_bonus = (N - dist) * 0.15

            val = (h * 10) + parity_bonus + central_bonus

            if val > best_val:
                best_val = val
                best_cells = [(r, c)]
            elif val == best_val:
                best_cells.append((r, c))

        return {"target": random.choice(best_cells) if best_cells else random.choice(untried)}

    def _sync_from_history(self, shot_history):
        # Update internal structures from newly appended history
        for entry in shot_history[self._seen_shots:]:
            coord = tuple(entry["coord"])
            res = entry["result"]
            self._shot_result[coord] = res
            if res == "HIT":
                self._hits.add(coord)
                self._misses.discard(coord)
            else:
                self._misses.add(coord)
                self._hits.discard(coord)
                self._resolved_hits.discard(coord)
        self._seen_shots = len(shot_history)

    def _infer_sunk_ships(self):
        """
        Infer sunk ships only when we have a straight-line connected hit component whose
        both ends are blocked by boundary or MISS. Then:
          - mark those hits as resolved
          - remove that length from remaining lengths (if available)
        """
        unresolved = self._hits - self._resolved_hits
        if not unresolved:
            self._remaining_lengths = list(self.ships)  # safe default, but keep inference:
            # Actually keep previous inference; do nothing.
            return

        remaining = list(self.ships)
        # Remove already-resolved lengths? We don't store lengths per component, so recompute:
        # Start from full and re-infer by scanning ALL hits with current misses info.
        # This is safe and prevents drift across turns.
        self._resolved_hits = set()

        hits_all = set(self._hits)
        visited = set()

        for start in hits_all:
            if start in visited:
                continue
            # BFS component (orthogonal adjacency)
            comp = []
            dq = deque([start])
            visited.add(start)
            while dq:
                r, c = dq.popleft()
                comp.append((r, c))
                for nb in self._neighbors4(r, c):
                    if nb in hits_all and nb not in visited:
                        visited.add(nb)
                        dq.append(nb)

            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}

            # Only infer sink for straight-line components
            if len(rows) == 1:
                r = next(iter(rows))
                minc = min(c for _, c in comp)
                maxc = max(c for _, c in comp)
                length = len(comp)

                # Ensure contiguous (should be, but verify)
                if length != (maxc - minc + 1):
                    continue

                left_blocked = (minc == 0) or ((r, minc - 1) in self._misses)
                right_blocked = (maxc == self.board_size - 1) or ((r, maxc + 1) in self._misses)

                if left_blocked and right_blocked and (length in remaining):
                    remaining.remove(length)
                    self._resolved_hits.update(comp)

            elif len(cols) == 1:
                c = next(iter(cols))
                minr = min(r for r, _ in comp)
                maxr = max(r for r, _ in comp)
                length = len(comp)

                if length != (maxr - minr + 1):
                    continue

                up_blocked = (minr == 0) or ((minr - 1, c) in self._misses)
                down_blocked = (maxr == self.board_size - 1) or ((maxr + 1, c) in self._misses)

                if up_blocked and down_blocked and (length in remaining):
                    remaining.remove(length)
                    self._resolved_hits.update(comp)

        self._remaining_lengths = remaining

    def _compute_heatmap(self, blocked, ship_lengths):
        """
        Count number of valid placements of each remaining ship length that would cover each cell,
        given a set of blocked cells (typically misses, and sometimes already-hit cells).
        """
        N = self.board_size
        heat = {(r, c): 0 for r in range(N) for c in range(N)}

        if not ship_lengths:
            return heat

        blocked = set(blocked)

        for L in ship_lengths:
            # Horizontal placements
            for r in range(N):
                for c0 in range(N - L + 1):
                    cells = [(r, c0 + i) for i in range(L)]
                    if any(cell in blocked for cell in cells):
                        continue
                    for cell in cells:
                        heat[cell] += 1

            # Vertical placements
            for r0 in range(N - L + 1):
                for c in range(N):
                    cells = [(r0 + i, c) for i in range(L)]
                    if any(cell in blocked for cell in cells):
                        continue
                    for cell in cells:
                        heat[cell] += 1

        return heat

    # -------------------------- Helpers --------------------------

    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _neighbors4(self, r, c):
        if r > 0:
            yield (r - 1, c)
        if r < self.board_size - 1:
            yield (r + 1, c)
        if c > 0:
            yield (r, c - 1)
        if c < self.board_size - 1:
            yield (r, c + 1)
