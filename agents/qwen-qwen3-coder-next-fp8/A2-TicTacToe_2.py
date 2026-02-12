"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder-next
Run: 2
Generated: 2026-02-11 20:47:17
"""



import random

EMPTY = ' '

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
    
    def make_move(self, board):
        try:
            # Get all available moves
            available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
            if not available_moves:
                return None
                
            # If it's the first move and center is empty, take it
            if len(available_moves) == 9 or (len(available_moves) == 8 and board[4] == EMPTY):
                if board[4] == EMPTY:
                    return 4
            
            # Try to win or block opponent
            opponent = 'O' if self.symbol == 'X' else 'X'
            
            # Check for winning move
            for move in available_moves:
                temp_board = board.copy()
                temp_board[move] = self.symbol
                if self._check_winner(temp_board) == self.symbol:
                    return move
            
            # Check for blocking move
            for move in available_moves:
                temp_board = board.copy()
                temp_board[move] = opponent
                if self._check_winner(temp_board) == opponent:
                    return move
            
            # Try to take corners
            corners = [0, 2, 6, 8]
            available_corners = [c for c in corners if board[c] == EMPTY]
            if available_corners:
                return random.choice(available_corners)
            
            # Try to take center
            if board[4] == EMPTY:
                return 4
            
            # Take any available edge
            edges = [1, 3, 5, 7]
            available_edges = [e for e in edges if board[e] == EMPTY]
            if available_edges:
                return random.choice(available_edges)
            
            # Fallback to random available move
            return random.choice(available_moves)
            
        except Exception:
            # On any error, return a random valid move
            available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
            return random.choice(available_moves) if available_moves else None
    
    def _check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        if EMPTY not in board:
            return 'DRAW'
        return None
