"""
Agent Code: A2-TicTacToe
Model: minimax/minimax-m2.1@preset/fp8
Run: 1
Generated: 2026-02-11 21:03:27
"""



import random

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
    A strategic Tic Tac Toe agent that uses intelligent decision-making.
    """
    
    # Winning combinations indices
    WIN_LINES = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
        (0, 4, 8), (2, 4, 6)              # Diagonals
    ]
    
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
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        
        if not available_moves:
            return None
            
        # Strategy 1: Check for winning move
        for move in available_moves:
            if self._is_winning_move(board, move, self.symbol):
                return move
                
        # Strategy 2: Block opponent's winning move
        for move in available_moves:
            if self._is_winning_move(board, move, self.opponent_symbol):
                return move
                
        # Strategy 3: Take center if available
        if 4 in available_moves:
            return 4
            
        # Strategy 4: Take corners if available
        corners = [0, 2, 6, 8]
        for corner in corners:
            if corner in available_moves:
                return corner
                
        # Strategy 5: Take edges if available
        edges = [1, 3, 5, 7]
        for edge in edges:
            if edge in available_moves:
                return edge
                
        # Fallback: return random available move
        return random.choice(available_moves)

    def _is_winning_move(self, board, move, symbol):
        """Check if placing symbol at move results in a win."""
        board_copy = board[:]
        board_copy[move] = symbol
        
        for line in self.WIN_LINES:
            a, b, c = line
            if board_copy[a] == board_copy[b] == board_copy[c] == symbol:
                return True
        return False
