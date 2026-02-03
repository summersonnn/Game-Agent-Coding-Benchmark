"""
Agent Code: A2-TicTacToe
Model: google/gemma-3-27b-it@preset/fp8
Run: 4
Generated: 2026-02-03 19:54:05
"""



import random

# --- Board Representations ---
EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'

class TicTacToeGame:
    """ Manages the state and rules of the game. """
    def __init__(self):
        self.board = [EMPTY for _ in range(9)]
        self.current_turn = X_MARK

    def make_move(self, position):
        if self.board[position] == EMPTY:
            self.board[position] = self.current_turn
            self.current_turn = O_MARK if self.current_turn == X_MARK else X_MARK
            return True
        return False

    def check_winner(self):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8), # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8), # Columns
            (0, 4, 8), (2, 4, 6)             # Diagonals
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
        self.symbol = symbol # 'X' or 'O'

    def make_move(self, board):
        """
        Return the index (0-8) of the cell you want to mark.
        board: List of 9 strings representing the current board state.
        """
        if self.symbol == X_MARK:
            return self._minimax(board, self.symbol)
        else:
            return self._minimax(board, self.symbol)

    def _minimax(self, board, player):
        """
        Minimax algorithm to find the best move.
        """
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]

        if not available_moves:
            return None

        if self.check_win(board, player):
            return max(available_moves)

        if self.check_win(board, O_MARK if player == X_MARK else X_MARK):
            return min(available_moves)

        best_move = None
        if player == self.symbol:
            max_eval = float('-inf')
            for move in available_moves:
                new_board = board[:]
                new_board[move] = player
                eval = self._minimax(new_board, O_MARK if player == X_MARK else X_MARK)
                if eval is not None:
                    if eval > max_eval:
                        max_eval = eval
                        best_move = move
        else:
            min_eval = float('inf')
            for move in available_moves:
                new_board = board[:]
                new_board[move] = player
                eval = self._minimax(new_board, X_MARK if player == O_MARK else O_MARK)
                if eval is not None:
                    if eval < min_eval:
                        min_eval = eval
                        best_move = move
        return best_move

    def check_win(self, board, player):
        """
        Helper function to check if a player has won.
        """
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)  # Diagonals
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] == player:
                return True
        return False
