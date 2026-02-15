"""
Agent Code: A1-Battleship
Model: deepseek-deepseek-v3.2-fp8
Run: 2
Generated: 2026-02-11 19:24:56
"""


import random
from collections import deque

class BattleshipAgent:
    """
    A smart Battleship agent that uses probabilistic targeting and a hunt mode.
    - Placement: chooses a random valid location for each ship.
    - Bombing: maintains a probability map over unknown cells, and switches to
      hunt mode after a hit to explore adjacent cells.
    """

    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships  # list of ship lengths, e.g. [5,4,3]

        # opponent board: 0 = unknown, 1 = miss, 2 = hit
        self.opponent_grid = [[0] * board_size for _ in range(board_size)]

        # queue of cells to try when in hunt mode (after a hit)
        self.hunt_queue = deque()

    def make_move(self, state, feedback):
        # ----- PLACEMENT PHASE -----
        if state['phase'] == 'placement':
            ship_len = state['ships_to_place'][0]
            my_board = state['my_board']

            # collect all valid placements for this ship
            valid_placements = []

            # horizontal
            for r in range(self.board_size):
                for c in range(self.board_size - ship_len + 1):
                    if all(my_board[r][c + i] == 'O' for i in range(ship_len)):
                        valid_placements.append((ship_len, (r, c), 'horizontal'))
            # vertical
            for r in range(self.board_size - ship_len + 1):
                for c in range(self.board_size):
                    if all(my_board[r + i][c] == 'O' for i in range(ship_len)):
                        valid_placements.append((ship_len, (r, c), 'vertical'))

            # choose randomly among them (guaranteed to be valid)
            chosen = random.choice(valid_placements)
            return {
                'ship_length': chosen[0],
                'start': chosen[1],
                'orientation': chosen[2]
            }

        # ----- BOMBING PHASE -----
        else:
            # update our knowledge from the last shot (if any)
            last_coord = state['last_shot_coord']
            last_result = state['last_shot_result']
            if last_coord is not None:
                r, c = last_coord
                if last_result == 'HIT':
                    self.opponent_grid[r][c] = 2   # hit
                    # add neighbours to hunt queue (if unknown)
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            if self.opponent_grid[nr][nc] == 0:
                                self.hunt_queue.append((nr, nc))
                elif last_result == 'MISS':
                    self.opponent_grid[r][c] = 1   # miss

            # decide next target
            # 1. if we have pending hunt targets, use them
            while self.hunt_queue:
                r, c = self.hunt_queue.popleft()
                if self.opponent_grid[r][c] == 0:   # still unknown
                    return {'target': (r, c)}
                # otherwise already known – skip

            # 2. otherwise compute a probability map over all unknown cells
            best_score = -1
            candidates = []

            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self.opponent_grid[r][c] != 0:
                        continue

                    score = 0
                    for L in self.ships:   # consider all ships (still afloat assumption)
                        # horizontal placements covering (r,c)
                        for start_c in range(max(0, c - L + 1), min(c, self.board_size - L) + 1):
                            valid = True
                            for i in range(L):
                                if self.opponent_grid[r][start_c + i] == 1:   # miss
                                    valid = False
                                    break
                            if valid:
                                score += 1
                        # vertical placements covering (r,c)
                        for start_r in range(max(0, r - L + 1), min(r, self.board_size - L) + 1):
                            valid = True
                            for i in range(L):
                                if self.opponent_grid[start_r + i][c] == 1:
                                    valid = False
                                    break
                            if valid:
                                score += 1

                    if score > best_score:
                        best_score = score
                        candidates = [(r, c)]
                    elif score == best_score:
                        candidates.append((r, c))

            if candidates:
                chosen = random.choice(candidates)
                return {'target': chosen}

            # fallback (should never happen on a non‑full board)
            unknowns = [(r, c) for r in range(self.board_size)
                        for c in range(self.board_size) if self.opponent_grid[r][c] == 0]
            if unknowns:
                return {'target': random.choice(unknowns)}
            else:
                # every cell has been shot – game should have ended, but return something
                return {'target': (0, 0)}
