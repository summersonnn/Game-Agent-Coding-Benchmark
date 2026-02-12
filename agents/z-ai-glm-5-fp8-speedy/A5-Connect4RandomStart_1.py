"""
Agent Code: A5-Connect4RandomStart
Model: z-ai/glm-5@preset/fp8-speedy
Run: 1
Generated: 2026-02-12 14:50:42
"""

import math

import math
import random

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
        self.rows = 6
        self.cols = 7

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        Uses Minimax with Alpha-Beta pruning.
        """
        valid_cols = [c for c in range(self.cols) if board[0][c] == ' ']
        
        if not valid_cols:
            return 0 # Should not happen in a valid game

        # 1. Check for immediate winning move
        for col in valid_cols:
            row = self.get_next_open_row(board, col)
            temp_board = [r[:] for r in board]
            temp_board[row][col] = self.symbol
            if self.check_winner(temp_board) == self.symbol:
                return col

        # 2. Check for immediate block (opponent winning)
        for col in valid_cols:
            row = self.get_next_open_row(board, col)
            temp_board = [r[:] for r in board]
            temp_board[row][col] = self.opponent_symbol
            if self.check_winner(temp_board) == self.opponent_symbol:
                return col

        # 3. Minimax Algorithm
        # Depth 4 offers a good balance between lookahead and execution time safety (under 1s)
        best_score = -math.inf
        best_col = random.choice(valid_cols)
        
        # Prioritize center columns for move ordering (optimization)
        center_col = self.cols // 2
        valid_cols.sort(key=lambda x: abs(x - center_col))

        for col in valid_cols:
            row = self.get_next_open_row(board, col)
            temp_board = [r[:] for r in board]
            temp_board[row][col] = self.symbol
            # Start minimax with the opponent's turn (minimizing player)
            score = self.minimax(temp_board, 4, -math.inf, math.inf, False)
            
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col

    def get_next_open_row(self, board, col):
        """Return the lowest empty row index in the given column."""
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return -1

    def check_winner(self, board):
        """Check the board for a winner."""
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        return None

    def minimax(self, board, depth, alpha, beta, maximizingPlayer):
        """Minimax algorithm with alpha-beta pruning."""
        valid_cols = [c for c in range(self.cols) if board[0][c] == ' ']
        winner = self.check_winner(board)
        
        # Terminal states
        if winner == self.symbol:
            return 100000000 + depth
        elif winner == self.opponent_symbol:
            return -100000000 - depth
        elif len(valid_cols) == 0: # Draw
            return 0
        elif depth == 0:
            return self.evaluate_board(board)

        # Move ordering: prioritize center
        center_col = self.cols // 2
        valid_cols.sort(key=lambda x: abs(x - center_col))

        if maximizingPlayer:
            value = -math.inf
            for col in valid_cols:
                row = self.get_next_open_row(board, col)
                temp_board = [r[:] for r in board]
                temp_board[row][col] = self.symbol
                new_score = self.minimax(temp_board, depth - 1, alpha, beta, False)
                value = max(value, new_score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = math.inf
            for col in valid_cols:
                row = self.get_next_open_row(board, col)
                temp_board = [r[:] for r in board]
                temp_board[row][col] = self.opponent_symbol
                new_score = self.minimax(temp_board, depth - 1, alpha, beta, True)
                value = min(value, new_score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def evaluate_board(self, board):
        """Heuristic evaluation of the board state."""
        score = 0
        
        # Score Center Column (Strategy: control center)
        center_array = [row[self.cols // 2] for row in board]
        center_count = center_array.count(self.symbol)
        score += center_count * 3

        # Score Horizontal
        for r in range(self.rows):
            row_array = board[r]
            for c in range(self.cols - 3):
                window = row_array[c:c+4]
                score += self.evaluate_window(window)

        # Score Vertical
        for c in range(self.cols):
            for r in range(self.rows - 3):
                window = [board[r+i][c] for i in range(4)]
                score += self.evaluate_window(window)

        # Score Positive Diagonal
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window)

        # Score Negative Diagonal
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window)

        return score

    def evaluate_window(self, window):
        """Score a specific window of 4 cells."""
        score = 0
        my_piece = self.symbol
        opp_piece = self.opponent_symbol
        empty = ' '

        if window.count(my_piece) == 4:
            score += 100
        elif window.count(my_piece) == 3 and window.count(empty) == 1:
            score += 5
        elif window.count(my_piece) == 2 and window.count(empty) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(empty) == 1:
            score -= 4

        return score
