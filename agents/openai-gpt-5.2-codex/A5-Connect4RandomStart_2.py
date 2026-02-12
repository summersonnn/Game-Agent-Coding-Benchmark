"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-5.2-codex
Run: 2
Generated: 2026-02-12 15:02:53
"""

import math

import random
import math

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'R' if symbol == 'Y' else 'Y'
        self.ROWS = 6
        self.COLS = 7
        self.EMPTY = ' '

    def make_move(self, board):
        valid_locations = self.get_valid_locations(board)
        if not valid_locations:
            return 0

        # 1. Check for immediate winning move
        for col in valid_locations:
            if self.is_winning_move(board, self.symbol, col):
                return col

        # 2. Block opponent's immediate win
        for col in valid_locations:
            if self.is_winning_move(board, self.opponent, col):
                return col

        # 3. Use minimax
        depth = self.choose_depth(board)
        col, _ = self.minimax(board, depth, -math.inf, math.inf, True)
        if col is None:
            col = random.choice(valid_locations)
        return col

    def choose_depth(self, board):
        empty = sum(row.count(self.EMPTY) for row in board)
        if empty > 30:
            return 4
        elif empty > 15:
            return 5
        else:
            return 6

    def get_valid_locations(self, board):
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    def get_next_open_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return None

    def is_winning_move(self, board, piece, col):
        row = self.get_next_open_row(board, col)
        if row is None:
            return False
        temp = [r[:] for r in board]
        temp[row][col] = piece
        return self.winning_move(temp, piece)

    def winning_move(self, board, piece):
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if all(board[r][c+i] == piece for i in range(4)):
                    return True
        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if all(board[r+i][c] == piece for i in range(4)):
                    return True
        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if all(board[r-i][c+i] == piece for i in range(4)):
                    return True
        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if all(board[r+i][c+i] == piece for i in range(4)):
                    return True
        return False

    def score_position(self, board, piece):
        score = 0

        # Center column preference
        center_array = [board[r][self.COLS // 2] for r in range(self.ROWS)]
        score += center_array.count(piece) * 3

        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = board[r][c:c+4]
                score += self.evaluate_window(window, piece)

        # Vertical
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, piece)

        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        return score

    def evaluate_window(self, window, piece):
        score = 0
        opp = self.opponent if piece == self.symbol else self.symbol

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(self.EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(self.EMPTY) == 2:
            score += 2

        if window.count(opp) == 3 and window.count(self.EMPTY) == 1:
            score -= 4
        elif window.count(opp) == 4:
            score -= 100

        return score

    def minimax(self, board, depth, alpha, beta, maximizing):
        valid_locations = self.get_valid_locations(board)
        terminal = (
            self.winning_move(board, self.symbol) or
            self.winning_move(board, self.opponent) or
            len(valid_locations) == 0
        )

        if depth == 0 or terminal:
            if terminal:
                if self.winning_move(board, self.symbol):
                    return None, 1e6
                elif self.winning_move(board, self.opponent):
                    return None, -1e6
                else:
                    return None, 0
            else:
                return None, self.score_position(board, self.symbol)

        if maximizing:
            value = -math.inf
            best_col = random.choice(valid_locations)
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                b_copy[row][col] = self.symbol
                new_score = self.minimax(b_copy, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value

        else:
            value = math.inf
            best_col = random.choice(valid_locations)
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                b_copy[row][col] = self.opponent
                new_score = self.minimax(b_copy, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value
