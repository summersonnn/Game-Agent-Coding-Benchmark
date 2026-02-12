"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-12 15:02:53
"""

import time
import math

import time
import math
import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'R' or 'Y'
        self.ROWS = 6
        self.COLS = 7
        self.EMPTY = ' '
        self.WIN_SCORE = 1_000_000

        # Move ordering: center-first is usually best in Connect4
        self.order = [3, 2, 4, 1, 5, 0, 6]

    def make_move(self, board):
        self.deadline = time.perf_counter() + 0.95  # stay under 1s hard limit
        me = self.symbol
        opp = 'Y' if me == 'R' else 'R'

        valid_moves = self._valid_moves(board)
        if not valid_moves:
            return 0  # should not happen, but must return an int

        # Safe fallback (ensures we never forfeit due to invalid move)
        fallback = self._best_centerish(valid_moves)

        # 1) If we can win now, do it.
        for c in self._ordered(valid_moves):
            r = self._next_row(board, c)
            self._place(board, r, c, me)
            if self._check_winner(board) == me:
                self._unplace(board, r, c)
                return c
            self._unplace(board, r, c)

        # 2) If opponent can win next, block it.
        for c in self._ordered(valid_moves):
            r = self._next_row(board, c)
            self._place(board, r, c, opp)
            if self._check_winner(board) == opp:
                self._unplace(board, r, c)
                return c
            self._unplace(board, r, c)

        # 3) Iterative deepening search
        best_move = fallback
        best_score = -math.inf

        # Simple transposition table: (key, depth, player)->score
        # (kept per-move so it doesn't grow without bound)
        self.tt = {}

        depth = 1
        while True:
            if time.perf_counter() >= self.deadline:
                break

            score, move = self._negamax_root(board, depth, me)
            if time.perf_counter() >= self.deadline:
                break

            if move is not None:
                best_move, best_score = move, score

            # If we found a forced win, stop early
            if best_score >= self.WIN_SCORE - 1000:
                break

            depth += 1
            # Practical cap (keeps node counts sane)
            if depth > 10:
                break

        # Always return a valid move
        if best_move not in valid_moves:
            return fallback
        return best_move

    # ---------- Search (Negamax + alpha-beta) ----------

    def _negamax_root(self, board, depth, player):
        alpha = -math.inf
        beta = math.inf
        best_score = -math.inf
        best_move = None

        valid_moves = self._valid_moves(board)
        if not valid_moves:
            return 0, None

        for c in self._ordered(valid_moves):
            if time.perf_counter() >= self.deadline:
                break
            r = self._next_row(board, c)
            self._place(board, r, c, player)
            score = -self._negamax(board, depth - 1, -beta, -alpha, self._other(player))
            self._unplace(board, r, c)

            if score > best_score:
                best_score = score
                best_move = c
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score, best_move

    def _negamax(self, board, depth, alpha, beta, player):
        if time.perf_counter() >= self.deadline:
            # If out of time, return heuristic immediately
            return self._evaluate(board)

        winner = self._check_winner(board)
        if winner is not None:
            if winner == self.symbol:
                return self.WIN_SCORE + depth  # quicker win slightly better
            else:
                return -self.WIN_SCORE - depth  # quicker loss slightly worse

        if self._is_full(board):
            return 0

        if depth <= 0:
            return self._evaluate(board)

        key = self._board_key(board)
        tt_key = (key, depth, player)
        if tt_key in self.tt:
            return self.tt[tt_key]

        best = -math.inf
        valid_moves = self._valid_moves(board)
        if not valid_moves:
            return 0

        for c in self._ordered(valid_moves):
            if time.perf_counter() >= self.deadline:
                break
            r = self._next_row(board, c)
            self._place(board, r, c, player)
            score = -self._negamax(board, depth - 1, -beta, -alpha, self._other(player))
            self._unplace(board, r, c)

            if score > best:
                best = score
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        self.tt[tt_key] = best
        return best

    # ---------- Heuristic ----------

    def _evaluate(self, board):
        me = self.symbol
        opp = self._other(me)

        score = 0

        # Center column preference
        center_col = 3
        center_count = sum(1 for r in range(self.ROWS) if board[r][center_col] == me)
        score += center_count * 6

        # Score all 4-cell windows
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._score_window(window, me, opp)

        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                window = [board[r+i][c] for i in range(4)]
                score += self._score_window(window, me, opp)

        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._score_window(window, me, opp)

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._score_window(window, me, opp)

        return score

    def _score_window(self, window, me, opp):
        m = window.count(me)
        o = window.count(opp)
        e = window.count(self.EMPTY)

        if o > 0 and m > 0:
            return 0  # mixed window has little direct value

        if m == 4:
            return 100000
        if m == 3 and e == 1:
            return 80
        if m == 2 and e == 2:
            return 10

        if o == 4:
            return -100000
        if o == 3 and e == 1:
            return -90
        if o == 2 and e == 2:
            return -12

        return 0

    # ---------- Board helpers ----------

    def _valid_moves(self, board):
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    def _ordered(self, valid_moves):
        s = set(valid_moves)
        return [c for c in self.order if c in s]

    def _best_centerish(self, valid_moves):
        # Pick the valid move closest to center (3), break ties consistently
        return min(valid_moves, key=lambda c: (abs(c - 3), c))

    def _next_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return None  # column full

    def _place(self, board, r, c, sym):
        board[r][c] = sym

    def _unplace(self, board, r, c):
        board[r][c] = self.EMPTY

    def _other(self, sym):
        return 'Y' if sym == 'R' else 'R'

    def _is_full(self, board):
        return all(board[0][c] != self.EMPTY for c in range(self.COLS))

    def _board_key(self, board):
        # 42-char string key (fast enough for a small TT)
        return ''.join(''.join(row) for row in board)

    def _check_winner(self, board):
        E = self.EMPTY
        R = self.ROWS
        C = self.COLS

        # Horizontal
        for r in range(R):
            row = board[r]
            for c in range(C - 3):
                v = row[c]
                if v != E and v == row[c+1] == row[c+2] == row[c+3]:
                    return v

        # Vertical
        for r in range(R - 3):
            for c in range(C):
                v = board[r][c]
                if v != E and v == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return v

        # Diagonal \
        for r in range(R - 3):
            for c in range(C - 3):
                v = board[r][c]
                if v != E and v == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return v

        # Diagonal /
        for r in range(3, R):
            for c in range(C - 3):
                v = board[r][c]
                if v != E and v == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return v

        return None
