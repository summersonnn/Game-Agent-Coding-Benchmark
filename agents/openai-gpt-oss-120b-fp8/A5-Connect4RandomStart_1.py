"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-17 13:57:36
"""

import math
import copy
import time

import random
import math
import copy
import time

class Connect4Agent:
    """
    A simple but strong Connect‑4 agent.

    Strategy (in order of priority):
    1. Win immediately if possible.
    2. Block opponent's immediate winning move.
    3. Use a depth‑limited minimax search with alpha‑beta pruning
       (default depth = 4). The evaluation function favours centre columns,
       potential 2‑ and 3‑in‑a‑rows and penalises opponent threats.
    """

    ROWS = 6
    COLS = 7
    EMPTY = ' '

    def __init__(self, name: str, symbol: str):
        """
        name   – arbitrary identifier (not used by the agent)
        symbol – 'R' for Red or 'Y' for Yellow
        """
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        # depth can be tuned; 4 gives a good trade‑off between strength and speed
        self.search_depth = 4

    # --------------------------------------------------------------------- #
    # Helper methods operating on the board (list of lists, row‑major order) #
    # --------------------------------------------------------------------- #

    def _valid_columns(self, board):
        """Return a list of column indices that are not full."""
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    def _drop(self, board, col, disc):
        """
        Return a new board with `disc` placed in `col`.
        Assumes the column is not full.
        """
        new_board = [row[:] for row in board]
        for r in range(self.ROWS - 1, -1, -1):
            if new_board[r][col] == self.EMPTY:
                new_board[r][col] = disc
                break
        return new_board

    def _winner(self, board):
        """Detect a winner on the given board; return 'R', 'Y' or None."""
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                s = board[r][c]
                if s != self.EMPTY and s == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return s
        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                s = board[r][c]
                if s != self.EMPTY and s == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return s
        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                s = board[r][c]
                if s != self.EMPTY and s == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return s
        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                s = board[r][c]
                if s != self.EMPTY and s == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return s
        return None

    def _window_score(self, window, disc):
        """
        Score a list of four cells (`window`) for `disc`.
        Positive values favour `disc`, negative values favour opponent.
        """
        opp = self.opponent
        count_disc = window.count(disc)
        count_opp = window.count(opp)
        count_empty = window.count(self.EMPTY)

        if count_disc == 4:
            return 100000
        if count_disc == 3 and count_empty == 1:
            return 100
        if count_disc == 2 and count_empty == 2:
            return 10
        if count_opp == 3 and count_empty == 1:
            return -80   # block opponent threat
        if count_opp == 2 and count_empty == 2:
            return -5
        return 0

    def _evaluate(self, board, disc):
        """
        Simple heuristic evaluation for `disc`.
        Higher scores indicate a more favorable position for `disc`.
        """
        score = 0

        # centre column preference
        centre_col = [board[r][self.COLS // 2] for r in range(self.ROWS)]
        centre_count = centre_col.count(disc)
        score += centre_count * 3

        # Horizontal
        for r in range(self.ROWS):
            row_array = board[r]
            for c in range(self.COLS - 3):
                window = row_array[c:c+4]
                score += self._window_score(window, disc)

        # Vertical
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r+4]
                score += self._window_score(window, disc)

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._window_score(window, disc)

        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._window_score(window, disc)

        return score

    # --------------------------------------------------------------------- #
    # Minimax with alpha‑beta pruning                                          #
    # --------------------------------------------------------------------- #

    def _minimax(self, board, depth, alpha, beta, maximizing):
        """
        Return a tuple (score, column).  If no moves are possible, column is None.
        """
        valid_cols = self._valid_columns(board)

        # Terminal test
        winner = self._winner(board)
        if winner == self.symbol:
            return (float('inf'), None)
        elif winner == self.opponent:
            return (float('-inf'), None)
        elif not valid_cols:
            return (0, None)  # draw

        if depth == 0:
            return (self._evaluate(board, self.symbol), None)

        if maximizing:
            value = -math.inf
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                child = self._drop(board, col, self.symbol)
                new_score, _ = self._minimax(child, depth - 1, alpha, beta, False)
                if new_score > value:
                    value, best_col = new_score, col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # beta cut‑off
            return (value, best_col)
        else:
            value = math.inf
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                child = self._drop(board, col, self.opponent)
                new_score, _ = self._minimax(child, depth - 1, alpha, beta, True)
                if new_score < value:
                    value, best_col = new_score, col
                beta = min(beta, value)
                if alpha >= beta:
                    break  # alpha cut‑off
            return (value, best_col)

    # --------------------------------------------------------------------- #
    # Public interface                                                       #
    # --------------------------------------------------------------------- #

    def make_move(self, board):
        """
        Choose a column (0‑6) for the next disc.
        The engine guarantees this method is called with a correct board
        representation and will enforce a 1 s CPU time limit.
        """
        start_time = time.time()

        # 1️⃣  Immediate win?
        for col in self._valid_columns(board):
            trial = self._drop(board, col, self.symbol)
            if self._winner(trial) == self.symbol:
                return col

        # 2️⃣  Block opponent's immediate win?
        for col in self._valid_columns(board):
            trial = self._drop(board, col, self.opponent)
            if self._winner(trial) == self.opponent:
                return col

        # 3️⃣  Minimax decision
        _, best = self._minimax(board, self.search_depth,
                               -math.inf, math.inf, True)

        # Fallback – should never happen, but keep engine safe
        if best is None:
            best = random.choice(self._valid_columns(board))

        # Ensure we respect the time budget (engine will replace invalid moves)
        if time.time() - start_time > 0.9:
            # Very close to timeout – pick a safe random column
            best = random.choice(self._valid_columns(board))

        return best
