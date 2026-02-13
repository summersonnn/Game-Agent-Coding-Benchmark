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
        self.opponent = 'Y' if symbol == 'R' else 'R'

    def make_move(self, board):
        self.start_time = time.time()
        self.timed_out = False

        valid = [c for c in range(self.COLS) if board[0][c] == ' ']
        if not valid:
            return 0

        for c in valid:
            r = self._drop(board, c, self.symbol)
            if r is not None and self._is_winning(board, r, c, self.symbol):
                board[r][c] = ' '
                return c
            if r is not None:
                board[r][c] = ' '

        for c in valid:
            r = self._drop(board, c, self.opponent)
            if r is not None and self._is_winning(board, r, c, self.opponent):
                board[r][c] = ' '
                return c
            if r is not None:
                board[r][c] = ' '

        best_move = valid[len(valid) // 2]
        order = sorted(valid, key=lambda c: abs(c - 3))

        for depth in range(1, 43):
            if time.time() - self.start_time > 0.85:
                break
            try:
                best_score = -float('inf')
                for c in order:
                    r = self._drop(board, c, self.symbol)
                    if r is None:
                        continue
                    score = -self._negamax(board, depth - 1, -float('inf'), float('inf'), self.opponent)
                    board[r][c] = ' '
                    if self.timed_out:
                        raise TimeoutError
                    if score > best_score:
                        best_score = score
                        best_move = c
            except TimeoutError:
                break

        return best_move

    def _drop(self, board, col, symbol):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return r
        return None

    def _is_winning(self, board, row, col, symbol):
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in dirs:
            count = 1
            for d in (1, -1):
                r, c = row + dr * d, col + dc * d
                while 0 <= r < self.ROWS and 0 <= c < self.COLS and board[r][c] == symbol:
                    count += 1
                    r += dr * d
                    c += dc * d
            if count >= 4:
                return True
        return False

    def _negamax(self, board, depth, alpha, beta, symbol):
        if time.time() - self.start_time > 0.85:
            self.timed_out = True
            return 0

        opp = 'Y' if symbol == 'R' else 'R'
        valid = [c for c in range(self.COLS) if board[0][c] == ' ']

        if not valid:
            return 0

        if depth == 0:
            return self._evaluate(board, symbol)

        order = sorted(valid, key=lambda c: abs(c - 3))
        best = -float('inf')

        for c in order:
            r = self._drop(board, c, symbol)
            if r is None:
                continue
            if self._is_winning(board, r, c, symbol):
                board[r][c] = ' '
                return 10000 + depth
            score = -self._negamax(board, depth - 1, -beta, -alpha, opp)
            board[r][c] = ' '
            if self.timed_out:
                return 0
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best

    def _evaluate(self, board, symbol):
        opp = 'Y' if symbol == 'R' else 'R'
        score = 0

        for c in range(self.COLS):
            for r in range(self.ROWS):
                if board[r][c] == ' ':
                    continue
                if board[r][c] == symbol:
                    score += self._cell_score(board, r, c, symbol)
                else:
                    score -= self._cell_score(board, r, c, opp)

        for c in range(self.COLS):
            for r in range(self.ROWS):
                if board[r][c] == symbol:
                    score += [0, 1, 2, 4, 4, 2, 1, 0][c]
                elif board[r][c] == opp:
                    score -= [0, 1, 2, 4, 4, 2, 1, 0][c]

        return score

    def _cell_score(self, board, row, col, symbol):
        score = 0
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in dirs:
            count = 0
            empty = 0
            for i in range(4):
                r, c = row + dr * i, col + dc * i
                if not (0 <= r < self.ROWS and 0 <= c < self.COLS):
                    break
                if board[r][c] == symbol:
                    count += 1
                elif board[r][c] == ' ':
                    empty += 1
                else:
                    break
            else:
                if count == 3 and empty == 1:
                    score += 50
                elif count == 2 and empty == 2:
                    score += 10
        return score