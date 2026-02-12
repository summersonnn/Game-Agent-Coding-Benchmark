"""
Agent Code: A5-Connect4RandomStart
Model: x-ai/grok-code-fast-1
Run: 2
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

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        
        Args:
            board: A list of lists representing the 6x7 grid.
                   board[row][col] contains 'R', 'Y', or ' ' (empty).
                   Row 0 is the top, Row 5 is the bottom.
                   
        Returns:
            int: The column index (0-6) where the agent wants to drop a disc.
        """
        # Use minimax with alpha-beta pruning to find the best move
        piece = self.symbol
        valid_locations = self.get_valid_locations(board)
        if not valid_locations:
            return 0  # Fallback, though unlikely
        
        # Perform minimax with depth 5 (adjustable based on time constraints)
        best_col, minimax_score = self.minimax(board, 5, -math.inf, math.inf, True, piece)
        return best_col

    def get_valid_locations(self, board):
        """Return a list of valid column indices (not full)."""
        valid_locations = []
        for col in range(7):
            if board[0][col] == ' ':
                valid_locations.append(col)
        return valid_locations

    def get_next_open_row(self, board, col):
        """Return the next open row in the given column."""
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                return r
        return None  # Should not happen if valid

    def drop_piece(self, board, row, col, piece):
        """Drop a piece on the board copy."""
        board[row][col] = piece

    def winning_move(self, board, piece):
        """Check if the given piece has a winning move."""
        # Horizontal
        for c in range(4):
            for r in range(6):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        # Vertical
        for c in range(7):
            for r in range(3):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
        # Positive diagonal
        for c in range(4):
            for r in range(3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        # Negative diagonal
        for c in range(4):
            for r in range(3, 6):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        return False

    def evaluate_window(self, window, piece):
        """Evaluate a 4-cell window."""
        score = 0
        opp_piece = 'R' if piece == 'Y' else 'Y'
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(' ') == 1:
            score += 10
        elif window.count(piece) == 2 and window.count(' ') == 2:
            score += 2
        if window.count(opp_piece) == 3 and window.count(' ') == 1:
            score -= 80
        return score

    def score_position(self, board, piece):
        """Score the board position for the given piece."""
        score = 0
        # Score center column
        center_array = [board[i][3] for i in range(6)]
        center_count = center_array.count(piece)
        score += center_count * 3
        # Horizontal
        for r in range(6):
            row_array = board[r]
            for c in range(4):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, piece)
        # Vertical
        for c in range(7):
            col_array = [board[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, piece)
        # Positive diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)
        # Negative diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+3-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)
        return score

    def is_terminal_node(self, board):
        """Check if the game is over."""
        return self.winning_move(board, 'R') or self.winning_move(board, 'Y') or len(self.get_valid_locations(board)) == 0

    def minimax(self, board, depth, alpha, beta, maximizingPlayer, piece):
        """Minimax algorithm with alpha-beta pruning."""
        valid_locations = self.get_valid_locations(board)
        is_terminal = self.is_terminal_node(board)
        if depth == 0 or is_terminal:
            if is_terminal:
                if self.winning_move(board, piece):
                    return (None, 100000000000000)
                elif self.winning_move(board, 'R' if piece == 'Y' else 'Y'):
                    return (None, -100000000000000)
                else:  # Draw
                    return (None, 0)
            else:  # Depth zero
                return (None, self.score_position(board, piece))
        
        if maximizingPlayer:
            max_eval = -math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                self.drop_piece(b_copy, row, col, piece)
                new_score = self.minimax(b_copy, depth-1, alpha, beta, False, piece)[1]
                if new_score > max_eval:
                    max_eval = new_score
                    column = col
                alpha = max(alpha, max_eval)
                if alpha >= beta:
                    break
            return column, max_eval
        else:
            min_eval = math.inf
            column = random.choice(valid_locations)
            opp_piece = 'R' if piece == 'Y' else 'Y'
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                self.drop_piece(b_copy, row, col, opp_piece)
                new_score = self.minimax(b_copy, depth-1, alpha, beta, True, piece)[1]
                if new_score < min_eval:
                    min_eval = new_score
                    column = col
                beta = min(beta, min_eval)
                if alpha >= beta:
                    break
            return column, min_eval
