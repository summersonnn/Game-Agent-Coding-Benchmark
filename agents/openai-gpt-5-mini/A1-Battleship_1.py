"""
Agent Code: A1-Battleship
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-03 19:52:39
"""



class BattleshipAgent:
    """
    Smart Battleship agent using a hunt/target strategy with exact placement enumeration.
    - Maintains sets of moves, misses, hits, sunk cells and remaining ship sizes.
    - In 'target' mode (when there are unresolved hits) it focuses on finishing that ship using
      orientation heuristics and counting consistent placements.
    - In 'hunt' mode it builds a heatmap by enumerating all possible placements of remaining ships
      consistent with known misses/sunk/hits and chooses the cell covered by the most placements.
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = list(ships_config)
        # mutable state
        self.remaining_ships = list(self.ships_config)  # lengths remaining to sink
        self.moves_available = {(r, c) for r in range(board_size) for c in range(board_size)}
        self.miss_cells = set()   # coordinates known to be misses
        self.hit_cells = set()    # coordinates known to be hits (not yet confirmed sunk)
        self.sunk_cells = set()   # coordinates we've marked as part of sunk ships
        self.pending_hits = set() # same as hit_cells (alias for clarity)
        # bookkeeping
        self._last_played = None

    # helper utilities
    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _neighbors(self, r, c):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if self._in_bounds(nr, nc):
                yield (nr, nc)

    def _placements_for_size(self, L, require_include_set=None):
        """
        Return a list of placements (each a tuple of coords) of length L that:
        - do not include any known MISS or known SUNK coordinates
        - do not overlap any known HIT that's NOT part of require_include_set (ships do not overlap)
        - if require_include_set is provided, the placement must include all coords from that set
        """
        placements = []
        req = set(require_include_set) if require_include_set else None

        # horizontal placements
        for r in range(self.board_size):
            for c in range(self.board_size - L + 1):
                coords = tuple((r, c + i) for i in range(L))
                if req and not req.issubset(coords):
                    continue
                invalid = False
                for cell in coords:
                    if cell in self.miss_cells or cell in self.sunk_cells:
                        invalid = True; break
                    # cannot cover hits that belong to other components
                    if cell in self.hit_cells and (not req or cell not in req):
                        invalid = True; break
                if not invalid:
                    placements.append(coords)

        # vertical placements
        for c in range(self.board_size):
            for r in range(self.board_size - L + 1):
                coords = tuple((r + i, c) for i in range(L))
                if req and not req.issubset(coords):
                    continue
                invalid = False
                for cell in coords:
                    if cell in self.miss_cells or cell in self.sunk_cells:
                        invalid = True; break
                    if cell in self.hit_cells and (not req or cell not in req):
                        invalid = True; break
                if not invalid:
                    placements.append(coords)

        return placements

    def _hit_components(self):
        """Return list of connected components (sets) of current hit_cells (excluding sunk_cells)."""
        comps = []
        unvisited = set(self.hit_cells)
        while unvisited:
            start = next(iter(unvisited))
            stack = [start]
            comp = set()
            while stack:
                cell = stack.pop()
                if cell in comp:
                    continue
                comp.add(cell)
                r, c = cell
                for nb in self._neighbors(r, c):
                    if nb in unvisited and nb not in comp:
                        stack.append(nb)
            comps.append(comp)
            unvisited -= comp
        return comps

    def _detect_and_mark_sunk(self):
        """
        Examine each connected component of hits and determine if it must be sunk.
        Returns a list of coordinates for all components we now mark as sunk.
        """
        sunk_coords = []
        comps = self._hit_components()
        # operate on a copy since we'll be modifying remaining_ships
        for comp in comps:
            comp_set = set(comp)
            confirmed_length = None
            # check each candidate remaining ship size
            for L in sorted(set(self.remaining_ships)):
                placements = self._placements_for_size(L, require_include_set=comp_set)
                if not placements:
                    continue
                # check whether every placement that includes comp has all its cells within comp
                all_fully_covered = True
                for p in placements:
                    # if any cell in the placement is not in comp, then ship of length L could still extend
                    if any(cell not in comp_set for cell in p):
                        all_fully_covered = False
                        break
                if all_fully_covered:
                    confirmed_length = L
                    break
            if confirmed_length is not None:
                # mark as sunk: remove one ship of that length and move hit cells to sunk_cells
                try:
                    self.remaining_ships.remove(confirmed_length)
                except ValueError:
                    # already removed; ignore
                    pass
                for cell in comp_set:
                    if cell in self.hit_cells:
                        self.hit_cells.remove(cell)
                    if cell in self.pending_hits:
                        self.pending_hits.remove(cell)
                    self.sunk_cells.add(cell)
                sunk_coords.extend(list(comp_set))
        return sunk_coords

    def _score_candidate_for_component(self, candidate, comp):
        """
        Score a candidate neighbor cell for a given hit component by counting how many
        legal placements (across all remaining ship sizes) include both comp and candidate.
        """
        score = 0
        comp_set = set(comp)
        for L in set(self.remaining_ships):
            placements = self._placements_for_size(L, require_include_set=comp_set)
            for p in placements:
                if candidate in p:
                    score += 1
        return score

    def _choose_target_move(self):
        """
        Choose a move aimed at finishing a current hit component (target mode).
        Returns a move (r,c) or None if no suitable target candidates found.
        """
        if not self.hit_cells:
            return None
        comps = self._hit_components()
        # choose the component to focus: prefer the one with latest hit if possible (heuristic: largest size)
        # We'll pick the largest component (most constrained)
        comps.sort(key=lambda s: (-len(s), min(s)))  # largest first; tie-break deterministically
        comp = comps[0]
        # deduce orientation if possible
        rows = {r for r, _ in comp}
        cols = {c for _, c in comp}
        candidates = []

        if len(comp) >= 2:
            if len(rows) == 1:
                # horizontal
                r = next(iter(rows))
                minc = min(c for _, c in comp)
                maxc = max(c for _, c in comp)
                left = (r, minc - 1)
                right = (r, maxc + 1)
                for nb in (left, right):
                    if nb in self.moves_available:
                        candidates.append(nb)
            elif len(cols) == 1:
                # vertical
                c = next(iter(cols))
                minr = min(r for r, _ in comp)
                maxr = max(r for r, _ in comp)
                up = (minr - 1, c)
                down = (maxr + 1, c)
                for nb in (up, down):
                    if nb in self.moves_available:
                        candidates.append(nb)
            else:
                # non-straight cluster (rare). Try any neighbor of cluster cells.
                for cell in comp:
                    r, c = cell
                    for nb in self._neighbors(r, c):
                        if nb in self.moves_available:
                            candidates.append(nb)
        else:
            # single hit: try all 4 neighbors
            (r0, c0) = next(iter(comp))
            for nb in self._neighbors(r0, c0):
                if nb in self.moves_available:
                    candidates.append(nb)

        # deduplicate candidates
        candidates = list(dict.fromkeys(candidates))
        if not candidates:
            return None

        # score candidates by number of consistent placements that include both comp and candidate
        scored = []
        for cand in candidates:
            sc = self._score_candidate_for_component(cand, comp)
            scored.append((sc, cand))
        # choose highest score (break ties randomly)
        max_score = max(scored, key=lambda x: x[0])[0]
        best = [cand for sc, cand in scored if sc == max_score]
        return random.choice(best)

    def _choose_hunt_move(self):
        """
        Hunt mode: build heatmap of all placements of remaining ships and choose cell with max coverage.
        """
        heat = {}
        for L in self.remaining_ships:
            placements = self._placements_for_size(L, require_include_set=None)
            for p in placements:
                for cell in p:
                    if cell in self.moves_available:
                        heat[cell] = heat.get(cell, 0) + 1
        if heat:
            maxval = max(heat.values())
            best = [cell for cell, v in heat.items() if v == maxval]
            return random.choice(best)
        # fallback: if heat empty, just pick a random available move
        if self.moves_available:
            return random.choice(list(self.moves_available))
        return None

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Receive information about the previous shot you made (if any) via last_shot_result and last_shot_coord,
        update internal state, detect any sunk ships (based on deductions), and pick the next coordinate to bomb.
        Returns: ((row, col), sunk_coords)
        - sunk_coords: list of coords (r,c) that agent now deduces are sunk (these correspond to prior hits).
        """
        # Update internal state with the result of our previous shot (if any)
        if last_shot_coord is not None:
            # ensure it's not in available moves (we remove when we fire)
            self.moves_available.discard(last_shot_coord)
            if last_shot_result == 'HIT':
                # record hit
                self.hit_cells.add(last_shot_coord)
                self.pending_hits.add(last_shot_coord)
            else:
                # record miss
                self.miss_cells.add(last_shot_coord)

        # Based on accumulated hits/misses, detect if any ship(s) can be confirmed sunk now
        sunk_coords = self._detect_and_mark_sunk()

        # Choose next move: target mode if we have unresolved hits, else hunt mode
        move = None
        # Prefer target move (finish off a detected hit cluster)
        if self.pending_hits:
            move = self._choose_target_move()
        # If target mode couldn't produce a candidate, do hunt
        if move is None:
            move = self._choose_hunt_move()

        # If no move available, resign (shouldn't normally happen)
        if move is None:
            return None

        # Remove selected move from available moves immediately
        self.moves_available.discard(move)
        self._last_played = move
        return move, sunk_coords
