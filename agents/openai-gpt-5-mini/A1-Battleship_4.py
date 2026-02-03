"""
Agent Code: A1-Battleship
Model: openai/gpt-5-mini
Run: 4
Generated: 2026-02-03 19:52:39
"""



class BattleshipAgent:
    """
    Smart Battleship agent using a hunt/target strategy with placement-based probability
    and conservative sunk detection (only declares a ship sunk when no larger placement
    could cover the known hit-cluster and a placement of the cluster's length exists).
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        # keep a mutable list of remaining ship lengths
        self.remaining_ships = list(ships_config[:])
        
        # state known about opponent board
        self.possible_moves = {(r, c) for r in range(board_size) for c in range(board_size)}
        self.misses = set()
        self.hits = set()   # hits not yet assigned to a sunk ship
        self.sunk = set()   # coordinates known (by us) to belong to sunk ships
        
        # holds newly discovered sunk coordinates after processing last_shot_result
        self._last_new_sunk = []
        
    # -------------------------
    # Helper utilities
    # -------------------------
    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _neighbors(self, r, c):
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if self._in_bounds(nr, nc):
                yield (nr, nc)

    def _placements_for_length(self, L, required_hits=None):
        """
        Return list of valid placements (each as a list of coords) of length L that:
         - do not include any known misses or already-declared sunk cells
         - do not overlap hits that are not in required_hits (ships cannot overlap)
         - if required_hits provided, the placement must include all required_hits
        """
        required_hits = set(required_hits) if required_hits else set()
        placements = []
        size = self.board_size
        for r in range(size):
            for c in range(size - L + 1):
                coords = [(r, c + i) for i in range(L)]
                coords_set = set(coords)
                # must include required hits
                if not required_hits.issubset(coords_set):
                    continue
                # cannot cover misses or sunk cells
                if any(cell in self.misses or cell in self.sunk for cell in coords):
                    continue
                # cannot overlap other hits that are not part of required_hits
                conflict = False
                for cell in coords:
                    if cell in self.hits and cell not in required_hits:
                        conflict = True
                        break
                if conflict:
                    continue
                placements.append(coords)
        for c in range(size):
            for r in range(size - L + 1):
                coords = [(r + i, c) for i in range(L)]
                coords_set = set(coords)
                if not required_hits.issubset(coords_set):
                    continue
                if any(cell in self.misses or cell in self.sunk for cell in coords):
                    continue
                conflict = False
                for cell in coords:
                    if cell in self.hits and cell not in required_hits:
                        conflict = True
                        break
                if conflict:
                    continue
                placements.append(coords)
        return placements

    def _get_hit_clusters(self):
        """
        Return a list of hit-clusters (each is a set of coords).
        Clusters are connected orthogonally. If a connected component is not linear
        (not all in same row or same col), break it into singleton clusters to avoid
        wrongly assuming multi-cell ship orientation for potentially adjacent distinct ships.
        """
        clusters = []
        visited = set()
        for cell in self.hits:
            if cell in visited:
                continue
            # BFS/DFS to collect component
            comp = set()
            stack = [cell]
            visited.add(cell)
            while stack:
                cur = stack.pop()
                comp.add(cur)
                r, c = cur
                for nb in self._neighbors(r, c):
                    if nb in self.hits and nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            # if comp linear (same row or same col) keep, else split into singletons
            if len(comp) <= 1:
                clusters.append(comp)
            else:
                rows = {r for r, _ in comp}
                cols = {c for _, c in comp}
                if len(rows) == 1 or len(cols) == 1:
                    clusters.append(comp)
                else:
                    # break into singles to treat them independently
                    for single in comp:
                        clusters.append({single})
        return clusters

    def _detect_new_sunk(self):
        """
        Inspect current hit clusters and decide if any can be declared sunk.
        Conservative rule:
         - For a hit-cluster C of size k, if there is NO valid placement of any remaining ship
           with length > k that includes all cells of C, and there exists at least one valid
           placement of a ship of length == k that includes C (and that length is still remaining),
           then C must be a sunk ship of length k.
        """
        new_sunk = []
        # copy to avoid modification during iteration
        clusters = self._get_hit_clusters()
        # evaluate each cluster
        for comp in clusters:
            # skip any already declared sunk coords
            if any(cell in self.sunk for cell in comp):
                continue
            k = len(comp)
            possible_longer = False
            possible_equal = False
            # Check placements for remaining ships
            for L in set(self.remaining_ships):
                placements = self._placements_for_length(L, required_hits=comp)
                if L > k and placements:
                    possible_longer = True
                    break  # if a longer ship can cover this cluster we can't declare it sunk
                if L == k and placements:
                    possible_equal = True
            # If no longer ship can cover and an equal-length placement exists, declare sunk
            if (not possible_longer) and possible_equal and (k in self.remaining_ships):
                # mark as sunk
                for cell in comp:
                    self.sunk.add(cell)
                    if cell in self.hits:
                        self.hits.remove(cell)
                    # ensure cell removed from possible moves (probably already removed when fired)
                    self.possible_moves.discard(cell)
                # remove the ship length from remaining_ships
                try:
                    self.remaining_ships.remove(k)
                except ValueError:
                    pass
                new_sunk.append(comp)
        # flatten coords for return
        flat = [coord for comp in new_sunk for coord in comp]
        return flat

    # -------------------------
    # State update when told previous shot result
    # -------------------------
    def _update_from_last_shot(self, last_shot_result, last_shot_coord):
        """
        Update agent knowledge given the result of the previous shot.
        Detect any newly sunk clusters and store them into self._last_new_sunk.
        """
        self._last_new_sunk = []
        if last_shot_coord is None:
            return
        # ensure we don't shoot same place again
        self.possible_moves.discard(last_shot_coord)
        if last_shot_result == 'HIT':
            self.hits.add(last_shot_coord)
        elif last_shot_result == 'MISS':
            self.misses.add(last_shot_coord)
        # detect sunk ships (if any) after adding the last hit
        newly_sunk = self._detect_new_sunk()
        if newly_sunk:
            self._last_new_sunk = newly_sunk

    # -------------------------
    # Targeting logic for finishing ships once we have a hit
    # -------------------------
    def _score_candidate_extension(self, cluster, candidate):
        """
        Score how many placements (across remaining ships) would be possible if we included 'candidate'
        with the existing cluster. Higher is better.
        """
        total = 0
        combined = set(cluster) | {candidate}
        for L in set(self.remaining_ships):
            placements = self._placements_for_length(L, required_hits=combined)
            total += len(placements)
        return total

    def _choose_from_cluster(self, cluster):
        """
        Given a cluster (set of hits, linear or singleton), choose the best next shot to extend/sink it.
        Returns a coordinate or None.
        """
        cluster = set(cluster)
        if not cluster:
            return None
        # If cluster has length >1, orientation known (row or col)
        if len(cluster) > 1:
            rows = {r for r, _ in cluster}
            cols = {c for _, c in cluster}
            if len(rows) == 1:
                # horizontal
                r = next(iter(rows))
                cols_sorted = sorted(c for _, c in cluster)
                left = (r, cols_sorted[0] - 1)
                right = (r, cols_sorted[-1] + 1)
                candidates = []
                for cell in (left, right):
                    if self._in_bounds(*cell) and cell in self.possible_moves:
                        candidates.append(cell)
                # if ends available choose the one with better placement score
                if candidates:
                    best = max(candidates, key=lambda c: self._score_candidate_extension(cluster, c))
                    return best
            elif len(cols) == 1:
                # vertical
                c = next(iter(cols))
                rows_sorted = sorted(r for r, _ in cluster)
                top = (rows_sorted[0] - 1, c)
                bottom = (rows_sorted[-1] + 1, c)
                candidates = []
                for cell in (top, bottom):
                    if self._in_bounds(*cell) and cell in self.possible_moves:
                        candidates.append(cell)
                if candidates:
                    best = max(candidates, key=lambda c: self._score_candidate_extension(cluster, c))
                    return best
            # If orientation ambiguous or ends blocked, try neighbors of cluster cells
            neighbor_candidates = []
            for (r, c) in cluster:
                for nb in self._neighbors(r, c):
                    if nb in self.possible_moves:
                        neighbor_candidates.append(nb)
            if neighbor_candidates:
                # choose best by placement score
                best = max(set(neighbor_candidates), key=lambda c: self._score_candidate_extension(cluster, c))
                return best
            return None
        else:
            # single hit: try adjacent cells first, choose by best placement score
            cell = next(iter(cluster))
            candidates = [nb for nb in self._neighbors(*cell) if nb in self.possible_moves]
            if candidates:
                best = max(candidates, key=lambda c: self._score_candidate_extension(cluster, c))
                return best
            return None

    # -------------------------
    # Hunting mode (no active hits): compute probability heatmap of where remaining ships could be
    # -------------------------
    def _hunt_move(self):
        """
        Compute a heatmap by counting how many valid placements (across remaining ships)
        cover each unknown cell, and return the cell with max score. If tie or zero,
        fall back to parity/randomized selection.
        """
        if not self.possible_moves:
            return None
        # Initialize counts
        counts = {}
        for move in self.possible_moves:
            counts[move] = 0
        # For each remaining ship length, enumerate placements consistent with known misses/sunk/hits
        for L in set(self.remaining_ships):
            placements = self._placements_for_length(L, required_hits=None)
            for placement in placements:
                for cell in placement:
                    if cell in self.possible_moves:
                        counts[cell] += 1
        # choose best move by count
        max_count = max(counts.values()) if counts else 0
        if max_count > 0:
            best_cells = [cell for cell, val in counts.items() if val == max_count]
            return random.choice(best_cells)
        # Fallback: use parity (checkerboard) to spread shots, preferring center-ish cells
        # Parity choosing based on largest remaining ship length to optimize covering
        largest = max(self.remaining_ships) if self.remaining_ships else 1
        parity = largest % 2
        parity_cells = [cell for cell in self.possible_moves if ((cell[0] + cell[1]) % 2) == parity]
        if parity_cells:
            # choose cell closest to center among parity cells
            center = (self.board_size-1)/2.0
            def dist(c):
                return abs(c[0]-center) + abs(c[1]-center)
            parity_cells.sort(key=dist)
            # pick a random among the best few to add variability
            top_k = parity_cells[:max(1, len(parity_cells)//6)]
            return random.choice(top_k)
        # final fallback: random remaining move
        return random.choice(list(self.possible_moves))

    # -------------------------
    # Main API
    # -------------------------
    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Return ((row, col), sunk_coords)
        Update internal state with last shot information, choose next best move,
        and return any newly-detected sunk coordinates (may be []).
        """
        # Update agent knowledge from previous shot (if any)
        if last_shot_coord is not None:
            # last_shot_result from the game is typically 'HIT' or 'MISS'
            self._update_from_last_shot(last_shot_result, last_shot_coord)

        # Decide move
        move = None
        # If we have active hits, go into target mode
        if self.hits:
            clusters = self._get_hit_clusters()
            # prioritize clusters with larger size (closer to being sunk)
            clusters.sort(key=lambda c: -len(c))
            for cluster in clusters:
                candidate = self._choose_from_cluster(cluster)
                if candidate:
                    move = candidate
                    break

        # If no target move, do hunt mode
        if move is None:
            move = self._hunt_move()

        # If no possible move (shouldn't normally happen), resign by returning None
        if move is None:
            return None

        # mark chosen move as used immediately
        self.possible_moves.discard(move)
        # Prepare sunk_coords to return (these were detected from last_shot_result update)
        sunk_coords = list(self._last_new_sunk) if self._last_new_sunk else []
        # clear the buffer so they are only reported once
        self._last_new_sunk = []
        return move, sunk_coords
