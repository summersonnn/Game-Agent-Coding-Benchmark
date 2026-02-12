"""
Agent Code: A2-TicTacToe
Model: xiaomi/mimo-v2-flash
Run: 2
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        
    def make_move(self, board):
        # Get all available moves
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        
        if not available_moves:
            return None
            
        # Check if we can win in the next move
        for move in available_moves:
            test_board = board[:]
            test_board[move] = self.symbol
            if self._check_winner(test_board, self.symbol):
                return move
                
        # Check if opponent can win in their next move, and block them
        for move in available_moves:
            test_board = board[:]
            test_board[move] = self.opponent_symbol
            if self._check_winner(test_board, self.opponent_symbol):
                return move
                
        # Try to take the center if available
        if 4 in available_moves:
            return 4
            
        # Try to take a corner if available
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if c in available_moves]
        if available_corners:
            return random.choice(available_corners)
            
        # Take any available edge
        edges = [1, 3, 5, 7]
        available_edges = [e for e in edges if e in available_moves]
        if available_edges:
            return random.choice(available_edges)
            
        # Fallback to random
        return random.choice(available_moves)
        
    def _check_winner(self, board, player):
        # Check rows
        for i in range(0, 9, 3):
            if board[i] == board[i+1] == board[i+2] == player:
                return True
                
        # Check columns
        for i in range(3):
            if board[i] == board[i+3] == board[i+6] == player:
                return True
                
        # Check diagonals
        if board[0] == board[4] == board[8] == player:
            return True
        if board[2] == board[4] == board[6] == player:
            return True
            
        return False
