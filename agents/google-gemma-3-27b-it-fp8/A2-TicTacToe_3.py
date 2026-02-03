"""
Agent Code: A2-TicTacToe
Model: google/gemma-3-27b-it@preset/fp8
Run: 3
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
        # Check for winning move
        for i in range(9):
            if board[i] == EMPTY:
                board[i] = self.symbol
                if TicTacToeGame().check_winner() == self.symbol:
                    board[i] = EMPTY  # Reset the board
                    return i
                board[i] = EMPTY  # Reset the board

        # Check for blocking move (opponent about to win)
        opponent_symbol = O_MARK if self.symbol == X_MARK else X_MARK
        for i in range(9):
            if board[i] == EMPTY:
                board[i] = opponent_symbol
                if TicTacToeGame().check_winner() == opponent_symbol:
                    board[i] = EMPTY  # Reset the board
                    return i
                board[i] = EMPTY  # Reset the board

        # Try to take the center
        if board[4] == EMPTY:
            return 4

        # Try to take a corner
        corners = [0, 2, 6, 8]
        for corner in corners:
            if board[corner] == EMPTY:
                return corner

        # Take any available spot
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        return random.choice(available_moves) if available_moves else None
