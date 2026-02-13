"""
Agent Code: A5-Connect4RandomStart
Model: anthropic-claude-opus-4.6
Run: 1
Generated: 2026-02-12 14:50:42
"""


import time
import random

class Connect4Agent:
    ROWS = 6
    COLS = 7
    EMPTY = ' '

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.move_order = [3, 2, 4, 1, 5, 0, 6]
        self.time_limit = 0.85
        self.transposition_table = {}

    def make_move(self, board):
        self.start_time = time.time()
        self.transposition_table.clear()

        valid = self._valid_moves(board)
        if not valid:
            return 0

        for col in valid:
            r = self._drop(board, col, self.symbol)
            if r is not None and self._is_winner(board, r, col, self.symbol):
                board[r][col] = self.EMPTY
                return col
            if r is not None:
                board[r][col] = self.EMPTY

        for col in valid:
            r = self._drop(board, col, self.opponent)
            if r is not None and self._is_winner(board, r, col, self.opponent):
                board[r][col] = self.EMPTY
                return col
            if r is not None:
                board[r][col] = self.EMPTY

        best_move = valid[0]
        best_score = float('-inf')

        for depth in range(4, 30):
            if time.time() - self.start_time > self.time_limit * 0.5:
                break
            try:
                current_best = None
                current_score = float('-inf')
                alpha = float('-inf')
                beta = float('inf')
                for col in self._ordered_moves(valid, board):
                    r = self._drop(board, col, self.symbol)
                    if r is None:
                        continue
                    score = -self._negamax(board, depth - 1, -beta, -alpha, self.opponent)
                    board[r][col] = self.EMPTY
                    if score > current_score:
                        current_score = score
                        current_best = col
                    alpha = max(alpha, score)
                if current_best is not None:
                    best_move = current_best
                    best_score = current_score
                if best_score > 100000:
                    break
            except TimeoutError:
                break

        return best_move

    def _negamax(self, board, depth, alpha, beta, symbol):
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError

        board_key = self._hash(board, symbol)
        if board_key in self.transposition_table:
            entry = self.transposition_table[board_key]
            if entry[0] >= depth:
                if entry[1] == 'exact':
                    return entry[2]
                elif entry[1] == 'lower' and entry[2] >= beta:
                    return entry[2]
                elif entry[1] == 'upper' and entry[2] <= alpha:
                    return entry[2]

        opponent = 'Y' if symbol == 'R' else 'R'
        valid = self._valid_moves(board)

        if not valid:
            return 0

        if depth == 0:
            score = self._evaluate(board, symbol)
            return score

        orig_alpha = alpha
        best_score = float('-inf')

        for col in self._ordered_moves(valid, board):
            r = self._drop(board, col, symbol)
            if r is None:
                continue

            if self._is_winner(board, r, col, symbol):
                board[r][col] = self.EMPTY
                best_score = 1000000 + depth
                break

            score = -self._negamax(board, depth - 1, -beta, -alpha, opponent)
            board[r][col] = self.EMPTY

            if score > best_score:
                best_score = score
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        if best_score <= orig_alpha:
            flag = 'upper'
        elif best_score >= beta:
            flag = 'lower'
        else:
            flag = 'exact'
        self.transposition_table[board_key] = (depth, flag, best_score)

        return best_score

    def _hash(self, board, symbol):
        flat = []
        for row in board:
            flat.extend(row)
        flat.append(symbol)
        return tuple(flat)

    def _valid_moves(self, board):
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    def _ordered_moves(self, valid, board):
        scores = []
        for c in valid:
            s = 0
            s += (3 - abs(c - 3)) * 4
            r = self._get_drop_row(board, c)
            if r is not None:
                if r > 0 and board[r-1][c] != self.EMPTY:
                    s -= 2
            scores.append((s, c))
        scores.sort(reverse=True)
        return [c for _, c in scores]

    def _drop(self, board, col, disc):
        if not (0 <= col < self.COLS):
            return None
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                board[r][col] = disc
                return r
        return None

    def _get_drop_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return None

    def _is_winner(self, board, r, c, symbol):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
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

    def _evaluate(self, board, symbol):
        opponent = 'Y' if symbol == 'R' else 'R'
        score = 0

        for c in range(self.COLS):
            for r in range(self.ROWS):
                if board[r][c] == symbol:
                    score += (3 - abs(c - 3))
                elif board[r][c] == opponent:
                    score -= (3 - abs(c - 3))

        score += self._count_threats(board, symbol, opponent)
        return score

    def _count_threats(self, board, symbol, opponent):
        score = 0
        lines = []

        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                lines.append([(r, c+i) for i in range(4)])
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                lines.append([(r+i, c) for i in range(4)])
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                lines.append([(r-i, c+i) for i in range(4)])
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                lines.append([(r+i, c+i) for i in range(4)])

        for line in lines:
            cells = [board[r][c] for r, c in line]
            mine = cells.count(symbol)
            theirs = cells.count(opponent)

            if theirs == 0:
                if mine == 3:
                    score += 50
                elif mine == 2:
                    score += 10
            if mine == 0:
                if theirs == 3:
                    score -= 80
                elif theirs == 2:
                    score -= 10

        return score