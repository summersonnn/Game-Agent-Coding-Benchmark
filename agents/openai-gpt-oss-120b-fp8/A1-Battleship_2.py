"""
Agent Code: A1-Battleship
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-10 16:22:20
"""

from collections import deque

import random
from collections import deque

# Board symbols used by the game engine
EMPTY = 'O'
SHIP = 'S'
HIT = 'X'
MISS = 'M'

class BattleshipAgent:
    """
    BattleshipAgent implements a deterministic placement strategy and a
    hunt‑target bombing strategy with simple probability scoring.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships                     # original list e.g. [5,4,3]

        # ---------- Placement state ----------
        # attempts made for the current ship length
        self._placement_attempts = {}

        # ---------- Bombing state ----------
        # cells we still want to investigate after a hit
        self._target_queue = deque()

        # remaining ship lengths that have not been sunk yet
        self._remaining_ships = list(ships)

        # set of coordinates already tried (filled each turn)
        self._tried = set()

    # ----------------------------------------------------------------------
    # Placement helpers
    # ----------------------------------------------------------------------
    def _first_valid_placement(self, board, ship_len):
        """Return the first valid placement (row, col, orientation) that fits."""
        for orientation in ('horizontal', 'vertical'):
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if orientation == 'horizontal':
                        if c + ship_len > self.board_size:
                            continue
                        if all(board[r][c + i] == EMPTY for i in range(ship_len)):
                            return (r, c, orientation)
                    else:  # vertical
                        if r + ship_len > self.board_size:
                            continue
                        if all(board[r + i][c] == EMPTY for i in range(ship_len)):
                            return (r, c, orientation)
        return None

    # ----------------------------------------------------------------------
    # Bombing helpers
    # ----------------------------------------------------------------------
    def _update_tried(self, shot_history):
        """Refresh the set of already‑tried cells."""
        self._tried = {tuple(entry['coord']) for entry in shot_history}

    def _cluster_hits(self, shot_history):
        """Group hit cells into orthogonal clusters."""
        hits = {tuple(entry['coord']) for entry in shot_history
                if entry['result'] == 'HIT'}
        visited = set()
        clusters = []

        for cell in hits:
            if cell in visited:
                continue
            stack = [cell]
            cluster = []
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                cluster.append(cur)
                r, c = cur
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (r + dr, c + dc)
                    if nb in hits and nb not in visited:
                        stack.append(nb)
            clusters.append(cluster)
        return clusters

    def _prune_sunk_ships(self, shot_history):
        """
        Remove lengths from _remaining_ships when a cluster size matches a
        ship length (i.e. the ship has been sunk).
        """
        clusters = self._cluster_hits(shot_history)
        remaining = list(self._remaining_ships)

        for cluster in clusters:
            size = len(cluster)
            # try to find an exact match in the remaining list
            for length in sorted(remaining, reverse=True):
                if size == length:
                    remaining.remove(length)
                    break
        self._remaining_ships = remaining

    def _populate_target_queue(self, shot_history):
        """
        After a hit (or a cluster of hits) add sensible neighbour cells to the
        target queue.  The queue is cleared each turn before being refilled.
        """
        self._target_queue.clear()
        clusters = self._cluster_hits(shot_history)

        # keep only clusters that are not already accounted for as sunk
        unsunk = [c for c in clusters
                  if len(c) not in [l for l in self.ships if l not in self._remaining_ships]]

        for cluster in unsunk:
            if len(cluster) == 1:
                # single hit – add the four orthogonal neighbours
                r, c = cluster[0]
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < self.board_size and 0 <= nc < self.board_size
                            and (nr, nc) not in self._tried):
                        self._target_queue.append((nr, nc))
            else:
                # line of hits – extend the line at both ends
                rows = {r for r, _ in cluster}
                cols = {c for _, c in cluster}
                if len(rows) == 1:          # horizontal line
                    r = rows.pop()
                    min_c, max_c = min(cols), max(cols)
                    for nc in (min_c - 1, max_c + 1):
                        if 0 <= nc < self.board_size and (r, nc) not in self._tried:
                            self._target_queue.append((r, nc))
                else:                        # vertical line
                    c = cols.pop()
                    min_r, max_r = min(rows), max(rows)
                    for nr in (min_r - 1, max_r + 1):
                        if 0 <= nr < self.board_size and (nr, c) not in self._tried:
                            self._target_queue.append((nr, c))

    def _score_cells(self, candidates):
        """
        Simple probability scoring: for each remaining ship length, count how
        many placements would still be possible that include the candidate cell.
        """
        scores = {}
        max_score = -1

        for r, c in candidates:
            score = 0
            for ship_len in self._remaining_ships:
                # horizontal placements covering (r,c)
                for start_c in range(c - ship_len + 1, c + 1):
                    if start_c < 0 or start_c + ship_len > self.board_size:
                        continue
                    # placement must not intersect a known miss
                    if any((r, cc) in self._tried and (r, cc) not in self._hit_set
                           for cc in range(start_c, start_c + ship_len)):
                        continue
                    score += 1

                # vertical placements covering (r,c)
                for start_r in range(r - ship_len + 1, r + 1):
                    if start_r < 0 or start_r + ship_len > self.board_size:
                        continue
                    if any((rr, c) in self._tried and (rr, c) not in self._hit_set
                           for rr in range(start_r, start_r + ship_len)):
                        continue
                    score += 1

            scores[(r, c)] = score
            if score > max_score:
                max_score = score

        # return all cells that share the highest score
        best = [cell for cell, sc in scores.items() if sc == max_score]
        return best

    # ----------------------------------------------------------------------
    # Public interface
    # ----------------------------------------------------------------------
    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases.
        """
        # --------------------------------------------------------------
        # Placement phase
        # --------------------------------------------------------------
        if state['phase'] == 'placement':
            ship_len = state['ships_to_place'][0]

            # keep track of attempts (used only for possible future extensions)
            self._placement_attempts[ship_len] = self._placement_attempts.get(ship_len, 0) + 1

            # try to find a deterministic valid placement on the current board
            placement = self._first_valid_placement(state['my_board'], ship_len)
            if placement:
                r, c, orient = placement
                return {
                    'ship_length': ship_len,
                    'start': (r, c),
                    'orientation': orient
                }

            # fallback – random placement (should only happen if board is somehow full)
            orient = random.choice(['horizontal', 'vertical'])
            if orient == 'horizontal':
                r = random.randint(0, self.board_size - 1)
                c = random.randint(0, self.board_size - ship_len)
            else:
                r = random.randint(0, self.board_size - ship_len)
                c = random.randint(0, self.board_size - 1)

            return {
                'ship_length': ship_len,
                'start': (r, c),
                'orientation': orient
            }

        # --------------------------------------------------------------
        # Bombing phase
        # --------------------------------------------------------------
        # Update internal knowledge from the history supplied by the engine
        shot_history = state['shot_history']
        self._update_tried(shot_history)

        # set of cells that are known hits (used by the scoring routine)
        self._hit_set = {tuple(entry['coord']) for entry in shot_history
                         if entry['result'] == 'HIT'}

        # Remove sunk ships from the remaining‑ship list
        self._prune_sunk_ships(shot_history)

        # Populate the target queue if we have fresh hit information
        if state['last_shot_result'] == 'HIT' and state['turn_continues']:
            # the most recent hit is guaranteed to be in shot_history already
            self._populate_target_queue(shot_history)
        elif not self._target_queue:
            # no pending targets – try to keep the queue fresh each turn
            self._populate_target_queue(shot_history)

        # --------------------------------------------------------------
        # 1) Resolve any pending target cells (target mode)
        # --------------------------------------------------------------
        while self._target_queue:
            cand = self._target_queue.popleft()
            if cand not in self._tried:
                return {'target': cand}

        # --------------------------------------------------------------
        # 2) Hunt mode – choose the most promising unknown cell
        # --------------------------------------------------------------
        # candidates respecting a checkerboard pattern (helps for ships >=2)
        candidates = [(r, c) for r in range(self.board_size)
                      for c in range(self.board_size)
                      if (r, c) not in self._tried and ((r + c) % 2 == 0)]

        # if the board is small or many cells already tried, fall back to any unknown cell
        if not candidates:
            candidates = [(r, c) for r in range(self.board_size)
                          for c in range(self.board_size)
                          if (r, c) not in self._tried]

        # pick the cell(s) with the highest placement score
        best_cells = self._score_cells(candidates)
        target = random.choice(best_cells)

        return {'target': target}
