"""
Agent Code: A1-Battleship
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-03 19:52:39
"""

import itertools

class BattleshipAgent:
    """
    Smart Battleship agent using a hunt/target strategy with a probability heatmap.
    Keeps track of its own knowledge (hits, misses, sunk), maintains the set of
    available moves, and tries to deduce sunk ships to update remaining ship list.
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = list(ships_config)
        # remaining ships (lengths) that we haven't accounted for being sunk
        self.remaining_ships = list(self.ships_config[:])
        # Knowledge grid: 0 = unknown, -1 = miss, 1 = hit, 2 = sunk
        self.knowledge = [[0 for _ in range(board_size)] for _ in range(board_size)]
        # set of coordinates still available to fire upon
        self.available_moves = {(r, c) for r in range(board_size) for c in range(board_size)}
        # sets to track hits and sunk cells
        self.hits = set()
        self.sunk_cells = set()
        # randomize choices
        random.seed()

    # Utility helpers
    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _neighbors(self, r, c):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if self._in_bounds(nr, nc):
                yield (nr, nc)

    def _process_last_shot(self, last_shot_result, last_shot_coord):
        """Update internal knowledge based on result of the previous shot."""
        if last_shot_coord is None:
            return
        r, c = last_shot_coord
        # Always ensure the move is removed from available moves
        self.available_moves.discard((r, c))
        if last_shot_result == 'HIT':
            self.knowledge[r][c] = 1
            self.hits.add((r, c))
        elif last_shot_result == 'MISS':
            self.knowledge[r][c] = -1
        else:
            # Unknown values are ignored
            pass

    def _get_hit_components(self):
        """Return a list of connected components (lists) of hit coordinates."""
        comps = []
        seen = set()
        for cell in self.hits:
            if cell in seen:
                continue
            stack = [cell]
            comp = []
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                comp.append(cur)
                for nb in self._neighbors(*cur):
                    if nb in self.hits and nb not in seen:
                        stack.append(nb)
            comps.append(comp)
        return comps

    def _valid_placements_for_ship(self, size, required_cells=None):
        """
        Generate all valid ship placements (list of coordinate lists) for a ship of given size,
        consistent with current knowledge. If required_cells is provided (iterable), only placements
        that include all those cells are returned.
        """
        required = set(required_cells) if required_cells else None
        placements = []
        n = self.board_size
        # horizontal
        for r in range(n):
            for c in range(n - size + 1):
                placement = [(r, c + i) for i in range(size)]
                ok = True
                for (pr, pc) in placement:
                    if self.knowledge[pr][pc] == -1:  # can't overlap a known miss
                        ok = False
                        break
                    if (pr, pc) in self.sunk_cells:   # can't overlap already-sunk cells
                        ok = False
                        break
                if not ok:
                    continue
                if required and not required.issubset(placement):
                    continue
                placements.append(placement)
        # vertical
        for c in range(n):
            for r in range(n - size + 1):
                placement = [(r + i, c) for i in range(size)]
                ok = True
                for (pr, pc) in placement:
                    if self.knowledge[pr][pc] == -1:
                        ok = False
                        break
                    if (pr, pc) in self.sunk_cells:
                        ok = False
                        break
                if not ok:
                    continue
                if required and not required.issubset(placement):
                    continue
                placements.append(placement)
        return placements

    def _detect_and_mark_sunk(self):
        """
        Detect any hit components that can be confidently declared sunk.
        Returns list of lists of coordinates that we believe are sunk ships.
        """
        sunk_lists = []
        comps = self._get_hit_components()
        # Work on a copy of remaining_ships to test placements
        for comp in comps:
            comp_set = set(comp)
            comp_len = len(comp)
            # If this component has already been marked sunk, skip
            if comp_set & self.sunk_cells:
                continue
            # Find ship sizes that can cover this component with valid placements
            possible_sizes = []
            placements_by_size = {}
            for s in sorted(self.remaining_ships):
                placements = self._valid_placements_for_ship(s, required_cells=comp)
                if placements:
                    possible_sizes.append(s)
                    placements_by_size[s] = placements
            if not possible_sizes:
                # Strange situation: no ship placement can explain these hits.
                # Skip declaring sunk; keep hunting/targeting to resolve contradictions.
                continue
            # If the only possible sizes that cover this component are exactly its length,
            # i.e., no larger ship can cover it, then we can safely declare it sunk.
            larger_possible = [s for s in possible_sizes if s > comp_len]
            if (comp_len in possible_sizes) and (not larger_possible):
                # We can mark this comp as sunk
                for cell in comp:
                    r, c = cell
                    self.knowledge[r][c] = 2
                    self.sunk_cells.add(cell)
                    if cell in self.hits:
                        self.hits.discard(cell)
                # remove one ship of this length from remaining ships
                try:
                    self.remaining_ships.remove(comp_len)
                except ValueError:
                    # might have been removed already; ignore
                    pass
                sunk_lists.append(comp)
        return sunk_lists

    def _build_heatmap(self, target_components=None):
        """
        Build a heatmap (cell -> score) for the next shot.
        If target_components is provided (list of hit-component lists), prefer placements that
        include those components. The returned dictionary maps (r, c) -> score.
        """
        heat = {}
        if target_components:
            # For each component, consider placements of remaining ships that cover that component
            for comp in target_components:
                comp_set = set(comp)
                for s in self.remaining_ships:
                    placements = self._valid_placements_for_ship(s, required_cells=comp)
                    for placement in placements:
                        for cell in placement:
                            if cell in self.available_moves:
                                # weight by component size to prioritize larger/well-established hits
                                heat[cell] = heat.get(cell, 0) + max(1, len(comp))
            # If we found any heat for targets, return it
            if heat:
                return heat
            # else fall back to general heatmap below

        # General heatmap across all ships and placements (used for hunting)
        for s in self.remaining_ships:
            placements = self._valid_placements_for_ship(s)
            for placement in placements:
                for cell in placement:
                    if cell in self.available_moves:
                        heat[cell] = heat.get(cell, 0) + 1
        return heat

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Return a tuple: ((row, col), sunk_coords)
        - (row, col): The cell to bomb (0-indexed)
        - sunk_coords: List of coordinates if you've sunk a ship, else []
        """
        # Update internal state with last shot result
        if last_shot_coord is not None:
            self._process_last_shot(last_shot_result, last_shot_coord)

        # Try to detect any newly sunk ships from our hits
        sunk_lists = self._detect_and_mark_sunk()
        # Flatten sunk lists for return
        sunk_coords = list(itertools.chain.from_iterable(sunk_lists)) if sunk_lists else []

        # Decide next move
        # If we have unresolved hits, treat them as targets
        target_comps = self._get_hit_components()
        heatmap = self._build_heatmap(target_components=target_comps if target_comps else None)

        chosen = None
        if heatmap:
            # pick cell(s) with maximum score
            max_score = max(heatmap.values())
            candidates = [cell for cell, score in heatmap.items() if score == max_score]
            # tie-breaker: prefer cells adjacent to existing hits (for better targeting)
            adj_candidates = []
            for cand in candidates:
                r, c = cand
                if any(nb in self.hits for nb in self._neighbors(r, c)):
                    adj_candidates.append(cand)
            if adj_candidates:
                chosen = random.choice(adj_candidates)
            else:
                chosen = random.choice(candidates)
        else:
            # No heatmap possible (rare) - choose a random available move (try to be parity-aware)
            if not self.available_moves:
                return None  # no moves left
            # parity heuristic: use a checkerboard pattern keyed to smallest remaining ship length
            min_ship = min(self.remaining_ships) if self.remaining_ships else 1
            if min_ship >= 2:
                parity_candidates = [m for m in self.available_moves if (m[0] + m[1]) % 2 == (min_ship % 2)]
                if parity_candidates:
                    chosen = random.choice(parity_candidates)
                else:
                    chosen = random.choice(list(self.available_moves))
            else:
                chosen = random.choice(list(self.available_moves))

        # Ensure chosen is removed from available moves immediately
        self.available_moves.discard(chosen)

        return chosen, sunk_coords
