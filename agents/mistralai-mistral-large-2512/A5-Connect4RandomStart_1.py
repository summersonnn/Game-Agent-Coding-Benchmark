"""
Agent Code: A5-Connect4RandomStart
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-12 14:50:42
"""

import time
from copy import deepcopy

import random
import time
from copy import deepcopy

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.rows = 6
        self.cols = 7
        self.max_depth = 5  # Initial depth, will adjust based on time
        self.start_time = 0

    def make_move(self, board):
        self.start_time = time.time()

        # First check if we can win immediately
        for col in range(self.cols):
            if self.is_valid_move(board, col):
                temp_board = deepcopy(board)
                row = self.drop_disc(temp_board, col, self.symbol)
                if self.check_winner(temp_board, row, col, self.symbol):
                    return col

        # Then check if opponent can win next move and block them
        for col in range(self.cols):
            if self.is_valid_move(board, col):
                temp_board = deepcopy(board)
                row = self.drop_disc(temp_board, col, self.opponent_symbol)
                if self.check_winner(temp_board, row, col, self.opponent_symbol):
                    return col

        # Use iterative deepening to find the best move within time limit
        best_move = random.choice([c for c in range(self.cols) if self.is_valid_move(board, c)])
        best_score = -float('inf')

        for depth in range(1, 6):  # Try increasing depths until time runs out
            self.max_depth = depth
            current_score, current_move = self.minimax(board, depth, -float('inf'), float('inf'), True)

            if time.time() - self.start_time > 0.9:  # Leave some buffer
                break

            if current_score > best_score:
                best_score = current_score
                best_move = current_move

        return best_move

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        # Check if we're out of time
        if time.time() - self.start_time > 0.9:
            return 0, None

        # Check for terminal states
        winner = self.check_winner_all(board)
        if winner == self.symbol:
            return 1000000, None  # Large positive score for winning
        elif winner == self.opponent_symbol:
            return -1000000, None  # Large negative score for losing
        elif self.is_board_full(board):
            return 0, None  # Draw

        if depth == 0:
            return self.evaluate_board(board), None

        valid_moves = [c for c in range(self.cols) if self.is_valid_move(board, c)]

        if maximizing_player:
            value = -float('inf')
            best_move = random.choice(valid_moves)
            for col in valid_moves:
                temp_board = deepcopy(board)
                row = self.drop_disc(temp_board, col, self.symbol)
                score, _ = self.minimax(temp_board, depth-1, alpha, beta, False)

                if score > value:
                    value = score
                    best_move = col

                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_move
        else:
            value = float('inf')
            best_move = random.choice(valid_moves)
            for col in valid_moves:
                temp_board = deepcopy(board)
                row = self.drop_disc(temp_board, col, self.opponent_symbol)
                score, _ = self.minimax(temp_board, depth-1, alpha, beta, True)

                if score < value:
                    value = score
                    best_move = col

                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, best_move

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
            return 100  # Win
        elif count == 3 and empty == 1:
            return 5    # Three in a row with open space
        elif count == 2 and empty == 2:
            return 2    # Two in a row with two open spaces
        elif window.count(opponent_symbol) == 3 and empty == 1:
            return -4   # Block opponent's three in a row
        else:
            return 0

    def is_valid_move(self, board, col):
        return 0 <= col < self.cols and board[0][col] == ' '

    def drop_disc(self, board, col, symbol):
        for r in range(self.rows-1, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return r
        return -1

    def check_winner(self, board, row, col, symbol):
        # Check horizontal
        for c in range(max(0, col-3), min(self.cols-3, col+1)):
            if (board[row][c] == symbol and
                board[row][c+1] == symbol and
                board[row][c+2] == symbol and
                board[row][c+3] == symbol):
                return True

        # Check vertical
        for r in range(max(0, row-3), min(self.rows-3, row+1)):
            if (board[r][col] == symbol and
                board[r+1][col] == symbol and
                board[r+2][col] == symbol and
                board[r+3][col] == symbol):
                return True

        # Check diagonal (positive slope)
        for r, c in zip(range(row, max(-1, row-4), -1), range(col, max(-1, col-4), -1)):
            if (r-3 >= 0 and c-3 >= 0 and
                board[r][c] == symbol and
                board[r-1][c-1] == symbol and
                board[r-2][c-2] == symbol and
                board[r-3][c-3] == symbol):
                return True

        # Check diagonal (negative slope)
        for r, c in zip(range(row, min(self.rows, row+4)), range(col, max(-1, col-4), -1)):
            if (r+3 < self.rows and c-3 >= 0 and
                board[r][c] == symbol and
                board[r+1][c-1] == symbol and
                board[r+2][c-2] == symbol and
                board[r+3][c-3] == symbol):
                return True

        return False

    def check_winner_all(self, board):
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
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]

        # Check diagonal (negative slope)
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]

        return None

    def is_board_full(self, board):
        return all(board[0][c] != ' ' for c in range(self.cols))
