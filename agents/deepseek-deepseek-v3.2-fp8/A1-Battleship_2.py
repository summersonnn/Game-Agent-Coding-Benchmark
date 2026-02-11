"""
Agent Code: A1-Battleship
Model: deepseek-deepseek-v3.2-fp8
Run: 2
Generated: 2026-02-11 19:24:56
"""

from collections import deque
import random

class BattleshipAgent:
    """
    Intelligent Battleship agent with:
    - Valid random placement (guaranteed no overlap, within board)
    - Bombing: maintains hit/miss sets, targets adjacent cells, detects sunk ships
    - Hunting: uses parity (checkerboard) to increase hit probability
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.reset()

    # ----------------------------------------------------------------------
    # Game state reset (called at the beginning of each new game)
    # ----------------------------------------------------------------------
    def reset(self):
        self.shots = set()          # all coordinates already bombed
        self.hits = set()           # unsunk hits (cells that hit a ship not yet sunk)
        self.misses = set()        # known misses
        self.targets = set()       # candidate cells adjacent to unsunk hits
        self.remaining_ships = sorted(self.ships, reverse=True)   # still alive (largest first)

    # ----------------------------------------------------------------------
    # Placement helpers
    # ----------------------------------------------------------------------
    def _is_valid_placement(self, board, ship_length, start, orientation):
        row, col = start
        if orientation == 'horizontal':
            if col + ship_length > self.board_size:
                return False
            for i in range(ship_length):
                if board[row][col + i] != 'O':   # 'O' = empty
                    return False
        else:  # vertical
            if row + ship_length > self.board_size:
                return False
            for i in range(ship_length):
                if board[row + i][col] != 'O':
                    return False
        return True

    def _get_all_placements(self, board, ship_length):
        placements = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self._is_valid_placement(board, ship_length, (r, c), 'horizontal'):
                    placements.append((ship_length, (r, c), 'horizontal'))
                if self._is_valid_placement(board, ship_length, (r, c), 'vertical'):
                    placements.append((ship_length, (r, c), 'vertical'))
        return placements

    # ----------------------------------------------------------------------
    # Sunk detection and target management
    # ----------------------------------------------------------------------
    def _find_components(self, hits):
        """Return list of 4‑connected components from the hit set."""
        visited = set()
        components = []
        for h in hits:
            if h not in visited:
                q = deque([h])
                comp = set()
                while q:
                    r, c = q.popleft()
                    if (r, c) in visited:
                        continue
                    visited.add((r, c))
                    comp.add((r, c))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if (nr, nc) in hits and (nr, nc) not in visited:
                            q.append((nr, nc))
                components.append(comp)
        return components

    def _is_straight_line(self, comp):
        """Check if a component forms an unbroken horizontal or vertical line."""
        if not comp:
            return False, None, None, None, None, 0
        rows = {r for r, _ in comp}
        cols = {c for _, c in comp}
        if len(rows) == 1:          # horizontal
            row = next(iter(rows))
            min_c = min(cols)
            max_c = max(cols)
            length = max_c - min_c + 1
            expected = {(row, c) for c in range(min_c, max_c + 1)}
            if comp == expected:
                return True, 'h', row, row, min_c, max_c, length
        elif len(cols) == 1:        # vertical
            col = next(iter(cols))
            min_r = min(rows)
            max_r = max(rows)
            length = max_r - min_r + 1
            expected = {(r, col) for r in range(min_r, max_r + 1)}
            if comp == expected:
                return True, 'v', min_r, max_r, col, col, length
        return False, None, None, None, None, None, 0

    def _check_sunk_and_update(self):
        """
        Identify any fully sunk ship:
        - component is a straight line of length L
        - L is still in remaining_ships
        - both ends are off‑board or known misses
        Remove the ship and rebuild target set.
        """
        components = self._find_components(self.hits)
        sunk = False
        for comp in components:
            ok, orient, r1, r2, c1, c2, length = self._is_straight_line(comp)
            if ok and length in self.remaining_ships:
                if orient == 'h':
                    left_blocked = (c1 == 0) or ((r1, c1-1) in self.misses)
                    right_blocked = (c2 == self.board_size-1) or ((r2, c2+1) in self.misses)
                    if left_blocked and right_blocked:
                        self.remaining_ships.remove(length)
                        self.hits -= comp
                        sunk = True
                else:   # vertical
                    top_blocked = (r1 == 0) or ((r1-1, c1) in self.misses)
                    bottom_blocked = (r2 == self.board_size-1) or ((r2+1, c2) in self.misses)
                    if top_blocked and bottom_blocked:
                        self.remaining_ships.remove(length)
                        self.hits -= comp
                        sunk = True
        if sunk:
            # rebuild targets from the remaining (unsunk) hits
            self.targets.clear()
            for r, c in self.hits:
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if (nr, nc) not in self.shots and (nr, nc) not in self.targets:
                            self.targets.add((nr, nc))
        return sunk

    # ----------------------------------------------------------------------
    # Main entry point
    # ----------------------------------------------------------------------
    def make_move(self, state, feedback):
        # ----- PLACEMENT PHASE -----
        if state['phase'] == 'placement':
            # Detect start of a new game and reset state
            if state['ships_placed'] == 0:
                self.reset()

            ship_length = state['ships_to_place'][0]
            board = state['my_board']
            placements = self._get_all_placements(board, ship_length)

            if placements:
                chosen = random.choice(placements)
                return {
                    'ship_length': chosen[0],
                    'start': chosen[1],
                    'orientation': chosen[2]
                }
            else:
                # Extremely unlikely fallback – random placement (will be penalised)
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }

        # ----- BOMBING PHASE -----
        else:
            # 1. Update knowledge from the result of our last shot
            last_coord = state.get('last_shot_coord')
            last_result = state.get('last_shot_result')

            if last_coord is not None:
                self.shots.add(last_coord)

                if last_result == 'HIT':
                    self.hits.add(last_coord)
                    # Add adjacent cells as potential targets
                    r, c = last_coord
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            if (nr, nc) not in self.shots and (nr, nc) not in self.targets:
                                self.targets.add((nr, nc))
                    # Check whether any ship has been sunk
                    self._check_sunk_and_update()

                elif last_result == 'MISS':
                    self.misses.add(last_coord)
                    # Remove this coordinate from the target set if it was there
                    if last_coord in self.targets:
                        self.targets.remove(last_coord)

            # 2. Choose next target
            if self.targets:
                # We have active targets – pop one arbitrarily
                target = self.targets.pop()
            else:
                # Hunt mode: prefer cells with even parity (checkerboard) for higher hit rate
                untested = [(r, c) for r in range(self.board_size) for c in range(self.board_size)
                            if (r, c) not in self.shots]
                if untested:
                    even = [pos for pos in untested if (pos[0] + pos[1]) % 2 == 0]
                    odd  = [pos for pos in untested if (pos[0] + pos[1]) % 2 == 1]
                    # Choose from the larger parity group to keep pattern balanced
                    if len(even) >= len(odd):
                        target = random.choice(even) if even else random.choice(odd)
                    else:
                        target = random.choice(odd) if odd else random.choice(even)
                else:
                    target = (0, 0)   # should never happen

            return {'target': target}