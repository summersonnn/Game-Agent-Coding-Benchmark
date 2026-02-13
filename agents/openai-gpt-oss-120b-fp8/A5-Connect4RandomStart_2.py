"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-13 22:26:38
"""

import math
from copy import deepcopy

import math
import random
from copy import deepcopy

class Connect4Agent:
    """
    Simple but strong Connect‑4 agent.

    Strategy (in order of priority):
        1. Win immediately if possible.
        2. Block opponent's immediate win.
        3. Look ahead a few plies with a minimax search (alpha‑beta) using a
           lightweight board‑evaluation function.
        4. Prefer centre columns when all else is equal.
    """

    ROWS = 6
    COLS = 7
    EMPTY = ' '

    def __init__(self, name: str, symbol: str):
        """
        name   – arbitrary identifier (not used by the agent)
        symbol – 'R' or 'Y' – the colour this agent plays
        """
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'

        # ordering of columns for tie‑breaks (centre‑first)
        self.column_order = [3, 2, 4, 1, 5, 0, 6]

    # ------------------------------------------------------------------ #
    # Helper utilities
    # ------------------------------------------------------------------ #
    def _valid_moves(self, board):
        """Return list of columns that are not full."""
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    def _drop(self, board, col, disc):
        """
        Drop a disc in *board* (modified in‑place) and return the row index
        where it landed, or None if the column is full.
        """
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                board[r][col] = disc
                return r
        return None

    def _undo(self, board, col, row):
        """Remove a disc placed at (row, col)."""
        board[row][col] = self.EMPTY

    def _is_winning_move(self, board, row, col, disc):
        """Check whether placing *disc* at (row,col) creates a connect‑4."""
        def count(delta_r, delta_c):
            cnt = 0
            r, c = row + delta_r, col + delta_c
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and board[r][c] == disc:
                cnt += 1
                r += delta_r
                c += delta_c
            return cnt

        # four directions
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            total = 1 + count(dr, dc) + count(-dr, -dc)
            if total >= 4:
                return True
        return False

    # ------------------------------------------------------------------ #
    # Evaluation
    # ------------------------------------------------------------------ #
    def _evaluate_window(self, window, player):
        """
        Score a list of 4 cells (a "window").
        Positive scores favour *player*, negative scores favour the opponent.
        """
        opp = self.opponent if player == self.symbol else self.symbol
        score = 0
        player_count = window.count(player)
        opp_count = window.count(opp)
        empty_count = window.count(self.EMPTY)

        if player_count == 4:
            score += 100000
        elif player_count == 3 and empty_count == 1:
            score += 100
        elif player_count == 2 and empty_count == 2:
            score += 10

        if opp_count == 4:
            score -= 100000
        elif opp_count == 3 and empty_count == 1:
            score -= 120   # block opponent's three‑in‑a‑row
        elif opp_count == 2 and empty_count == 2:
            score -= 8

        return score

    def _score_position(self, board, player):
        """Simple heuristic – sum of window scores."""
        score = 0

        # centre column preference (more possibilities)
        centre = [board[r][self.COLS // 2] for r in range(self.ROWS)]
        centre_count = centre.count(player)
        score += centre_count * 6

        # Horizontal windows
        for r in range(self.ROWS):
            row_array = board[r]
            for c in range(self.COLS - 3):
                window = row_array[c:c + 4]
                score += self._evaluate_window(window, player)

        # Vertical windows
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r + 4]
                score += self._evaluate_window(window, player)

        # Positive diagonal windows
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += self._evaluate_window(window, player)

        # Negative diagonal windows
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += self._evaluate_window(window, player)

        return score

    # ------------------------------------------------------------------ #
    # Minimax with alpha‑beta pruning
    # ------------------------------------------------------------------ #
    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        """
        Returns (best_score, best_column).  Column may be None when no move
        is possible (should only happen on a full board).
        """
        valid_cols = self._valid_moves(board)

        # terminal node (win/loss/draw) or depth limit
        if depth == 0 or not valid_cols:
            return self._score_position(board, self.symbol), None

        if maximizing_player:
            value = -math.inf
            best_col = random.choice(valid_cols)  # fallback
            for col in valid_cols:
                row = self._drop(board, col, self.symbol)
                if row is None:      # should not happen – column was valid
                    continue
                if self._is_winning_move(board, row, col, self.symbol):
                    self._undo(board, col, row)
                    return 1000000, col   # immediate win
                new_score, _ = self._minimax(board, depth - 1, alpha, beta, False)
                self._undo(board, col, row)

                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_col
        else:
            value = math.inf
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                row = self._drop(board, col, self.opponent)
                if row is None:
                    continue
                if self._is_winning_move(board, row, col, self.opponent):
                    self._undo(board, col, row)
                    return -1000000, col   # opponent can win
                new_score, _ = self._minimax(board, depth - 1, alpha, beta, True)
                self._undo(board, col, row)

                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, best_col

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def make_move(self, board):
        """
        Decide the next column (0‑6) for the current board.
        The engine supplies a *copy* of the board, so we may modify it safely.
        """
        # 1️⃣  Immediate win ?
        for col in self._valid_moves(board):
            row = self._drop(board, col, self.symbol)
            if row is not None and self._is_winning_move(board, row, col, self.symbol):
                self._undo(board, col, row)
                return col
            self._undo(board, col, row)

        # 2️⃣  Block opponent's immediate win ?
        for col in self._valid_moves(board):
            row = self._drop(board, col, self.opponent)
            if row is not None and self._is_winning_move(board, row, col, self.opponent):
                self._undo(board, col, row)
                return col
            self._undo(board, col, row)

        # 3️⃣  Mini‑max search (depth 4 works well within 1 s)
        _, best_col = self._minimax(board, depth=4,
                                    alpha=-math.inf,
                                    beta=math.inf,
                                    maximizing_player=True)

        # 4️⃣  Fallback – centre‑first ordering
        if best_col is None or best_col not in self._valid_moves(board):
            for col in self.column_order:
                if col in self._valid_moves(board):
                    best_col = col
                    break

        # The engine will treat any non‑int or out‑of‑range as invalid,
        # so we guarantee an int in range.
        return best_col if best_col is not None else random.choice(self._valid_moves(board))
