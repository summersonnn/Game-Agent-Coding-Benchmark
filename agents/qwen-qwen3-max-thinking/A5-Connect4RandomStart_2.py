"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-max-thinking
Run: 2
Generated: 2026-02-13 14:10:12
"""

import random
import time

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'R' if symbol == 'Y' else 'Y'
        self.time_limit = 0.95

    def make_move(self, board):
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        if not valid_cols:
            return 0

        for col in valid_cols:
            if self._is_winning_move(board, col, self.symbol):
                return col

        for col in valid_cols:
            if self._is_winning_move(board, col, self.opponent):
                return col

        self.start_time = time.time()
        best_col = random.choice(valid_cols)
        max_depth = 5
        for depth in range(1, max_depth + 1):
            try:
                col, _ = self._minimax(board, depth, True, -float('inf'), float('inf'))
                if col is not None:
                    best_col = col
            except self.TimeoutException:
                break
            if time.time() - self.start_time > self.time_limit:
                break
        return best_col

    def _minimax(self, board, depth, maximizing, alpha, beta):
        if time.time() - self.start_time > self.time_limit:
            raise self.TimeoutException()

        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        winner = self._check_winner(board)
        if winner == self.symbol:
            return None, 1000000
        if winner == self.opponent:
            return None, -1000000
        if not valid_cols or depth == 0:
            return None, self._evaluate_board(board)

        col_order = [3, 2, 4, 1, 5, 0, 6]
        ordered_cols = [c for c in col_order if c in valid_cols]

        if maximizing:
            max_eval = -float('inf')
            best_col = ordered_cols[0] if ordered_cols else random.choice(valid_cols)
            for col in ordered_cols:
                new_board = self._drop_disc(board, col, self.symbol)
                _, eval_score = self._minimax(new_board, depth - 1, False, alpha, beta)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return best_col, max_eval
        else:
            min_eval = float('inf')
            best_col = ordered_cols[0] if ordered_cols else random.choice(valid_cols)
            for col in ordered_cols:
                new_board = self._drop_disc(board, col, self.opponent)
                _, eval_score = self._minimax(new_board, depth - 1, True, alpha, beta)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return best_col, min_eval

    def _drop_disc(self, board, col, disc):
        new_board = [row[:] for row in board]
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = disc
                break
        return new_board

    def _check_winner(self, board):
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        return None

    def _is_winning_move(self, board, col, disc):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = disc
                win = self._check_winner(board) == disc
                board[r][col] = ' '
                return win
        return False

    def _evaluate_board(self, board):
        score = 0
        center_col = [board[r][3] for r in range(6)]
        score += center_col.count(self.symbol) * 3
        score -= center_col.count(self.opponent) * 3

        for r in range(6):
            row = board[r]
            for c in range(4):
                window = row[c:c+4]
                score += self._score_window(window)
        for c in range(7):
            col = [board[r][c] for r in range(6)]
            for r in range(3):
                window = col[r:r+4]
                score += self._score_window(window)
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._score_window(window)
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._score_window(window)
        return score

    def _score_window(self, window):
        my = window.count(self.symbol)
        opp = window.count(self.opponent)
        empty = window.count(' ')
        score = 0
        if my == 4:
            score += 100000
        elif my == 3 and empty == 1:
            score += 50
        elif my == 2 and empty == 2:
            score += 10
        elif my == 1 and empty == 3:
            score += 1
        if opp == 4:
            score -= 100000
        elif opp == 3 and empty == 1:
            score -= 55
        elif opp == 2 and empty == 2:
            score -= 12
        elif opp == 1 and empty == 3:
            score -= 1
        return score