"""
Agent Code: A5-Connect4RandomStart
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-14 19:46:39
"""

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'

    def make_move(self, board):
        best_score = -float('inf')
        best_col = None
        move_order = [3, 4, 2, 5, 1, 6, 0]
        alpha = -float('inf')
        beta = float('inf')
        depth = 7
        for col in move_order:
            if self.is_valid_move(board, col):
                row = self.drop(board, col, self.symbol)
                score = self.minimax(board, depth - 1, alpha, beta, False)
                self.undo(board, row, col)
                if score > best_score:
                    best_score = score
                    best_col = col
                alpha = max(alpha, score)
        return best_col

    def minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0 or self.check_winner(board) is not None or self.is_full(board):
            return self.evaluate(board)
        move_order = [3, 4, 2, 5, 1, 6, 0]
        if maximizing:
            max_eval = -float('inf')
            for col in move_order:
                if self.is_valid_move(board, col):
                    row = self.drop(board, col, self.symbol)
                    eval_ = self.minimax(board, depth - 1, alpha, beta, False)
                    self.undo(board, row, col)
                    max_eval = max(max_eval, eval_)
                    alpha = max(alpha, max_eval)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for col in move_order:
                if self.is_valid_move(board, col):
                    row = self.drop(board, col, self.opponent)
                    eval_ = self.minimax(board, depth - 1, alpha, beta, True)
                    self.undo(board, row, col)
                    min_eval = min(min_eval, eval_)
                    beta = min(beta, min_eval)
                    if beta <= alpha:
                        break
            return min_eval

    def evaluate(self, board):
        winner = self.check_winner(board)
        if winner is not None:
            empty = sum(1 for r in range(6) for c in range(7) if board[r][c] == ' ')
            if winner == self.symbol:
                return 1000000 + empty
            else:
                return -1000000 - empty
        if self.is_full(board):
            return 0
        my_score = 0
        opp_score = 0
        directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]
        for dr, dc in directions:
            for r in range(6):
                for c in range(7):
                    if (r + 3 * dr >= 0 and r + 3 * dr < 6 and
                        c + 3 * dc >= 0 and c + 3 * dc < 7):
                        window = [board[r + i * dr][c + i * dc] for i in range(4)]
                        my_count = window.count(self.symbol)
                        opp_count = window.count(self.opponent)
                        if opp_count == 0:
                            my_score += 10 ** my_count
                        if my_count == 0:
                            opp_score += 10 ** opp_count
        return my_score - opp_score

    def drop(self, board, col, symbol):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return r
        return None

    def undo(self, board, row, col):
        board[row][col] = ' '

    def is_valid_move(self, board, col):
        return 0 <= col < 7 and board[0][col] == ' '

    def is_full(self, board):
        return all(board[0][c] != ' ' for c in range(7))

    def check_winner(self, board):
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r][c] == board[r][c + i] for i in range(1, 4)):
                    return board[r][c]
        # Vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and all(board[r][c] == board[r + i][c] for i in range(1, 4)):
                    return board[r][c]
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r][c] == board[r - i][c + i] for i in range(1, 4)):
                    return board[r][c]
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r][c] == board[r + i][c + i] for i in range(1, 4)):
                    return board[r][c]
        return None