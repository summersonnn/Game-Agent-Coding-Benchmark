"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-max
Run: 1
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    """
    Your agent implementation goes here.
    Implement smart logic to beat your opponent.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        """
        Return the index (0-8) of the cell you want to mark.
        board: List of 9 strings representing the current board state.
              Each element is ' ' (empty), 'X', or 'O'.
        """
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        
        # Check for winning move
        for move in available_moves:
            board_copy = board[:]
            board_copy[move] = self.symbol
            if self._check_winner(board_copy) == self.symbol:
                return move
        
        # Check for blocking opponent's winning move
        for move in available_moves:
            board_copy = board[:]
            board_copy[move] = self.opponent_symbol
            if self._check_winner(board_copy) == self.opponent_symbol:
                return move
        
        # Take center if available
        if 4 in available_moves:
            return 4
        
        # Take corners if available
        corners = [0, 2, 6, 8]
        available_corners = [move for move in corners if move in available_moves]
        if available_corners:
            return random.choice(available_corners)
        
        # Take any remaining side
        sides = [1, 3, 5, 7]
        available_sides = [move for move in sides if move in available_moves]
        if available_sides:
            return random.choice(available_sides)
        
        # Fallback (should not happen if available_moves is not empty)
        return random.choice(available_moves) if available_moves else 0

    def _check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6),              # Diagonals
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        return None
