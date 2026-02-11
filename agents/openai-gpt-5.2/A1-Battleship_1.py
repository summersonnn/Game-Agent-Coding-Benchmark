"""
Agent Code: A1-Battleship
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-11 19:37:45
"""

import itertools
from collections import defaultdict

import itertools
from collections import defaultdict

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = list(ships)

        self._rng = random.Random((hash(name) ^ (board_size << 16)) & 0xFFFFFFFF)

        # Bombing knowledge (rebuilt incrementally from shot_history)
        self._processed_history_len = 0
        self._shots = set()
        self._hits = set()
        self._misses = set()

    # ------------------------- Public API -------------------------

    def make_move(self, state, feedback):
        if state["phase"] == "placement":
            return self._place_ship(state)
        return self._bomb(state)

    # ------------------------- Placement -------------------------

    def _place_ship(self, state):
        n = state["board_size"]
        board = state["my_board"]
        L = state["ships_to_place"][0]

        candidates = []
        for orient in ("horizontal", "vertical"):
            for r in range(n):
                for c in range(n):
                    if self._can_place(board, r, c, L, orient):
                        cells = self._cells_of(r, c, L, orient)
                        score = self._placement_score(board, cells)
                        candidates.append((score, r, c, orient))

        # Should always exist; if not, fall back safely (game will random-penalty anyway)
        if not candidates:
            orient = self._rng.choice(["horizontal", "vertical"])
            r = self._rng.randrange(n)
            c = self._rng.randrange(n)
            return {"ship_length": L, "start": (r, c), "orientation": orient}

        # Max-score; random tie-break among top few
        candidates.sort(reverse=True, key=lambda x: x[0])
        top_score = candidates[0][0]
        top = [t for t in candidates if t[0] == top_score]
        _, r, c, orient = self._rng.choice(top)

        return {"ship_length": L, "start": (r, c), "orientation": orient}

    def _can_place(self, board, r, c, L, orient):
        n = self.board_size
        if orient == "horizontal":
            if c + L > n:
                return False
            return all(board[r][cc] == "O" for cc in range(c, c + L))
        else:
            if r + L > n:
                return False
            return all(board[rr][c] == "O" for rr in range(r, r + L))

    def _placement_score(self, board, new_cells):
        """
        Heuristic: prefer edges/corners (lower prior probability),
        and keep ships dispersed from already-placed ships.
        """
        n = self.board_size
        existing = [(r, c) for r in range(n) for c in range(n) if board[r][c] == "S"]

        # Edge preference: closer to any edge => higher score
        edge_score = 0.0
        for r, c in new_cells:
            dist_edge = min(r, c, n - 1 - r, n - 1 - c)
            edge_score += (3.5 - dist_edge)  # larger when near edge

        # Dispersion: maximize distance from existing ships (if any)
        dispersion = 0.0
        if existing:
            # Use min distance from any new cell to any existing cell
            min_d = min(abs(r - er) + abs(c - ec) for (r, c) in new_cells for (er, ec) in existing)
            dispersion = 2.0 * min_d

        # Slight randomness to avoid predictability
        jitter = self._rng.random() * 0.01

        return edge_score + dispersion + jitter

    # ------------------------- Bombing -------------------------

    def _bomb(self, state):
        self._ingest_history(state["shot_history"])

        n = state["board_size"]
        unknown = [(r, c) for r in range(n) for c in range(n) if (r, c) not in self._shots]
        if not unknown:
            return {"target": (0, 0)}  # shouldn't happen before game ends

        # If we have hits on board, prioritize "target mode"
        if self._hits:
            target = self._choose_target_mode_shot()
            if target is not None:
                return {"target": target}

        # Otherwise "hunt mode" via heat map from all ship placements
        target = self._choose_hunt_mode_shot()
        return {"target": target}

    def _ingest_history(self, history):
        # Incremental update from shot_history
        for entry in history[self._processed_history_len:]:
            coord = tuple(entry["coord"])
            res = entry["result"]
            self._shots.add(coord)
            if res == "HIT":
                self._hits.add(coord)
            else:
                self._misses.add(coord)
        self._processed_history_len = len(history)

    # ---- Target mode helpers ----

    def _choose_target_mode_shot(self):
        """
        Try to extend known contiguous hit segments first.
        If only isolated hits exist, probe neighbors with a conditional heat map.
        """
        # 1) Build all horizontal/vertical hit segments (length >= 2)
        segments = self._hit_segments_len_ge_2(self._hits)

        # Prefer longer segments (more informative), with available end-caps to shoot
        seg_choices = []
        for seg in segments:
            ends = self._segment_endcaps(seg)
            ends = [p for p in ends if self._in_bounds(*p) and p not in self._shots]
            if ends:
                seg_choices.append((len(seg["cells"]), seg, ends))

        if seg_choices:
            seg_choices.sort(reverse=True, key=lambda x: x[0])
            _, seg, ends = seg_choices[0]
            heat = self._heat_map_conditioned_on_segment(seg)
            return self._best_by_heat(ends, heat)

        # 2) Isolated hits: pick a hit that still has unknown neighbors
        singletons = [h for h in self._hits if not self._has_adjacent_hit(h)]
        best_single = None
        best_options = None
        # Prefer singleton with more unknown neighbors (more likely to expand)
        for h in singletons:
            neigh = [p for p in self._neighbors4(h) if self._in_bounds(*p) and p not in self._shots]
            if neigh:
                if best_single is None or len(neigh) > len(best_options):
                    best_single, best_options = h, neigh

        if best_single is not None:
            heat = self._heat_map_conditioned_on_hit(best_single)
            return self._best_by_heat(best_options, heat)

        return None

    def _hit_segments_len_ge_2(self, hits):
        n = self.board_size
        hits_by_row = defaultdict(list)
        hits_by_col = defaultdict(list)
        for r, c in hits:
            hits_by_row[r].append(c)
            hits_by_col[c].append(r)

        segments = []

        # Horizontal segments
        for r, cols in hits_by_row.items():
            cols = sorted(cols)
            start = 0
            while start < len(cols):
                end = start
                while end + 1 < len(cols) and cols[end + 1] == cols[end] + 1:
                    end += 1
                if end - start + 1 >= 2:
                    cells = [(r, cc) for cc in cols[start:end + 1]]
                    segments.append({"orientation": "horizontal", "cells": cells})
                start = end + 1

        # Vertical segments
        for c, rows in hits_by_col.items():
            rows = sorted(rows)
            start = 0
            while start < len(rows):
                end = start
                while end + 1 < len(rows) and rows[end + 1] == rows[end] + 1:
                    end += 1
                if end - start + 1 >= 2:
                    cells = [(rr, c) for rr in rows[start:end + 1]]
                    segments.append({"orientation": "vertical", "cells": cells})
                start = end + 1

        # De-duplicate identical segments (unlikely but safe)
        uniq = []
        seen = set()
        for s in segments:
            key = (s["orientation"], tuple(s["cells"]))
            if key not in seen:
                seen.add(key)
                uniq.append(s)
        return uniq

    def _segment_endcaps(self, seg):
        cells = seg["cells"]
        if seg["orientation"] == "horizontal":
            r = cells[0][0]
            minc = min(c for _, c in cells)
            maxc = max(c for _, c in cells)
            return [(r, minc - 1), (r, maxc + 1)]
        else:
            c = cells[0][1]
            minr = min(r for r, _ in cells)
            maxr = max(r for r, _ in cells)
            return [(minr - 1, c), (maxr + 1, c)]

    def _heat_map_conditioned_on_segment(self, seg):
        """
        Count placements (over all ships) that:
        - match segment orientation,
        - include all segment hit cells,
        - do not include any known MISS.
        """
        n = self.board_size
        seg_cells = set(seg["cells"])
        k = len(seg_cells)
        orient = seg["orientation"]

        heat = defaultdict(float)

        for L in self.ships:
            if L < k:
                continue
            if orient == "horizontal":
                r = seg["cells"][0][0]
                minc = min(c for _, c in seg["cells"])
                maxc = max(c for _, c in seg["cells"])
                # start c must satisfy: start <= minc and start+L-1 >= maxc
                for start_c in range(max(0, maxc - L + 1), min(minc, n - L) + 1):
                    cells = [(r, cc) for cc in range(start_c, start_c + L)]
                    if any(p in self._misses for p in cells):
                        continue
                    if not seg_cells.issubset(cells):
                        continue
                    for p in cells:
                        if p not in self._shots:
                            heat[p] += 1.0
            else:
                c = seg["cells"][0][1]
                minr = min(r for r, _ in seg["cells"])
                maxr = max(r for r, _ in seg["cells"])
                for start_r in range(max(0, maxr - L + 1), min(minr, n - L) + 1):
                    cells = [(rr, c) for rr in range(start_r, start_r + L)]
                    if any(p in self._misses for p in cells):
                        continue
                    if not seg_cells.issubset(cells):
                        continue
                    for p in cells:
                        if p not in self._shots:
                            heat[p] += 1.0

        # Encourage shooting the immediate endcaps a bit (when present)
        for p in self._segment_endcaps(seg):
            if self._in_bounds(*p) and p not in self._shots:
                heat[p] += 0.75

        return heat

    def _heat_map_conditioned_on_hit(self, hit):
        """
        Count placements (over all ships, both orientations) that:
        - include this HIT cell,
        - do not include any known MISS.
        """
        n = self.board_size
        hr, hc = hit
        heat = defaultdict(float)

        for L in self.ships:
            # Horizontal placements including (hr,hc)
            for start_c in range(hc - L + 1, hc + 1):
                if 0 <= start_c <= n - L:
                    cells = [(hr, cc) for cc in range(start_c, start_c + L)]
                    if any(p in self._misses for p in cells):
                        continue
                    if hit not in cells:
                        continue
                    for p in cells:
                        if p not in self._shots:
                            heat[p] += 1.0

            # Vertical placements including (hr,hc)
            for start_r in range(hr - L + 1, hr + 1):
                if 0 <= start_r <= n - L:
                    cells = [(rr, hc) for rr in range(start_r, start_r + L)]
                    if any(p in self._misses for p in cells):
                        continue
                    if hit not in cells:
                        continue
                    for p in cells:
                        if p not in self._shots:
                            heat[p] += 1.0

        # Prefer immediate neighbors of the hit
        for p in self._neighbors4(hit):
            if self._in_bounds(*p) and p not in self._shots:
                heat[p] += 0.5

        return heat

    def _best_by_heat(self, candidates, heat):
        # Pick candidate with max heat; tie-break randomly
        scored = [(heat.get(p, 0.0), p) for p in candidates]
        scored.sort(reverse=True, key=lambda x: x[0])
        best_score = scored[0][0]
        best = [p for s, p in scored if s == best_score]
        return self._rng.choice(best)

    def _has_adjacent_hit(self, cell):
        return any(n in self._hits for n in self._neighbors4(cell))

    # ---- Hunt mode helpers ----

    def _choose_hunt_mode_shot(self):
        n = self.board_size
        heat = self._global_heat_map()

        unknown = [(r, c) for r in range(n) for c in range(n) if (r, c) not in self._shots]
        if not unknown:
            return (0, 0)

        # Parity preference early (checkerboard). Fall back if exhausted.
        parity = [p for p in unknown if (p[0] + p[1]) % 2 == 0]
        pool = parity if parity else unknown

        scored = [(heat.get(p, 0.0), p) for p in pool]
        scored.sort(reverse=True, key=lambda x: x[0])
        best_score = scored[0][0]
        best = [p for s, p in scored if s == best_score]
        return self._rng.choice(best)

    def _global_heat_map(self):
        """
        Classic probability density: count all ship placements that don't conflict with known MISS.
        (We don't force covering HITs here; target-mode handles those.)
        """
        n = self.board_size
        heat = defaultdict(float)

        for L in self.ships:
            # Horizontal
            for r in range(n):
                for c in range(n - L + 1):
                    cells = [(r, cc) for cc in range(c, c + L)]
                    if any(p in self._misses for p in cells):
                        continue
                    for p in cells:
                        if p not in self._shots:
                            heat[p] += 1.0

            # Vertical
            for c in range(n):
                for r in range(n - L + 1):
                    cells = [(rr, c) for rr in range(r, r + L)]
                    if any(p in self._misses for p in cells):
                        continue
                    for p in cells:
                        if p not in self._shots:
                            heat[p] += 1.0

        return heat

    # ------------------------- Utilities -------------------------

    def _cells_of(self, r, c, L, orient):
        if orient == "horizontal":
            return [(r, cc) for cc in range(c, c + L)]
        return [(rr, c) for rr in range(r, r + L)]

    def _neighbors4(self, cell):
        r, c = cell
        return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]

    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size
