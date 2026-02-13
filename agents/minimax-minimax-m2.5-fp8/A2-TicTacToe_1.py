"""
Agent Code: A2-TicTacToe
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:10:12
"""



import random

# --- Board Representations ---
EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'
BOARD_SIZE = 3


class TicTacToeAgent:
    """
    Smart Tic Tac Toe agent using minimax algorithm for optimal play.
    """
    
    WIN_COMBINATIONS = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
        (0, 4, 8), (2, 4, 6)               # Diagonals
    ]
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = O_MARK if symbol == X_MARK else X_MARK
    
    def make_move(self, board):
        """Return the index (0-8) of the cell to mark."""
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        
        if not available_moves:
            return None
        
        # Check for immediate win
        for move in available_moves:
            test_board = board[:]
            test_board[move] = self.symbol
            if self._check_winner(test_board) == self.symbol:
                return move
        
        # Check for immediate block
        for move in available_moves:
            test_board = board[:]
            test_board[move] = self.opponent
            if self._check_winner(test_board) == self.opponent:
                return move
        
        # Use minimax for optimal play
        best_score = float('-inf')
        best_move = available_moves[0]
        
        for move in available_moves:
            new_board = board[:]
            new_board[move] = self.symbol
            score = self._minimax(new_board, 0, False, float('-inf'), float('inf'))
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with alpha-beta pruning."""
        winner = self._check_winner(board)
        
        if winner == self.symbol:
            return 10 - depth
        elif winner == self.opponent:
            return depth - 10
        elif EMPTY not in board:
            return 0
        
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in available_moves:
                new_board = board[:]
                new_board[move] = self.symbol
                eval_score = self._minimax(new_board, depth + 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available_moves:
                new_board = board[:]
                new_board[move] = self.opponent
                eval_score = self._minimax(new_board, depth + 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def _check_winner(self, board):
        """Check if there's a winner on the board."""
        for combo in self.WIN_COMBINATIONS:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        if EMPTY not in board:
            return 'DRAW'
        return None
