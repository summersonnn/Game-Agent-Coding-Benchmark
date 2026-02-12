"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-coder@preset/fp8
Run: 2
Generated: 2026-02-12 15:11:12
"""



import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'R' if symbol == 'Y' else 'Y'
        self.ROWS = 6
        self.COLS = 7
        self.EMPTY = ' '
        self.DEPTH = 5  # Adjustable depth for performance vs strength trade-off

    def make_move(self, board):
        """
        Decide the next move using minimax with alpha-beta pruning.
        """
        valid_moves = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
        if not valid_moves:
            return 0  # Should not happen, handled by engine

        best_score = -float('inf')
        best_col = random.choice(valid_moves)

        for col in valid_moves:
            row = self.drop_disc(board, col, self.symbol)
            if row is not None:
                score = self.minimax(board, self.DEPTH - 1, False, -float('inf'), float('inf'))
                self.undo_drop(board, row, col)
                if score > best_score:
                    best_score = score
                    best_col = col
        return best_col

    def minimax(self, board, depth, maximizing_player, alpha, beta):
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 10000 + depth
        elif winner == self.opponent_symbol:
            return -10000 - depth
        elif self.is_full(board) or depth == 0:
            return self.evaluate_board(board)

        valid_moves = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

        if maximizing_player:
            max_eval = -float('inf')
            for col in valid_moves:
                row = self.drop_disc(board, col, self.symbol)
                if row is not None:
                    eval_score = self.minimax(board, depth - 1, False, alpha, beta)
                    self.undo_drop(board, row, col)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                row = self.drop_disc(board, col, self.opponent_symbol)
                if row is not None:
                    eval_score = self.minimax(board, depth - 1, True, alpha, beta)
                    self.undo_drop(board, row, col)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            return min_eval

    def evaluate_board(self, board):
        """
        Heuristic evaluation of board state.
        Positive for self advantage, negative otherwise.
        """
        score = 0
        # Center column preference
        center_col = self.COLS // 2
        center_count = sum(1 for r in range(self.ROWS) if board[r][center_col] == self.symbol)
        score += center_count * 3

        # Score horizontal positions
        for r in range(self.ROWS):
            row_array = [board[r][c] for c in range(self.COLS)]
            for c in range(self.COLS - 3):
                window = row_array[c:c+4]
                score += self.score_window(window)

        # Score vertical positions
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r+4]
                score += self.score_window(window)

        # Score positive diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += self.score_window(window)

        # Score negative diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += self.score_window(window)

        return score

    def score_window(self, window):
        """
        Evaluate a 4-cell window for scoring.
        """
        score = 0
        count_self = window.count(self.symbol)
        count_opponent = window.count(self.opponent_symbol)
        empty_count = window.count(self.EMPTY)

        if count_self == 4:
            score += 100
        elif count_self == 3 and empty_count == 1:
            score += 5
        elif count_self == 2 and empty_count == 2:
            score += 2

        if count_opponent == 3 and empty_count == 1:
            score -= 80  # Block opponent

        return score

    def drop_disc(self, board, col, disc):
        """Drop disc and return row index."""
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                board[r][col] = disc
                return r
        return None

    def undo_drop(self, board, row, col):
        """Remove disc from board."""
        board[row][col] = self.EMPTY

    def check_winner(self, board):
        """Check for winner."""
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]

        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]

        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]

        return None

    def is_full(self, board):
        return all(board[0][c] != self.EMPTY for c in range(self.COLS))
