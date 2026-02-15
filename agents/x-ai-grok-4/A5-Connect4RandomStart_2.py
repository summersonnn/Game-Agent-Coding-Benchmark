"""
Agent Code: A5-Connect4RandomStart
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-14 19:46:39
"""

import time

import time

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        opponent = 'Y' if self.symbol == 'R' else 'R'
        ROWS = 6
        COLS = 7
        EMPTY = ' '
        INF = 1000000

        filled = [0 for _ in range(COLS)]
        for c in range(COLS):
            for r in range(ROWS):
                if board[r][c] != EMPTY:
                    filled[c] += 1

        valid_cols = [c for c in range(COLS) if filled[c] < 6]
        if not valid_cols:
            return 0  # Should not happen
        if len(valid_cols) == 1:
            return valid_cols[0]

        def check_winner(board):
            # Horizontal
            for r in range(ROWS):
                for c in range(COLS - 3):
                    if board[r][c] != EMPTY and \
                       board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                        return board[r][c]
            # Vertical
            for r in range(ROWS - 3):
                for c in range(COLS):
                    if board[r][c] != EMPTY and \
                       board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                        return board[r][c]
            # Diagonal /
            for r in range(3, ROWS):
                for c in range(COLS - 3):
                    if board[r][c] != EMPTY and \
                       board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                        return board[r][c]
            # Diagonal \
            for r in range(ROWS - 3):
                for c in range(COLS - 3):
                    if board[r][c] != EMPTY and \
                       board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                        return board[r][c]
            return None

        def evaluate(board, my_symbol, opp_symbol):
            score = 0
            # Horizontal
            for r in range(ROWS):
                for c in range(COLS - 3):
                    window = [board[r][c + i] for i in range(4)]
                    score += score_window(window, my_symbol, opp_symbol)
            # Vertical
            for r in range(ROWS - 3):
                for c in range(COLS):
                    window = [board[r + i][c] for i in range(4)]
                    score += score_window(window, my_symbol, opp_symbol)
            # Diagonal /
            for r in range(3, ROWS):
                for c in range(COLS - 3):
                    window = [board[r - i][c + i] for i in range(4)]
                    score += score_window(window, my_symbol, opp_symbol)
            # Diagonal \
            for r in range(ROWS - 3):
                for c in range(COLS - 3):
                    window = [board[r + i][c + i] for i in range(4)]
                    score += score_window(window, my_symbol, opp_symbol)
            return score

        def score_window(window, my, opp):
            count_my = window.count(my)
            count_opp = window.count(opp)
            count_empty = window.count(EMPTY)
            score = 0
            if count_my == 3 and count_empty == 1:
                score += 100
            elif count_my == 2 and count_empty == 2:
                score += 10
            elif count_my == 1 and count_empty == 3:
                score += 1
            if count_opp == 3 and count_empty == 1:
                score -= 1000
            elif count_opp == 2 and count_empty == 2:
                score -= 10
            return score

        def alpha_beta(board, filled, depth, alpha, beta, maximizing):
            win = check_winner(board)
            if win:
                empty = 42 - sum(filled)
                if win == self.symbol:
                    return INF + max(empty, 3)
                else:
                    return -INF - max(empty, 3)
            if all(filled[c] == 6 for c in range(COLS)):
                return 0
            if depth == 0:
                return evaluate(board, self.symbol, opponent)

            if maximizing:
                value = -float('inf')
                for col in range(COLS):
                    if filled[col] < 6:
                        row = 5 - filled[col]
                        board[row][col] = self.symbol
                        filled[col] += 1
                        score = alpha_beta(board, filled, depth - 1, alpha, beta, False)
                        value = max(value, score)
                        alpha = max(alpha, value)
                        filled[col] -= 1
                        board[row][col] = EMPTY
                        if beta <= alpha:
                            break
                return value
            else:
                value = float('inf')
                for col in range(COLS):
                    if filled[col] < 6:
                        row = 5 - filled[col]
                        board[row][col] = opponent
                        filled[col] += 1
                        score = alpha_beta(board, filled, depth - 1, alpha, beta, True)
                        value = min(value, score)
                        beta = min(beta, value)
                        filled[col] -= 1
                        board[row][col] = EMPTY
                        if beta <= alpha:
                            break
                return value

        start = time.time()
        best_move = valid_cols[0]
        move_scores = {}
        for d in range(1, 43):
            timed_out = False
            move_scores_new = {}
            if d == 1:
                col_order = sorted(valid_cols, key=lambda c: abs(c - 3))
            else:
                col_order = sorted(valid_cols, key=lambda c: move_scores.get(c, -float('inf')), reverse=True)
            current_best_score = -float('inf')
            current_best = None
            root_alpha = -float('inf')
            root_beta = float('inf')
            for col in col_order:
                if time.time() - start > 0.8:
                    timed_out = True
                    break
                row = 5 - filled[col]
                board[row][col] = self.symbol
                filled[col] += 1
                total_discs = sum(filled)
                empty = 42 - total_discs
                win = check_winner(board)
                if win == self.symbol:
                    score = INF + max(empty, 3)
                elif total_discs == 42:
                    score = 0
                else:
                    score = alpha_beta(board, filled, d - 1, root_alpha, root_beta, False)
                move_scores_new[col] = score
                if score > current_best_score:
                    current_best_score = score
                    current_best = col
                root_alpha = max(root_alpha, score)
                filled[col] -= 1
                board[row][col] = EMPTY
            move_scores = move_scores_new
            if current_best is not None:
                best_move = current_best
            if timed_out or time.time() - start > 0.8:
                break
        return best_move
