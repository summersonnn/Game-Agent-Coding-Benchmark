"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-12 15:02:53
"""

import time
import math

import time
import math

class Connect4Agent:
    ROWS = 6
    COLS = 7
    EMPTY = ' '

    # Search / scoring constants
    WIN_SCORE = 1_000_000
    MOVE_ORDER = (3, 2, 4, 1, 5, 0, 6)  # center-first

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'R' or 'Y'
        self.opp = 'Y' if symbol == 'R' else 'R'

        # Tune these if needed
        self.time_limit = 0.95   # seconds (keep under 1s)
        self.max_depth = 8       # iterative deepening up to this

        # Transposition table (rebuilt each move)
        self.tt = {}

    def make_move(self, board):
        start = time.perf_counter()
        self.tt = {}

        # Work on a mutable copy
        b = [row[:] for row in board]
        heights = self._compute_heights(b)
        valid = self._valid_moves_from_heights(heights)
        if not valid:
            return 0  # should never happen, but keep safe

        # 1) Immediate win
        for c in self._ordered(valid):
            r = heights[c]
            self._do_move(b, heights, r, c, self.symbol)
            won = self._is_win_from(b, r, c, self.symbol)
            self._undo_move(b, heights, r, c)
            if won:
                return c

        # 2) Immediate block (opponent win next)
        for c in self._ordered(valid):
            r = heights[c]
            self._do_move(b, heights, r, c, self.opp)
            opp_wins = self._is_win_from(b, r, c, self.opp)
            self._undo_move(b, heights, r, c)
            if opp_wins:
                return c

        # 3) Iterative deepening minimax
        best_move = self._pick_centerish(valid)
        best_score = -math.inf

        for depth in range(1, self.max_depth + 1):
            if time.perf_counter() - start > self.time_limit:
                break

            move, score = self._search_root(b, heights, depth, start)
            if move is not None:
                best_move, best_score = move, score

        # Always return a valid move
        if best_move not in valid:
            best_move = self._pick_centerish(valid)
        return best_move

    # ---------------- Search ----------------

    def _search_root(self, b, heights, depth, start):
        valid = self._valid_moves_from_heights(heights)
        if not valid:
            return None, 0

        alpha, beta = -math.inf, math.inf
        best_move = None
        best_score = -math.inf

        for c in self._ordered(valid):
            if time.perf_counter() - start > self.time_limit:
                break

            r = heights[c]
            self._do_move(b, heights, r, c, self.symbol)

            if self._is_win_from(b, r, c, self.symbol):
                score = self.WIN_SCORE + depth  # faster wins preferred
            else:
                score = self._minimax(
                    b, heights, depth - 1, alpha, beta,
                    maximizing=False, start=start
                )

            self._undo_move(b, heights, r, c)

            if score > best_score:
                best_score = score
                best_move = c

            alpha = max(alpha, best_score)
            if alpha >= beta:
                break

        return best_move, best_score

    def _minimax(self, b, heights, depth, alpha, beta, maximizing, start):
        # Time cutoff: return static evaluation immediately (safe, no exceptions)
        if time.perf_counter() - start > self.time_limit:
            return self._evaluate(b)

        valid = self._valid_moves_from_heights(heights)
        if depth == 0 or not valid:
            return self._evaluate(b)

        # Transposition table (cheap base-3 encoding)
        key = (self._board_key(b), depth, maximizing)
        if key in self.tt:
            return self.tt[key]

        if maximizing:
            best = -math.inf
            for c in self._ordered(valid):
                r = heights[c]
                self._do_move(b, heights, r, c, self.symbol)

                if self._is_win_from(b, r, c, self.symbol):
                    score = self.WIN_SCORE + depth
                else:
                    score = self._minimax(b, heights, depth - 1, alpha, beta, False, start)

                self._undo_move(b, heights, r, c)

                best = max(best, score)
                alpha = max(alpha, best)
                if alpha >= beta:
                    break

        else:
            best = math.inf
            for c in self._ordered(valid):
                r = heights[c]
                self._do_move(b, heights, r, c, self.opp)

                if self._is_win_from(b, r, c, self.opp):
                    score = -(self.WIN_SCORE + depth)
                else:
                    score = self._minimax(b, heights, depth - 1, alpha, beta, True, start)

                self._undo_move(b, heights, r, c)

                best = min(best, score)
                beta = min(beta, best)
                if alpha >= beta:
                    break

        self.tt[key] = best
        return best

    # ---------------- Heuristics ----------------

    def _evaluate(self, b):
        """
        Heuristic score from self.symbol's perspective.
        """
        me = self.symbol
        opp = self.opp

        score = 0

        # Center preference
        center_col = 3
        center_count = sum(1 for r in range(self.ROWS) if b[r][center_col] == me)
        score += center_count * 6

        # Score all 4-cell windows
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                score += self._score_window([b[r][c+i] for i in range(4)], me, opp)
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                score += self._score_window([b[r+i][c] for i in range(4)], me, opp)
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                score += self._score_window([b[r+i][c+i] for i in range(4)], me, opp)
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                score += self._score_window([b[r-i][c+i] for i in range(4)], me, opp)

        return score

    def _score_window(self, window, me, opp):
        me_ct = window.count(me)
        opp_ct = window.count(opp)
        empty_ct = window.count(self.EMPTY)

        if me_ct == 4:
            return 100_000
        if opp_ct == 4:
            return -100_000

        # Build threats
        if me_ct == 3 and empty_ct == 1:
            return 80
        if me_ct == 2 and empty_ct == 2:
            return 12

        # Prevent opponent threats (weighted a bit higher than building)
        if opp_ct == 3 and empty_ct == 1:
            return -100
        if opp_ct == 2 and empty_ct == 2:
            return -14

        return 0

    # ---------------- Board utilities ----------------

    def _compute_heights(self, b):
        # heights[c] = next open row index (0..5), or -1 if column full
        heights = [-1] * self.COLS
        for c in range(self.COLS):
            rr = -1
            for r in range(self.ROWS - 1, -1, -1):
                if b[r][c] == self.EMPTY:
                    rr = r
                    break
            heights[c] = rr
        return heights

    def _valid_moves_from_heights(self, heights):
        return [c for c in range(self.COLS) if heights[c] >= 0]

    def _do_move(self, b, heights, r, c, sym):
        b[r][c] = sym
        heights[c] -= 1  # next open row moves up (or becomes -1)

    def _undo_move(self, b, heights, r, c):
        b[r][c] = self.EMPTY
        heights[c] += 1

    def _ordered(self, valid_moves):
        s = set(valid_moves)
        return [c for c in self.MOVE_ORDER if c in s]

    def _pick_centerish(self, valid_moves):
        # pick closest to center
        return min(valid_moves, key=lambda c: (abs(3 - c), c))

    def _is_win_from(self, b, r, c, sym):
        # Check 4 directions crossing (r,c)
        return (self._count_dir(b, r, c, sym, 0, 1) + self._count_dir(b, r, c, sym, 0, -1) - 1 >= 4 or
                self._count_dir(b, r, c, sym, 1, 0) + self._count_dir(b, r, c, sym, -1, 0) - 1 >= 4 or
                self._count_dir(b, r, c, sym, 1, 1) + self._count_dir(b, r, c, sym, -1, -1) - 1 >= 4 or
                self._count_dir(b, r, c, sym, 1, -1) + self._count_dir(b, r, c, sym, -1, 1) - 1 >= 4)

    def _count_dir(self, b, r, c, sym, dr, dc):
        cnt = 0
        rr, cc = r, c
        while 0 <= rr < self.ROWS and 0 <= cc < self.COLS and b[rr][cc] == sym:
            cnt += 1
            rr += dr
            cc += dc
        return cnt

    def _board_key(self, b):
        # Base-3 encoding of the 42 cells: ' '->0, 'R'->1, 'Y'->2
        vmap = {self.EMPTY: 0, 'R': 1, 'Y': 2}
        key = 0
        for r in range(self.ROWS):
            row = b[r]
            for c in range(self.COLS):
                key = key * 3 + vmap[row[c]]
        return key
