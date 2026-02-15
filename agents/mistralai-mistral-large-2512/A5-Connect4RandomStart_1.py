"""
Agent Code: A5-Connect4RandomStart
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-14 19:46:39
"""

import math

import random
import math

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.rows = 6
        self.cols = 7
        self.max_depth = 5  # Adjust based on performance needs

    def make_move(self, board):
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return 0

        # Try to win immediately
        for col in valid_moves:
            temp_board = [row[:] for row in board]
            row = self.drop_disc(temp_board, col, self.symbol)
            if self.check_winner(temp_board):
                return col

        # Block opponent's immediate win
        for col in valid_moves:
            temp_board = [row[:] for row in board]
            row = self.drop_disc(temp_board, col, self.opponent_symbol)
            if self.check_winner(temp_board):
                return col

        # Use minimax to find best move
        best_move = None
        best_value = -math.inf
        alpha = -math.inf
        beta = math.inf

        for col in valid_moves:
            temp_board = [row[:] for row in board]
            row = self.drop_disc(temp_board, col, self.symbol)
            move_value = self.minimax(temp_board, self.max_depth - 1, alpha, beta, False)

            if move_value > best_value:
                best_value = move_value
                best_move = col
            alpha = max(alpha, best_value)

        return best_move if best_move is not None else random.choice(valid_moves)

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 1000 + depth  # Prefer faster wins
        elif winner == self.opponent_symbol:
            return -1000 - depth  # Prefer slower losses
        elif depth == 0 or self.is_full(board):
            return self.evaluate_board(board)

        valid_moves = self.get_valid_moves(board)
        if maximizing_player:
            value = -math.inf
            for col in valid_moves:
                temp_board = [row[:] for row in board]
                self.drop_disc(temp_board, col, self.symbol)
                value = max(value, self.minimax(temp_board, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = math.inf
            for col in valid_moves:
                temp_board = [row[:] for row in board]
                self.drop_disc(temp_board, col, self.opponent_symbol)
                value = min(value, self.minimax(temp_board, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def evaluate_board(self, board):
        score = 0

        # Evaluate center control
        center_col = self.cols // 2
        for r in range(self.rows):
            if board[r][center_col] == self.symbol:
                score += 3
            elif board[r][center_col] == self.opponent_symbol:
                score -= 3

        # Evaluate horizontal, vertical, and diagonal patterns
        score += self.evaluate_patterns(board, self.symbol) * 10
        score -= self.evaluate_patterns(board, self.opponent_symbol) * 10

        return score

    def evaluate_patterns(self, board, symbol):
        score = 0

        # Horizontal patterns
        for r in range(self.rows):
            for c in range(self.cols - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self.evaluate_window(window, symbol)

        # Vertical patterns
        for r in range(self.rows - 3):
            for c in range(self.cols):
                window = [board[r+i][c] for i in range(4)]
                score += self.evaluate_window(window, symbol)

        # Diagonal patterns (positive slope)
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, symbol)

        # Diagonal patterns (negative slope)
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, symbol)

        return score

    def evaluate_window(self, window, symbol):
        opponent_symbol = 'Y' if symbol == 'R' else 'R'
        count = window.count(symbol)
        empty = window.count(' ')

        if count == 4:
            return 100
        elif count == 3 and empty == 1:
            return 5
        elif count == 2 and empty == 2:
            return 2
        elif window.count(opponent_symbol) == 3 and empty == 1:
            return -4  # Block opponent's 3 in a row
        return 0

    def get_valid_moves(self, board):
        return [c for c in range(self.cols) if board[0][c] == ' ']

    def drop_disc(self, board, col, symbol):
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return r
        return -1

    def check_winner(self, board):
        # Check horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]

        # Check vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]

        # Check diagonal (positive slope)
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]

        # Check diagonal (negative slope)
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]

        return None

    def is_full(self, board):
        return all(board[0][c] != ' ' for c in range(self.cols))
