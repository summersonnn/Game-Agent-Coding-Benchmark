"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-12 14:50:42
"""

import copy
from __future__ import annotations

import random
import copy

class Connect4Agent:
    """
    Connect‑4 agent that follows the “Random‑Start” rules.
    Symbol must be either 'R' (red) or 'Y' (yellow).
    """
    ROWS = 6
    COLS = 7
    EMPTY = ' '

    def __init__(self, name: str, symbol: str):
        """
        Parameters
        ----------
        name : str
            Human‑readable name of the agent (used only for logging / debugging).
        symbol : str
            Our disc symbol – either 'R' or 'Y'.
        """
        if symbol not in ('R', 'Y'):
            raise ValueError("symbol must be 'R' or 'Y'")
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'

    # ------------------------------------------------------------------ #
    # Helper methods – keep them private; the engine only calls make_move
    # ------------------------------------------------------------------ #
    def _drop(self, board, col, disc):
        """Return (row, col) after dropping `disc` in `col`, or None if full."""
        if not (0 <= col < self.COLS):
            return None
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                board[r][col] = disc
                return r, col
        return None                     # column is full

    def _is_winning_move(self, board, col, disc):
        """True if dropping `disc` in `col` creates a 4‑in‑a‑row."""
        tmp = copy.deepcopy(board)
        pos = self._drop(tmp, col, disc)
        if pos is None:
            return False
        r, c = pos
        # Directions: horiz, vert, diag /, diag \
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in dirs:
            count = 1
            # forward
            rr, cc = r + dr, c + dc
            while 0 <= rr < self.ROWS and 0 <= cc < self.COLS and tmp[rr][cc] == disc:
                count += 1
                rr += dr
                cc += dc
            # backward
            rr, cc = r - dr, c - dc
            while 0 <= rr < self.ROWS and 0 <= cc < self.COLS and tmp[rr][cc] == disc:
                count += 1
                rr -= dr
                cc -= dc
            if count >= 4:
                return True
        return False

    def _legal_columns(self, board):
        """List of column indices that are not full."""
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    # ------------------------------------------------------------------ #
    # Heuristic evaluation (step 4 of the strategy)
    # ------------------------------------------------------------------ #
    def _score_window(self, window, disc):
        """
        Heuristic for a length‑4 window.
        +100 for 4 of our discs,
        +5  for 3 of ours + 1 empty,
        +2  for 2 of ours + 2 empty,
        -4  for opponent 3 + 1 empty (danger),
        -1  for opponent 2 + 2 empty.
        """
        opp = self.opponent
        if window.count(disc) == 4:
            return 100
        if window.count(disc) == 3 and window.count(self.EMPTY) == 1:
            return 5
        if window.count(disc) == 2 and window.count(self.EMPTY) == 2:
            return 2
        if window.count(opp) == 3 and window.count(self.EMPTY) == 1:
            return -4
        if window.count(opp) == 2 and window.count(self.EMPTY) == 2:
            return -1
        return 0

    def _evaluate_board(self, board):
        """
        Simple static evaluation for the current board.
        Positive → good for us, Negative → good for opponent.
        """
        score = 0
        # ----- centre column (most valuable) -----
        centre_col = [board[r][self.COLS // 2] for r in range(self.ROWS)]
        centre_count = centre_col.count(self.symbol)
        score += centre_count * 3   # weight centre occupancy

        # ----- horizontal -----
        for r in range(self.ROWS):
            row_array = board[r]
            for c in range(self.COLS - 3):
                window = row_array[c:c + 4]
                score += self._score_window(window, self.symbol)

        # ----- vertical -----
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r + 4]
                score += self._score_window(window, self.symbol)

        # ----- diagonal (positive slope) -----
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += self._score_window(window, self.symbol)

        # ----- diagonal (negative slope) -----
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += self._score_window(window, self.symbol)

        return score

    # ------------------------------------------------------------------ #
    # Public API – the only method the engine calls
    # ------------------------------------------------------------------ #
    def make_move(self, board):
        """
        Return the column index (0‑6) where we want to drop our disc.

        The engine guarantees that `board` is a *copy* – we must never
        modify it in‑place, otherwise we would affect the real game state.
        """
        legal = self._legal_columns(board)

        # 1️⃣  Immediate win?
        for col in legal:
            if self._is_winning_move(board, col, self.symbol):
                return col

        # 2️⃣  Block opponent immediate win?
        for col in legal:
            if self._is_winning_move(board, col, self.opponent):
                return col

        # 3️⃣  Prefer centre column if possible
        centre = self.COLS // 2
        if centre in legal:
            # give centre a slight boost but still evaluate others
            # (helps in early game when centre is open)
            pass  # we keep it in the candidate list – scoring will favour it

        # 4️⃣  Score each legal move using the static evaluation
        best_score = -float('inf')
        best_cols = []
        for col in legal:
            # Simulate the move
            tmp_board = copy.deepcopy(board)
            self._drop(tmp_board, col, self.symbol)

            # Evaluate resulting board
            score = self._evaluate_board(tmp_board)

            # Small deterministic bias: centre column gets +0.5
            if col == centre:
                score += 0.5

            if score > best_score:
                best_score = score
                best_cols = [col]
            elif score == best_score:
                best_cols.append(col)

        # 5️⃣  Choose randomly among the best‑scoring columns
        return random.choice(best_cols) if best_cols else random.choice(legal)

# ---------------------------------------------------------------------- #
# Example of a quick sanity‑check (run locally, not part of the submission)
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simple self‑play to verify the agent never crashes
    from __future__ import annotations

    class DummyAgent(Connect4Agent):
        """A very dumb opponent that just picks a random legal column."""
        def make_move(self, board):
            legal = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
            return random.choice(legal)

    game = Connect4Game()
    red  = Connect4Agent("SmartRed", Connect4Game.RED)
    yellow = DummyAgent("RandomYellow", Connect4Game.YELLOW)

    winner = game.play_game(red, yellow)
    print("Winner:", winner)
