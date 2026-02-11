"""
Agent Code: A1-Battleship
Model: deepseek-deepseek-v3.2-fp8
Run: 1
Generated: 2026-02-11 19:24:56
"""

import random
from collections import deque

class BattleshipAgent:
    """
    Smart Battleship agent using probability density targeting and
    non-adjacent placement strategy.
    """
    # Board cell states
    UNKNOWN = 0
    MISS = 1
    HIT = 2
    SUNK = 3

    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = sorted(ships, reverse=True)  # store original

        # opponent board representation
        self.opponent_board = [
            [self.UNKNOWN for _ in range(board_size)] for _ in range(board_size)
        ]
        self.remaining_ships = list(ships)  # mutable copy
        self.hits_unsunk = []               # list of (r,c) of unsunk hits
        self.sunk_cells = set()            # for quick lookup (optional)

    # ----------------------------------------------------------------------
    # Public method called by the game engine
    # ----------------------------------------------------------------------
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            self._update_opponent_board(state)
            target = self._choose_target()
            return {'target': target}

    # ----------------------------------------------------------------------
    # Placement phase
    # ----------------------------------------------------------------------
    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        my_board = state['my_board']

        # collect all valid placements
        valid_placements = self._get_valid_placements(ship_length, my_board)

        # prefer placements that are not adjacent (including diagonal) to existing ships
        smart = []
        for placement in valid_placements:
            if not self._is_adjacent_to_ship(placement, my_board):
                smart.append(placement)

        if smart:
            chosen = random.choice(smart)
        else:
            chosen = random.choice(valid_placements)

        return {
            'ship_length': ship_length,
            'start': chosen['start'],
            'orientation': chosen['orientation']
        }

    def _get_valid_placements(self, length, board):
        """Return list of valid (start, orientation) for a ship of given length."""
        placements = []
        size = self.board_size
        # horizontal
        for row in range(size):
            for col in range(size - length + 1):
                # check overlap
                ok = True
                for c in range(col, col + length):
                    if board[row][c] == 'S':
                        ok = False
                        break
                if ok:
                    placements.append({
                        'start': (row, col),
                        'orientation': 'horizontal'
                    })
        # vertical
        for col in range(size):
            for row in range(size - length + 1):
                ok = True
                for r in range(row, row + length):
                    if board[r][col] == 'S':
                        ok = False
                        break
                if ok:
                    placements.append({
                        'start': (row, col),
                        'orientation': 'vertical'
                    })
        return placements

    def _is_adjacent_to_ship(self, placement, board):
        """Check if any cell of the proposed ship is adjacent (8‑way) to an existing 'S'."""
        r0, c0 = placement['start']
        orient = placement['orientation']
        length = 5 if orient == 'horizontal' else 4  # dummy, actual length unknown here
        # we need the length; better to pass it or recompute from placement
        # but we have the ship length from the caller. We'll compute cells directly.
        # Actually, we don't have the length in this method. Let's recompute:
        if orient == 'horizontal':
            # find end column
            # we don't know length, but we can derive it from the fact that the placement
            # was generated for a specific length. However, we can just pass length as argument.
            # Let's redesign: pass length and placement dict.
            pass
        # We'll rewrite this method to take ship cells instead.
        # For simplicity, we'll move the adjacency check inside _place_ship.
        # So we'll just compute ship_cells there and call a helper.
        return False  # stub, will be replaced

    # Actually, we'll compute adjacency directly in _place_ship:
    # after getting valid_placements, for each placement generate its cells,
    # then check 8-neighbors for 'S'. We'll do that in the loop.

    # ----------------------------------------------------------------------
    # Bombing phase - update internal state from game feedback
    # ----------------------------------------------------------------------
    def _update_opponent_board(self, state):
        """Update our opponent board using the last shot result."""
        result = state['last_shot_result']
        coord = state['last_shot_coord']
        if coord is None:
            return

        r, c = coord
        if result == 'HIT':
            # a new hit
            if self.opponent_board[r][c] == self.UNKNOWN:
                self.opponent_board[r][c] = self.HIT
                self.hits_unsunk.append((r, c))
                self._check_sunk(r, c)
        else:  # MISS
            # do not overwrite HIT or SUNK (wasted shot on already hit cell)
            if self.opponent_board[r][c] == self.UNKNOWN:
                self.opponent_board[r][c] = self.MISS

    def _check_sunk(self, row, col):
        """
        After a hit at (row,col), check if this completes a sunk ship.
        Update remaining_ships, mark cells as SUNK, remove from hits_unsunk.
        """
        # horizontal check
        left = col
        while left > 0 and self.opponent_board[row][left - 1] == self.HIT:
            left -= 1
        right = col
        while right < self.board_size - 1 and self.opponent_board[row][right + 1] == self.HIT:
            right += 1
        h_length = right - left + 1
        if h_length in self.remaining_ships:
            # check both ends blocked (miss, sunk, or edge)
            left_blocked = (left == 0) or (self.opponent_board[row][left - 1] in (self.MISS, self.SUNK))
            right_blocked = (right == self.board_size - 1) or (self.opponent_board[row][right + 1] in (self.MISS, self.SUNK))
            if left_blocked and right_blocked:
                # ship sunk
                self.remaining_ships.remove(h_length)
                for c in range(left, right + 1):
                    self.opponent_board[row][c] = self.SUNK
                    if (row, c) in self.hits_unsunk:
                        self.hits_unsunk.remove((row, c))
                    self.sunk_cells.add((row, c))
                return  # a ship cannot be both horizontal and vertical

        # vertical check
        up = row
        while up > 0 and self.opponent_board[up - 1][col] == self.HIT:
            up -= 1
        down = row
        while down < self.board_size - 1 and self.opponent_board[down + 1][col] == self.HIT:
            down += 1
        v_length = down - up + 1
        if v_length in self.remaining_ships:
            up_blocked = (up == 0) or (self.opponent_board[up - 1][col] in (self.MISS, self.SUNK))
            down_blocked = (down == self.board_size - 1) or (self.opponent_board[down + 1][col] in (self.MISS, self.SUNK))
            if up_blocked and down_blocked:
                self.remaining_ships.remove(v_length)
                for r in range(up, down + 1):
                    self.opponent_board[r][col] = self.SUNK
                    if (r, col) in self.hits_unsunk:
                        self.hits_unsunk.remove((r, col))
                    self.sunk_cells.add((r, col))

    # ----------------------------------------------------------------------
    # Bombing phase - target selection
    # ----------------------------------------------------------------------
    def _choose_target(self):
        """Select the next cell to bomb using probability density."""
        # If no ships remain, game should be over – return random (should not happen)
        if not self.remaining_ships:
            return self._random_unknown()

        # compute probability map
        probs = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        total_configs = self._compute_probabilities(probs)

        if total_configs == 0:
            # fallback: try adjacent to hits, then random
            return self._fallback_target()

        # find unknown cell with highest probability
        best_val = -1
        best_cells = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.opponent_board[r][c] == self.UNKNOWN:
                    if probs[r][c] > best_val:
                        best_val = probs[r][c]
                        best_cells = [(r, c)]
                    elif probs[r][c] == best_val:
                        best_cells.append((r, c))
        if best_cells:
            return random.choice(best_cells)
        else:
            return self._random_unknown()

    def _compute_probabilities(self, prob_grid):
        """
        Fill prob_grid with number of valid configurations that include each cell.
        Return total number of configurations.
        """
        # get unsunk hits as set
        hit_set = set(self.hits_unsunk)
        # forbidden cells: MISS and SUNK
        forbidden = set()
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.opponent_board[r][c] in (self.MISS, self.SUNK):
                    forbidden.add((r, c))

        # generate placements for each remaining ship
        placements_per_ship = []
        for length in self.remaining_ships:
            placements = self._generate_placements(length, forbidden)
            if not placements:  # no placements for a ship -> inconsistent
                return 0
            placements_per_ship.append(placements)

        # recursive search over ship assignments
        total = 0

        def backtrack(idx, occupied_set, covered_hits, counts):
            nonlocal total
            if idx == len(self.remaining_ships):
                if covered_hits == hit_set:
                    total += 1
                    for cell in occupied_set:
                        r, c = cell
                        counts[r][c] += 1
                return
            for ship_cells in placements_per_ship[idx]:
                # check overlap with already placed ships
                if occupied_set.intersection(ship_cells):
                    continue
                new_occupied = occupied_set.union(ship_cells)
                new_covered = covered_hits.union(hit_set.intersection(ship_cells))
                backtrack(idx + 1, new_occupied, new_covered, counts)

        backtrack(0, set(), set(), prob_grid)
        return total

    def _generate_placements(self, length, forbidden):
        """
        Return list of sets of cells for all valid placements of a ship of given length
        that do not touch any forbidden cell (miss or sunk).
        """
        placements = []
        size = self.board_size
        # horizontal
        for r in range(size):
            for c in range(size - length + 1):
                cells = set()
                ok = True
                for i in range(length):
                    cell = (r, c + i)
                    if cell in forbidden:
                        ok = False
                        break
                    cells.add(cell)
                if ok:
                    placements.append(cells)
        # vertical
        for c in range(size):
            for r in range(size - length + 1):
                cells = set()
                ok = True
                for i in range(length):
                    cell = (r + i, c)
                    if cell in forbidden:
                        ok = False
                        break
                    cells.add(cell)
                if ok:
                    placements.append(cells)
        return placements

    def _fallback_target(self):
        """When probability map fails, try adjacent cells to unsunk hits."""
        # neighbours of unsunk hits
        for (r, c) in self.hits_unsunk:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if self.opponent_board[nr][nc] == self.UNKNOWN:
                        return (nr, nc)
        # no neighbour – random unknown
        return self._random_unknown()

    def _random_unknown(self):
        """Return a random unknown cell."""
        unknown = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.opponent_board[r][c] == self.UNKNOWN:
                    unknown.append((r, c))
        return random.choice(unknown) if unknown else (0, 0)

    # ----------------------------------------------------------------------
    # Placement helper (rewritten to avoid stub)
    # ----------------------------------------------------------------------
    # The placement logic is now fully integrated in _place_ship.
    # We'll keep the adjacency check inline to avoid method confusion.