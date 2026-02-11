"""
Agent Code: A2-TicTacToe
Model: minimax/minimax-m2.1@preset/fp8
Run: 2
Generated: 2026-02-11 20:47:17
"""

import math

import random
import math

# --- Board Representations ---
EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'
BOARD_SIZE = 3


class TicTacToeGame:
    """Manages the state and rules of a Tic Tac Toe game."""

    def __init__(self):
        self.board = [EMPTY for _ in range(9)]
        self.current_turn = X_MARK

    def make_move(self, position):
        if 0 <= position < 9 and self.board[position] == EMPTY:
            self.board[position] = self.current_turn
            self.current_turn = O_MARK if self.current_turn == X_MARK else X_MARK
            return True
        return False

    def check_winner(self):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6),              # Diagonals
        ]
        for combo in win_conditions:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != EMPTY:
                return self.board[combo[0]]
        if EMPTY not in self.board:
            return 'DRAW'
        return None


# -------------------------------------------------------------------------------
class TicTacToeAgent:
    """
    Your agent implementation goes here.
    Implement smart logic to beat your opponent.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent_symbol = O_MARK if symbol == X_MARK else X_MARK
        
    def make_move(self, board):
        """
        Return the index (0-8) of the cell you want to mark.
        board: List of 9 strings representing the current board state.
              Each element is ' ' (empty), 'X', or 'O'.
        """
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return None
            
        # Use minimax algorithm with alpha-beta pruning for optimal play
        best_move = self._get_best_move(board, available_moves)
        return best_move
    
    def _get_best_move(self, board, available_moves):
        """Find the optimal move using minimax with alpha-beta pruning."""
        best_score = -math.inf
        best_move = available_moves[0]
        
        for move in available_moves:
            # Create a new board with the move made
            new_board = board.copy()
            new_board[move] = self.symbol
            
            # Calculate the score for this move
            score = self._minimax(new_board, 0, False, -math.inf, math.inf)
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
    
    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with alpha-beta pruning."""
        winner = self._check_winner(board)
        
        # Base cases
        if winner == self.symbol:
            return 10 - depth  # Prefer faster wins
        elif winner == self.opponent_symbol:
            return depth - 10  # Prefer slower losses
        elif winner == 'DRAW':
            return 0
            
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        
        if is_maximizing:
            max_eval = -math.inf
            for move in available_moves:
                new_board = board.copy()
                new_board[move] = self.symbol
                eval = self._minimax(new_board, depth + 1, False, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for move in available_moves:
                new_board = board.copy()
                new_board[move] = self.opponent_symbol
                eval = self._minimax(new_board, depth + 1, True, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    def _check_winner(self, board):
        """Check the winner on the board."""
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6),              # Diagonals
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        if EMPTY not in board:
            return 'DRAW'
        return None
