"""
Agent Code: A5-Connect4RandomStart
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-14 19:46:39
"""

import copy

import copy

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opp = 'Y' if self.symbol == 'R' else 'R'

    def make_move(self, board):
        valid_cols = self.valid_moves(board)
        if not valid_cols:
            return 0  # though shouldn't happen
        
        # Check for winning move
        for col in valid_cols:
            new_board = self.make_move_on_board(board, col, self.symbol)
            if self.check_winner(new_board) == self.symbol:
                return col
        
        # Check for blocking move
        for col in valid_cols:
            new_board = self.make_move_on_board(board, col, self.opp)
            if self.check_winner(new_board) == self.opp:
                return col
        
        # Use minimax to choose best move
        best_col = valid_cols[0]
        best_score = -float('inf')
        for col in valid_cols:
            new_board = self.make_move_on_board(board, col, self.symbol)
            score = self.minimax(new_board, 4, -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_col = col
        return best_col

    def valid_moves(self, board):
        return [c for c in range(7) if board[0][c] == ' ']

    def make_move_on_board(self, board, col, symbol):
        new_board = [row[:] for row in board]
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = symbol
                return new_board
        return new_board  # shouldn't happen

    def is_terminal(self, board):
        return self.check_winner(board) is not None or self.is_full(board)

    def minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0 or self.is_terminal(board):
            return self.evaluate(board)
        if maximizing:
            max_eval = -float('inf')
            for col in self.valid_moves(board):
                new_board = self.make_move_on_board(board, col, self.symbol)
                eval = self.minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for col in self.valid_moves(board):
                new_board = self.make_move_on_board(board, col, self.opp)
                eval = self.minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate(self, board):
        score = 0
        # Center column preference
        for r in range(6):
            if board[r][3] == self.symbol:
                score += 1
            elif board[r][3] == self.opp:
                score -= 1
        # Evaluate lines
        score += self.evaluate_lines(board, self.symbol)
        score -= self.evaluate_lines(board, self.opp)
        return score

    def evaluate_lines(self, board, symbol):
        total = 0
        # Horizontal
        for r in range(6):
            for c in range(4):
                line = [board[r][c + i] for i in range(4)]
                total += self.score_line(line, symbol)
        # Vertical
        for c in range(7):
            for r in range(3):
                line = [board[r + i][c] for i in range(4)]
                total += self.score_line(line, symbol)
        # Diagonal \
        for r in range(3):
            for c in range(4):
                line = [board[r + i][c + i] for i in range(4)]
                total += self.score_line(line, symbol)
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                line = [board[r - i][c + i] for i in range(4)]
                total += self.score_line(line, symbol)
        return total

    def score_line(self, line, symbol):
        count = sum(1 for cell in line if cell == symbol)
        empty = sum(1 for cell in line if cell == ' ')
        if count == 4:
            return 1000
        elif count == 3 and empty == 1:
            return 100
        elif count == 2 and empty == 2:
            return 10
        elif count == 1 and empty == 3:
            return 1
        return 0

    def check_winner(self, board):
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r][c + i] == board[r][c] for i in range(1, 4)):
                    return board[r][c]
        # Vertical
        for c in range(7):
            for r in range(3):
                if board[r][c] != ' ' and all(board[r + i][c] == board[r][c] for i in range(1, 4)):
                    return board[r][c]
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r + i][c + i] == board[r][c] for i in range(1, 4)):
                    return board[r][c]
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r - i][c + i] == board[r][c] for i in range(1, 4)):
                    return board[r][c]
        return None

    def is_full(self, board):
        return all(board[0][c] != ' ' for c in range(7))
