"""
Agent Code: A1-Battleship
Model: openai/gpt-5-mini
Run: 3
Generated: 2026-02-03 19:52:39
"""



class BattleshipAgent:
    """
    Smart Battleship agent using a hunt/target strategy with placement-based probability heatmaps.
    - Keeps track of shots, hits, misses and sunk ships.
    - When no unresolved hits: hunts by scoring every cell by counting all valid ship placements (probability density).
    - When there are unresolved hits: targets by restricting placements to those covering the hit-cluster(s).
    - Attempts to deduce sinks by checking whether any placement of a larger ship can still cover the cluster.
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = list(ships_config)
        # remaining ship lengths (we remove lengths as they are deduced sunk)
        self.remaining_ships = list(self.ships_config)
        # all moves available at start
        self.available_moves = {(r, c) for r in range(board_size) for c in range(board_size)}
        # fired shots (both hits and misses)
        self.fired = set()
        self.hits = set()   # coordinates that were hits but not yet marked sunk
        self.misses = set()
        self.sunk = set()   # coordinates belonging to deduced sunk ships
        # convenience
        self.min_ship = min(self.ships_config) if self.ships_config else 1

    # ----------------- Helper utilities -----------------
    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _get_hit_clusters(self):
        """Return list of sets, each set is a cluster (connected orthogonally) of hit coords."""
        clusters = []
        seen = set()
        for cell in self.hits:
            if cell in seen:
                continue
            stack = [cell]
            cluster = set()
            seen.add(cell)
            while stack:
                x, y = stack.pop()
                cluster.add((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in self.hits and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            clusters.append(cluster)
        return clusters

    def _placements_for_length(self, L, cluster=None):
        """
        Enumerate all valid placements (list of coord lists) for ship length L.
        If cluster is provided (set of coords), only placements that include the entire cluster are allowed.
        A placement is valid if:
         - all placement cells are on-board
         - no cell is in misses or sunk
         - if cluster given: placement must include cluster and must not include hits outside cluster
         - if cluster not given: placement must not include any existing hits (we use this only when no hits exist)
        """
        placements = []
        hits_outside = set(self.hits) - (set(cluster) if cluster is not None else set())
        for r in range(self.board_size):
            for c in range(self.board_size - L + 1):
                cells = [(r, c + i) for i in range(L)]
                # cannot overlap misses or sunk cells
                if any(cell in self.misses or cell in self.sunk for cell in cells):
                    continue
                if cluster is not None:
                    # must include whole cluster
                    if not set(cluster).issubset(cells):
                        continue
                    # cannot include hits that belong to other clusters
                    if any(cell in hits_outside for cell in cells):
                        continue
                else:
                    # when no cluster, avoid placements that include existing hits (shouldn't be used when hits exist)
                    if any(cell in self.hits for cell in cells):
                        continue
                placements.append(cells)
        # vertical
        for c in range(self.board_size):
            for r in range(self.board_size - L + 1):
                cells = [(r + i, c) for i in range(L)]
                if any(cell in self.misses or cell in self.sunk for cell in cells):
                    continue
                if cluster is not None:
                    if not set(cluster).issubset(cells):
                        continue
                    if any(cell in hits_outside for cell in cells):
                        continue
                else:
                    if any(cell in self.hits for cell in cells):
                        continue
                placements.append(cells)
        return placements

    def _compute_heatmap(self, cluster=None):
        """
        Compute a heatmap (dict cell -> score) by counting how many valid placements
        (for all remaining ships) include each not-yet-shot cell.
        If cluster provided: only placements that include the cluster are considered.
        """
        counts = {}
        # union of fired and sunk to treat as already shot
        already_shot = self.fired | self.sunk
        for L in self.remaining_ships:
            placements = self._placements_for_length(L, cluster)
            for placement in placements:
                for cell in placement:
                    if cell in already_shot:
                        continue
                    counts[cell] = counts.get(cell, 0) + 1
        return counts

    def _is_cluster_sunk(self, cluster):
        """
        Determine whether a cluster of hits must be a sunk ship.
        Logic: if there exists any valid placement of ANY remaining ship length > len(cluster)
               that includes the cluster, then the cluster may not be sunk yet.
               If no such extension exists but there is at least one placement with length == len(cluster),
               we deduce it is sunk.
        """
        cluster_size = len(cluster)
        found_equal = False
        for L in self.remaining_ships:
            # placements that include cluster
            placements = self._placements_for_length(L, cluster)
            for placement in placements:
                # If placement length > cluster_size => possible extension
                if L > cluster_size:
                    # Check if placement actually extends beyond cluster into some unshot cell
                    # If so then cluster might not be sunk
                    placement_set = set(placement)
                    if any(cell not in cluster and cell not in self.fired and cell not in self.sunk for cell in placement_set):
                        return False  # can extend into an unknown cell
                    # If extension only into already fired cells (should not normally happen), treat as possible extension
                    if any(cell not in cluster for cell in placement_set):
                        # If those extra cells are misses or otherwise impossible we excluded earlier,
                        # So here treat as possible extension unless all extra cells are already hits (but they'd be in cluster)
                        return False
                elif L == cluster_size:
                    # placements that exactly match cluster size are possible sinks (if they fit)
                    if any(not (cell in self.misses or cell in self.sunk) for cell in placement):
                        # ensure placement doesn't include hits outside cluster done in _placements_for_length
                        found_equal = True
        return found_equal

    def _choose_neighbor_candidate(self, cluster):
        """
        Try to pick a plausible neighbor of the cluster (to continue targeting along an orientation).
        Prefer extension along aligned axis when cluster length >= 2.
        """
        cluster_list = sorted(cluster)
        rows = {r for r, _ in cluster_list}
        cols = {c for _, c in cluster_list}
        # determine orientation
        neighbors = []
        if len(rows) == 1 and len(cols) >= 1:
            # horizontal
            r = next(iter(rows))
            cols_sorted = sorted(cols)
            left = (r, cols_sorted[0] - 1)
            right = (r, cols_sorted[-1] + 1)
            neighbors = [left, right]
        elif len(cols) == 1 and len(rows) >= 1:
            # vertical
            c = next(iter(cols))
            rows_sorted = sorted(rows)
            up = (rows_sorted[0] - 1, c)
            down = (rows_sorted[-1] + 1, c)
            neighbors = [up, down]
        else:
            # single cell or ambiguous: consider all 4 neighbors
            r, c = next(iter(cluster))
            neighbors = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]

        # filter neighbors: in bounds, not fired, and plausible (i.e., there's at least one placement that covers cluster and the neighbor)
        plausible = []
        for n in neighbors:
            if not self._in_bounds(n[0], n[1]):
                continue
            if n in self.fired or n in self.sunk:
                continue
            # check plausibility: is there any placement for any remaining ship that includes cluster and also includes this neighbor?
            possible = False
            for L in self.remaining_ships:
                placements = self._placements_for_length(L, cluster)
                for placement in placements:
                    if n in placement:
                        # placement already validated not to overlap misses/sunk and not include hits outside cluster
                        possible = True
                        break
                if possible:
                    break
            if possible:
                plausible.append(n)
        if plausible:
            return random.choice(plausible)
        return None

    def _choose_from_pattern_or_random(self):
        """
        Fallback selection when heatmap yields nothing: try to prefer a spacing pattern based on min ship length,
        otherwise pick a random available move.
        """
        # prefer pattern where (r+c) % min_ship == 0
        pattern = [(r, c) for (r, c) in self.available_moves if (r + c) % self.min_ship == 0]
        if pattern:
            return random.choice(pattern)
        else:
            return random.choice(list(self.available_moves))

    # ----------------- Main move method -----------------
    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Return ((row, col), sunk_coords)
        - last_shot_result: 'HIT' or 'MISS' from your previous shot (None on first turn)
        - last_shot_coord: (row, col) of your previous shot (None on first turn)
        """
        sunk_report = []

        # Process the last shot result (this updates our knowledge before choosing the next move).
        if last_shot_coord is not None:
            # Ensure we don't try this cell again
            self.available_moves.discard(last_shot_coord)
            self.fired.add(last_shot_coord)

            if last_shot_result == 'HIT':
                self.hits.add(last_shot_coord)
                # Check if the hit completed/sunk a ship
                # Identify the cluster containing this last hit
                clusters = self._get_hit_clusters()
                target_cluster = None
                for cl in clusters:
                    if last_shot_coord in cl:
                        target_cluster = cl
                        break
                if target_cluster is not None and self._is_cluster_sunk(target_cluster):
                    # Deduce this cluster is a sunk ship
                    sunk_coords = list(target_cluster)
                    sunk_len = len(sunk_coords)
                    # Remove one ship of that length from remaining_ships (if present)
                    try:
                        self.remaining_ships.remove(sunk_len)
                    except ValueError:
                        # if not present (should not happen normally), ignore
                        pass
                    # Update sunk and hits sets
                    for cell in sunk_coords:
                        self.sunk.add(cell)
                        if cell in self.hits:
                            self.hits.remove(cell)
                    sunk_report = sunk_coords
            else:
                # MISS
                self.misses.add(last_shot_coord)

        # If no available moves left, return None to indicate surrender (shouldn't usually happen)
        if not self.available_moves:
            return None, []

        # Decide next move
        next_move = None

        if self.hits:
            # Target mode: pick the largest (most promising) cluster to finish
            clusters = self._get_hit_clusters()
            # prefer the cluster with most hits (bigger cluster -> higher priority)
            clusters.sort(key=lambda x: (-len(x), min(x)))
            cluster = clusters[0]

            # Build heatmap restricted to placements including this cluster
            heatmap = self._compute_heatmap(cluster)
            if heatmap:
                max_score = max(heatmap.values())
                best_cells = [cell for cell, score in heatmap.items() if score == max_score]
                next_move = random.choice(best_cells)
            else:
                # No placements found (rare) -> try neighbor probing
                neighbor = self._choose_neighbor_candidate(cluster)
                if neighbor is not None:
                    next_move = neighbor
                else:
                    # fallback to global heuristic
                    next_move = self._choose_from_pattern_or_random()
        else:
            # Hunt mode: no active hits to follow up; compute global heatmap
            heatmap = self._compute_heatmap(cluster=None)
            if heatmap:
                max_score = max(heatmap.values())
                best_cells = [cell for cell, score in heatmap.items() if score == max_score]
                next_move = random.choice(best_cells)
            else:
                # fallback pattern/random
                next_move = self._choose_from_pattern_or_random()

        # Final housekeeping: remove the chosen move from available moves and mark as fired
        if next_move is None:
            return None, sunk_report

        self.available_moves.discard(next_move)
        self.fired.add(next_move)

        return next_move, sunk_report
