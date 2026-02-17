"""
Agent Code: A5-Connect4RandomStart
Model: anthropic-claude-opus-4.6
Run: 2
Generated: 2026-02-12 14:50:42
"""

import time

class Connect4Agent:
    ROWS = 6
    COLS = 7

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opp = 'Y' if symbol == 'R' else 'R'
        self.tt = {}

    def _board_key(self, board):
        return tuple(board[r][c] for r in range(self.ROWS) for c in range(self.COLS))

    def make_move(self, board):
        valid = [c for c in range(self.COLS) if board[0][c] == ' ']
        if not valid:
            return 0

        for c in valid:
            r = self._drop(board, c, self.symbol)
            if r is not None and self._is_win(board, r, c, self.symbol):
                board[r][c] = ' '
                return c
            if r is not None:
                board[r][c] = ' '

        for c in valid:
            r = self._drop(board, c, self.opp)
            if r is not None and self._is_win(board, r, c, self.opp):
                board[r][c] = ' '
                return c
            if r is not None:
                board[r][c] = ' '

        self.start_time = time.time()
        self.time_limit = 0.85
        self.tt.clear()
        best_col = valid[len(valid) // 2]
        order = self._move_order(valid)

        for depth in range(1, 30):
            try:
                best_score = -float('inf')
                best_c = order[0]
                scores = []
                for c in order:
                    r = self._drop(board, c, self.symbol)
                    if r is None:
                        continue
                    score = -self._negamax(board, depth - 1, -float('inf'), -best_score, self.opp)
                    board[r][c] = ' '
                    scores.append((score, c))
                    if score > best_score:
                        best_score = score
                        best_c = c
                best_col = best_c
                order = [c for _, c in sorted(scores, reverse=True)]
                if best_score > 100000:
                    break
            except TimeoutError:
                break

        return best_col

    def _negamax(self, board, depth, alpha, beta, symbol):
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError

        alpha_orig = alpha
        key = (self._board_key(board), symbol)
        if key in self.tt:
            td, ts, tf = self.tt[key]
            if td >= depth:
                if tf == 0:
                    return ts
                elif tf == 1:
                    alpha = max(alpha, ts)
                elif tf == 2:
                    beta = min(beta, ts)
                if alpha >= beta:
                    return ts

        opp = 'Y' if symbol == 'R' else 'R'
        valid = [c for c in range(self.COLS) if board[0][c] == ' ']
        if not valid:
            return 0
        if depth == 0:
            return self._evaluate(board, symbol)

        order = self._move_order(valid)
        best = -float('inf')
        for c in order:
            r = self._drop(board, c, symbol)
            if r is None:
                continue
            if self._is_win(board, r, c, symbol):
                board[r][c] = ' '
                return 1000000 + depth
            score = -self._negamax(board, depth - 1, -beta, -alpha, opp)
            board[r][c] = ' '
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        if best <= alpha_orig:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, best, flag)
        return best

    def _drop(self, board, col, symbol):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return r
        return None

    def _is_win(self, board, r, c, symbol):
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in dirs:
            count = 1
            for d in (1, -1):
                nr, nc = r + dr * d, c + dc * d
                while 0 <= nr < self.ROWS and 0 <= nc < self.COLS and board[nr][nc] == symbol:
                    count += 1
                    nr += dr * d
                    nc += dc * d
            if count >= 4:
                return True
        return False

    def _move_order(self, valid):
        center = self.COLS // 2
        return sorted(valid, key=lambda c: abs(c - center))

    def _evaluate(self, board, symbol):
        opp = 'Y' if symbol == 'R' else 'R'
        score = 0
        for r in range(self.ROWS):
            for c in range(self.COLS):
                for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    er, ec = r + 3 * dr, c + 3 * dc
                    if not (0 <= er < self.ROWS and 0 <= ec < self.COLS):
                        continue
                    w = [board[r + i * dr][c + i * dc] for i in range(4)]
                    sc = w.count(symbol)
                    oc = w.count(opp)
                    if sc > 0 and oc == 0:
                        score += (1, 10, 50, 1000000)[sc - 1]
                    elif oc > 0 and sc == 0:
                        score -= (1, 10, 50, 1000000)[oc - 1]

        for c in range(self.COLS):
            for r in range(self.ROWS):
                if board[r][c] == symbol:
                    score += 3 - abs(c - 3)
                elif board[r][c] == opp:
                    score -= 3 - abs(c - 3)
        return score