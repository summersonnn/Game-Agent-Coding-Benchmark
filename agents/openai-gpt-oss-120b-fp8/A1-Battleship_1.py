"""
Agent Code: A1-Battleship
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-03 19:52:39
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Simple but effective Battleship AI.

    Strategy:
    1. **Hunt mode** – while we have no known hits we fire on a checker‑board
       pattern (cells where (row+col) is even).  This guarantees that a ship
       of length ≥ 3 cannot be missed indefinitely on an 8×8 board.
    2. **Target mode** – as soon as we hit a ship we enqueue the four
       orthogonal neighbours of that hit (if they are still unknown).  We
       then keep firing from this queue until it is empty or the ship is
       sunk (the game will give us a miss for any cell that is not part of
       the ship, automatically draining the queue).
    3. All fired cells are removed from the set of *unknown* cells so we
       never waste a shot.

    The agent keeps its own internal view of the opponent board:
        - `unknown_cells` : cells we have never shot at
        - `hit_cells`     : cells that resulted in a hit
        - `miss_cells`    : cells that resulted in a miss
        - `target_queue`  : ordered list of cells to try next while we are
                           chasing a hit
    The `make_move` method receives the result of the previous shot (if any)
    and updates the internal state before selecting the next coordinate.
    """

    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config

        # All board positions start as unknown
        self.unknown_cells = {
            (r, c) for r in range(board_size) for c in range(board_size)
        }
        self.hit_cells = set()
        self.miss_cells = set()
        self.target_queue = deque()

    def _add_adjacent_unknowns(self, row, col):
        """Enqueue orthogonal neighbours of (row, col) that are still unknown."""
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                if (nr, nc) in self.unknown_cells:
                    if (nr, nc) not in self.target_queue:
                        self.target_queue.append((nr, nc))

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Decide the next bombing coordinate.

        Parameters
        ----------
        last_shot_result : str or None
            'HIT' or 'MISS' describing the outcome of the previous shot
            (None on the very first turn).
        last_shot_coord : tuple or None
            (row, col) of the previous shot (0‑based).

        Returns
        -------
        ((row, col), []) : tuple
            The coordinate to bomb and an empty list (we do not report sunk
            ships – the game does not require it for correctness).
        """
        # ------------------------------------------------------------------
        # 1. Update internal knowledge based on the previous shot (if any)
        # ------------------------------------------------------------------
        if last_shot_coord is not None:
            r, c = last_shot_coord
            # Remove the cell from the pool of unknown cells
            self.unknown_cells.discard((r, c))
            # Also make sure it is not lingering in the target queue
            try:
                self.target_queue.remove((r, c))
            except ValueError:
                pass

            if last_shot_result == 'HIT':
                self.hit_cells.add((r, c))
                # In target mode – enqueue the four orthogonal neighbours
                self._add_adjacent_unknowns(r, c)
            else:  # MISS or any other result
                self.miss_cells.add((r, c))

        # ------------------------------------------------------------------
        # 2. Choose the next coordinate
        # ------------------------------------------------------------------
        # Target mode: we have a queue of promising cells
        while self.target_queue:
            cand = self.target_queue.popleft()
            if cand in self.unknown_cells:
                next_move = cand
                break
        else:
            # Hunt mode: checker‑board pattern to maximise coverage
            checker_cells = [
                cell for cell in self.unknown_cells
                if (cell[0] + cell[1]) % 2 == 0
            ]
            # If the checker set is empty (very late game), fall back to any unknown
            if not checker_cells:
                checker_cells = list(self.unknown_cells)

            if not checker_cells:          # no cells left – should not happen
                return None, []

            next_move = random.choice(checker_cells)

        # ------------------------------------------------------------------
        # 3. Return the chosen coordinate (no sunk information)
        # ------------------------------------------------------------------
        return next_move, []
