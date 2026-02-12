"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-12 14:50:42
"""

import time
from copy import deepcopy
from copy import deepcopy
from time import sleep

import time
import random
from copy import deepcopy

class Connect4Agent:
    """
    Connect‑4 agent for the Random‑Start variant.
    Works with the engine you supplied (expects a 6×7 board,
    'R' = Red, 'Y' = Yellow, ' ' = empty).
    """

    # ------------------------------------------------------------------
    #  Public API (required by the engine)
    # ------------------------------------------------------------------
    def __init__(self, name: str, symbol: str):
        """
        Parameters
        ----------
        name : str
            Human readable name – used only for reporting.
        symbol : str
            'R' for Red or 'Y' for Yellow.  The engine will always call
            make_move() when it is this symbol's turn.
        """
        if symbol not in ("R", "Y"):
            raise ValueError("symbol must be 'R' or 'Y'")
        self.name = name
        self.my_piece = symbol
        self.opp_piece = "Y" if symbol == "R" else "R"

        # --- search parameters (tuned for the 1 s limit) -----------------
        self.time_limit = 0.90          # seconds (leave a safety margin)
        self.max_depth = 5              # will be reduced if we run out of time
        self.start_time = None

        # Pre‑compute column order for move‑ordering (centre first)
        self.column_order = [3, 2, 4, 1, 5, 0, 6]

    # ------------------------------------------------------------------
    def make_move(self, board):
        """
        Return the column (0‑6) where we want to drop a disc.

        The engine passes us a **copy** of the current board, so we can
        modify it safely if we want to.
        """
        self.start_time = time.time()

        legal_cols = self._legal_moves(board)
        # Defensive programming – the engine guarantees at least one legal move,
        # but we keep the check just in case.
        if not legal_cols:
            return 3  # centre (any column would be illegal, but this will never happen)

        # --------------------------------------------------------------
        # 1) Immediate win / block
        # --------------------------------------------------------------
        for col in legal_cols:
            # Simulate our move
            r, _ = self._drop(board, col, self.my_piece)
            if self._is_winning_move(board, r, col, self.my_piece):
                return col
            # Undo
            board[r][col] = " "

        # Block opponent's immediate win
        for col in legal_cols:
            r, _ = self._drop(board, col, self.opp_piece)
            if self._is_winning_move(board, r, col, self.opp_piece):
                # Undo before returning
                board[r][col] = " "
                return col
            board[r][col] = " "

        # --------------------------------------------------------------
        # 2) Negamax search (alpha‑beta) – iterative deepening
        # --------------------------------------------------------------
        best_col = random.choice(legal_cols)   # fallback
        best_score = -float('inf')

        # Iterative deepening: start shallow, increase depth while we have time.
        for depth in range(1, self.max_depth + 1):
            if self._time_up():
                break
            score, col = self._negamax(board, depth, -float('inf'), float('inf'), True)
            if self._time_up():
                break
            # In the very rare case that the search returns None (no move)
            # we keep the previous best.
            if col is not None:
                best_score, best_col = score, col

        return best_col

    # ------------------------------------------------------------------
    #  Internal helper methods (not part of the public API)
    # ------------------------------------------------------------------

    # --------------------------------------------------------------
    # Timing
    # --------------------------------------------------------------
    def _time_up(self) -> bool:
        """True if we have exceeded the allotted time."""
        return (time.time() - self.start_time) >= self.time_limit

    # --------------------------------------------------------------
    # Board utilities
    # --------------------------------------------------------------
    ROWS = 6
    COLS = 7
    EMPTY = " "

    def _legal_moves(self, board):
        """Return a list of columns that are not full."""
        return [c for c in self.column_order if board[0][c] == self.EMPTY]

    def _drop(self, board, col, piece):
        """
        Drop a piece in `col` on the supplied board.
        Returns (row, col) where the piece landed, or (None, None) if the column is full.
        """
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                board[r][col] = piece
                return r, col
        return None, None

    # --------------------------------------------------------------
    # Win detection (used during search)
    # --------------------------------------------------------------
    def _is_winning_move(self, board, row, col, piece):
        """Check whether placing `piece` at (row, col) creates a 4‑in‑a‑row."""
        if row is None:
            return False

        # Directions: (dr, dc)
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1  # the piece we just placed
            # forward
            r, c = row + dr, col + dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and board[r][c] == piece:
                count += 1
                r += dr
                c += dc
            # backward
            r, c = row - dr, col - dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and board[r][c] == piece:
                count += 1
                r -= dr
                c -= dc

            if count >= 4:
                return True
        return False

    # --------------------------------------------------------------
    # Evaluation function
    # --------------------------------------------------------------
    def _evaluate(self, board):
        """
        Heuristic score from the point of view of `self.my_piece`.
        Positive = good for us, Negative = good for opponent.
        """
        SCORE_FOUR = 100000   # guaranteed win
        SCORE_THREE = 1000
        SCORE_TWO = 100
        SCORE_ONE = 10

        # Helper to count windows of length 4
        def count_window(window, piece):
            opp = self.opp_piece
            if opp in window:
                return 0
            cnt = window.count(piece)
            if cnt == 4:
                return SCORE_FOUR
            elif cnt == 3:
                return SCORE_THREE
            elif cnt == 2:
                return SCORE_TWO
            elif cnt == 1:
                return SCORE_ONE
            else:
                return 0

        total = 0

        # Horizontal windows
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r][c + i] for i in range(4)]
                total += count_window(window, self.my_piece)
                total -= count_window(window, self.opp_piece)

        # Vertical windows
        for c in range(self.COLS):
            for r in range(self.ROWS - 3):
                window = [board[r + i][c] for i in range(4)]
                total += count_window(window, self.my_piece)
                total -= count_window(window, self.opp_piece)

        # Positive‑slope diagonal windows (/)
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                total += count_window(window, self.my_piece)
                total -= count_window(window, self.opp_piece)

        # Negative‑slope diagonal windows (\)
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                total += count_window(window, self.my_piece)
                total -= count_window(window, self.opp_piece)

        return total

    # --------------------------------------------------------------
    # Negamax with alpha‑beta pruning
    # --------------------------------------------------------------
    def _negamax(self, board, depth, alpha, beta, is_root):
        """
        Returns (score, best_column).  The score is from the viewpoint of
        the player to move (positive = good for that player).
        """
        if self._time_up():
            # Abort search – treat as a neutral score
            return 0, None

        legal = self._legal_moves(board)

        # Terminal test
        if depth == 0 or not legal:
            # If board is full we treat it as a draw (score 0)
            return self._evaluate(board), None

        best_score = -float('inf')
        best_col = None

        for col in legal:
            # Simulate move
            r, _ = self._drop(board, col, self.my_piece if is_root else self.opp_piece)
            win = self._is_winning_move(board, r, col,
                                        self.my_piece if is_root else self.opp_piece)

            if win:
                # Immediate win for the player who just moved.
                # From the perspective of the *current* player we return
                # a huge positive value (or negative if it's the opponent).
                score = (self.ROWS * self.COLS + 1) if is_root else -(self.ROWS * self.COLS + 1)
                # Undo
                board[r][col] = self.EMPTY
                return score, col

            # Recurse – note the colour flip (negamax trick)
            sub_score, _ = self._negamax(board, depth - 1, -beta, -alpha, False)
            sub_score = -sub_score   # because we swapped players

            # Undo move
            board[r][col] = self.EMPTY

            if sub_score > best_score:
                best_score = sub_score
                best_col = col
            alpha = max(alpha, best_score)
            if alpha >= beta:
                # Cut‑off
                break

        return best_score, best_col
