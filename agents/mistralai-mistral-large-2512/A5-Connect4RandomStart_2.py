"""
Agent Code: A5-Connect4RandomStart
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-12 14:50:42
"""

import time

import random
import time

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.rows = 6
        self.cols = 7
        self.max_depth = 5  # Adjust based on performance needs

    def make_move(self, board):
        """
        Decide the next move using minimax with alpha-beta pruning.
        """
        start_time = time.time()

        # First check if we can win immediately
        winning_move = self.find_winning_move(board, self.symbol)
        if winning_move is not None:
            return winning_move

        # Then check if opponent can win next move and block
        blocking_move = self.find_winning_move(board, self.opponent_symbol)
        if blocking_move is not None:
            return blocking_move

        # Use minimax for deeper lookahead
        best_move = None
        best_value = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        # Try center column first for better position
        columns = list(range(self.cols))
        random.shuffle(columns)  # Add some randomness to avoid predictable patterns
        columns.sort(key=lambda x: abs(x - self.cols//2))  # Prefer center columns

        for col in columns:
            row = self.get_next_open_row(board, col)
            if row is not None:
                # Make the move
                board[row][col] = self.symbol
                move_value = self.minimax(board, self.max_depth - 1, alpha, beta, False, start_time)
                # Undo the move
                board[row][col] = ' '

                if move_value > best_value:
                    best_value = move_value
                    best_move = col

                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break  # Beta cutoff

        # If no good move found (shouldn't happen), return a random valid move
        if best_move is None:
            valid_moves = [c for c in range(self.cols) if self.get_next_open_row(board, c) is not None]
            return random.choice(valid_moves) if valid_moves else 0

        return best_move

    def minimax(self, board, depth, alpha, beta, maximizing_player, start_time):
        """
        Minimax algorithm with alpha-beta pruning.
        """
        # Check timeout (1 second limit)
        if time.time() - start_time > 0.95:  # Leave some buffer
            return 0

        # Check for terminal states
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 1000 + depth  # Higher score for faster wins
        elif winner == self.opponent_symbol:
            return -1000 - depth  # Lower score for faster losses
        elif self.is_board_full(board):
            return 0

        if depth == 0:
            return self.evaluate_board(board)

        if maximizing_player:
            value = -float('inf')
            columns = list(range(self.cols))
            random.shuffle(columns)
            for col in columns:
                row = self.get_next_open_row(board, col)
                if row is not None:
                    board[row][col] = self.symbol
                    value = max(value, self.minimax(board, depth - 1, alpha, beta, False, start_time))
                    board[row][col] = ' '
                    alpha = max(alpha, value)
                    if beta <= alpha:
                        break  # Beta cutoff
            return value
        else:
            value = float('inf')
            columns = list(range(self.cols))
            random.shuffle(columns)
            for col in columns:
                row = self.get_next_open_row(board, col)
                if row is not None:
                    board[row][col] = self.opponent_symbol
                    value = min(value, self.minimax(board, depth - 1, alpha, beta, True, start_time))
                    board[row][col] = ' '
                    beta = min(beta, value)
                    if beta <= alpha:
                        break  # Alpha cutoff
            return value

    def evaluate_board(self, board):
        """
        Evaluate the board position using a heuristic.
        """
        score = 0

        # Evaluate center control
        center_col = self.cols // 2
        for row in range(self.rows):
            if board[row][center_col] == self.symbol:
                score += 3
            elif board[row][center_col] == self.opponent_symbol:
                score -= 3

        # Evaluate all possible lines (horizontal, vertical, diagonal)
        score += self.evaluate_lines(board, self.symbol) * 5
        score -= self.evaluate_lines(board, self.opponent_symbol) * 5

        # Add some randomness to avoid predictable patterns
        score += random.uniform(-0.1, 0.1)

        return score

    def evaluate_lines(self, board, symbol):
        """
        Evaluate all possible lines for the given symbol.
        """
        score = 0

        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self.evaluate_window(window, symbol)

        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                window = [board[r+i][c] for i in range(4)]
                score += self.evaluate_window(window, symbol)

        # Diagonal (positive slope)
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, symbol)

        # Diagonal (negative slope)
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, symbol)

        return score

    def evaluate_window(self, window, symbol):
        """
        Evaluate a window of 4 cells.
        """
        opponent_symbol = 'Y' if symbol == 'R' else 'R'
        count_symbol = window.count(symbol)
        count_opponent = window.count(opponent_symbol)
        count_empty = window.count(' ')

        if count_opponent == 0:
            if count_symbol == 4:
                return 100
            elif count_symbol == 3:
                return 5
            elif count_symbol == 2:
                return 2
            elif count_symbol == 1:
                return 1
        elif count_symbol == 0:
            if count_opponent == 4:
                return -100
            elif count_opponent == 3:
                return -5
            elif count_opponent == 2:
                return -2
            elif count_opponent == 1:
                return -1

        return 0

    def find_winning_move(self, board, symbol):
        """
        Check if there's a winning move available.
        """
        for col in range(self.cols):
            row = self.get_next_open_row(board, col)
            if row is not None:
                board[row][col] = symbol
                if self.check_winner(board) == symbol:
                    board[row][col] = ' '
                    return col
                board[row][col] = ' '
        return None

    def get_next_open_row(self, board, col):
        """
        Get the next open row in a column.
        """
        for r in range(self.rows-1, -1, -1):
            if board[r][col] == ' ':
                return r
        return None

    def check_winner(self, board):
        """
        Check if there's a winner on the board.
        """
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]

        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]

        # Diagonal (positive slope)
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]

        # Diagonal (negative slope)
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]

        return None

    def is_board_full(self, board):
        """
        Check if the board is full.
        """
        return all(board[0][c] != ' ' for c in range(self.cols))
