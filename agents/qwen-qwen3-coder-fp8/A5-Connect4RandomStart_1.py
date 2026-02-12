"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-coder@preset/fp8
Run: 1
Generated: 2026-02-12 15:11:12
"""

import time
from SmartConnect4Agent import Connect4Agent

import random
import time

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        Initialize the agent.
        name: str - The name of the agent.
        symbol: str - The character representing the agent's disc ('R' or 'Y').
        """
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.max_depth = 6  # Adjustable based on performance
        self.start_time = 0
        self.time_limit = 0.95  # Leave a small buffer under 1s

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        """
        self.start_time = time.time()
        valid_cols = [c for c in range(7) if board[0][c] == ' ']

        # Immediate win or block
        for col in valid_cols:
            row = self.get_next_open_row(board, col)
            board[row][col] = self.symbol
            if self.is_winning_move(board, self.symbol):
                board[row][col] = ' '  # Undo
                return col
            board[row][col] = ' '  # Undo

        for col in valid_cols:
            row = self.get_next_open_row(board, col)
            board[row][col] = self.opponent_symbol
            if self.is_winning_move(board, self.opponent_symbol):
                board[row][col] = ' '  # Undo
                return col
            board[row][col] = ' '  # Undo

        # Minimax with iterative deepening
        best_col = random.choice(valid_cols)
        try:
            for depth in range(1, self.max_depth + 1):
                if time.time() - self.start_time > self.time_limit:
                    break
                _, col = self.minimax(board, depth, -float('inf'), float('inf'), True)
                if col is not None:
                    best_col = col
        except:
            pass
        return best_col

    def minimax(self, board, depth, alpha, beta, maximizing):
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        is_terminal = self.is_terminal_node(board)
        if depth == 0 or is_terminal or (time.time() - self.start_time > self.time_limit):
            if is_terminal:
                if self.is_winning_move(board, self.symbol):
                    return (1000000, None)
                elif self.is_winning_move(board, self.opponent_symbol):
                    return (-1000000, None)
                else:
                    return (0, None)
            else:
                return (self.evaluate_board(board), None)
        if maximizing:
            value = -float('inf')
            column = random.choice(valid_cols)
            for col in valid_cols:
                row = self.get_next_open_row(board, col)
                board[row][col] = self.symbol
                new_score, _ = self.minimax(board, depth - 1, alpha, beta, False)
                board[row][col] = ' '
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, column
        else:
            value = float('inf')
            column = random.choice(valid_cols)
            for col in valid_cols:
                row = self.get_next_open_row(board, col)
                board[row][col] = self.opponent_symbol
                new_score, _ = self.minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = ' '
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, column

    def is_terminal_node(self, board):
        return (self.is_winning_move(board, self.symbol) or
                self.is_winning_move(board, self.opponent_symbol) or
                all(board[0][c] != ' ' for c in range(7)))

    def is_winning_move(self, board, piece):
        # Horizontal
        for r in range(6):
            for c in range(4):
                if all(board[r][c + i] == piece for i in range(4)):
                    return True
        # Vertical
        for r in range(3):
            for c in range(7):
                if all(board[r + i][c] == piece for i in range(4)):
                    return True
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if all(board[r - i][c + i] == piece for i in range(4)):
                    return True
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if all(board[r + i][c + i] == piece for i in range(4)):
                    return True
        return False

    def evaluate_board(self, board):
        score = 0
        # Center column preference
        center_col = [board[r][3] for r in range(6)]
        center_count = center_col.count(self.symbol)
        score += center_count * 3

        # Horizontal
        for r in range(6):
            row_array = [board[r][c] for c in range(7)]
            for c in range(4):
                window = row_array[c:c+4]
                score += self.evaluate_window(window)

        # Vertical
        for c in range(7):
            col_array = [board[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window)

        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                window = [board[r - i][c + i] for i in range(4)]
                score += self.evaluate_window(window)

        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r + i][c + i] for i in range(4)]
                score += self.evaluate_window(window)

        return score

    def evaluate_window(self, window):
        score = 0
        player_count = window.count(self.symbol)
        opponent_count = window.count(self.opponent_symbol)
        empty_count = window.count(' ')

        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2

        if opponent_count == 3 and empty_count == 1:
            score -= 4

        return score

    def get_next_open_row(self, board, col):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                return r
        return None
