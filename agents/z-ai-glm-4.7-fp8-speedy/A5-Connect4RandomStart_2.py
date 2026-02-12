"""
Agent Code: A5-Connect4RandomStart
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 2
Generated: 2026-02-12 14:50:42
"""

import math

import random
import math

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        Initialize the agent.
        name: str - The name of the agent.
        symbol: str - The character representing the agent's disc ('R' or 'Y').
        """
        self.name = name
        self.symbol = symbol
        self.rows = 6
        self.cols = 7
        self.empty = ' '
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        
        # Center column preference (index 3 is the middle)
        self.center_col = 3
        # Order of columns to check for better alpha-beta pruning efficiency
        self.column_order = [3, 2, 4, 1, 5, 0, 6]

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        """
        valid_moves = self.get_valid_moves(board)
        
        # If no moves available (board full), return 0 (should not happen in normal play)
        if not valid_moves:
            return 0

        # 1. Check for immediate winning move
        for col in valid_moves:
            if self.is_winning_move(board, col, self.symbol):
                return col

        # 2. Check if opponent has a winning move they can play next (must block)
        for col in valid_moves:
            if self.is_winning_move(board, col, self.opponent_symbol):
                return col

        # 3. Run Minimax with Alpha-Beta Pruning
        best_score = -math.inf
        best_move = valid_moves[0]
        alpha = -math.inf
        beta = math.inf
        
        # Depth 5 is a safe balance between strength and speed for Python within 1s
        search_depth = 5

        # Sort moves based on center preference to improve pruning
        valid_moves.sort(key=lambda c: self.column_order.index(c) if c in self.column_order else 99)

        for col in valid_moves:
            row = self.get_next_open_row(board, col)
            
            # Simulate move
            board[row][col] = self.symbol
            
            # Evaluate score
            score = self.minimax(board, search_depth - 1, alpha, beta, False)
            
            # Undo move (backtrack)
            board[row][col] = self.empty
            
            if score > best_score:
                best_score = score
                best_move = col
            
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        
        return best_move

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        valid_moves = self.get_valid_moves(board)
        
        # Terminal states checks
        if self.check_win(board, self.symbol):
            # Return large score + depth to prefer faster wins
            return 100000 + depth
        if self.check_win(board, self.opponent_symbol):
            # Return negative large score - depth to prefer slower losses
            return -100000 - depth
        if len(valid_moves) == 0:
            return 0 # Draw
        if depth == 0:
            return self.evaluate_board(board)

        if maximizing_player:
            value = -math.inf
            # Sort moves for efficiency
            valid_moves.sort(key=lambda c: self.column_order.index(c) if c in self.column_order else 99)
            for col in valid_moves:
                row = self.get_next_open_row(board, col)
                board[row][col] = self.symbol
                value = max(value, self.minimax(board, depth - 1, alpha, beta, False))
                board[row][col] = self.empty
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = math.inf
            valid_moves.sort(key=lambda c: self.column_order.index(c) if c in self.column_order else 99)
            for col in valid_moves:
                row = self.get_next_open_row(board, col)
                board[row][col] = self.opponent_symbol
                value = min(value, self.minimax(board, depth - 1, alpha, beta, True))
                board[row][col] = self.empty
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    def evaluate_board(self, board):
        """
        Heuristic evaluation of the board state.
        Scores windows of 4 cells.
        """
        score = 0
        
        # Center column preference
        center_array = [board[r][self.center_col] for r in range(self.rows)]
        score += center_array.count(self.symbol) * 3

        # Horizontal windows
        for r in range(self.rows):
            for c in range(self.cols - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self.score_window(window)

        # Vertical windows
        for c in range(self.cols):
            for r in range(self.rows - 3):
                window = [board[r+i][c] for i in range(4)]
                score += self.score_window(window)

        # Diagonal (positive slope)
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.score_window(window)

        # Diagonal (negative slope)
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.score_window(window)

        return score

    def score_window(self, window):
        """
        Evaluate a single window of 4 cells.
        """
        score = 0
        my_pieces = window.count(self.symbol)
        opp_pieces = window.count(self.opponent_symbol)
        empty_spaces = window.count(self.empty)

        if my_pieces == 4:
            score += 100
        elif my_pieces == 3 and empty_spaces == 1:
            score += 10
        elif my_pieces == 2 and empty_spaces == 2:
            score += 5

        if opp_pieces == 3 and empty_spaces == 1:
            score -= 80 # Heavily penalize opponent having 3 in a row

        return score

    def get_valid_moves(self, board):
        """Returns a list of columns that are not full."""
        return [c for c in range(self.cols) if board[0][c] == self.empty]

    def get_next_open_row(self, board, col):
        """Returns the lowest empty row in a column."""
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == self.empty:
                return r
        return -1

    def is_winning_move(self, board, col, piece):
        """Simulates a drop and checks if it results in a win."""
        row = self.get_next_open_row(board, col)
        if row == -1:
            return False
        board[row][col] = piece
        is_win = self.check_win(board, piece)
        board[row][col] = self.empty # Undo simulation
        return is_win

    def check_win(self, board, piece):
        """Checks if the specified piece has 4 in a row."""
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if all(board[r][c+i] == piece for i in range(4)):
                    return True
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if all(board[r+i][c] == piece for i in range(4)):
                    return True
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if all(board[r-i][c+i] == piece for i in range(4)):
                    return True
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if all(board[r+i][c+i] == piece for i in range(4)):
                    return True
        return False
