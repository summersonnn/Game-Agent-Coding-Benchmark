"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-coder@preset/fp8
Run: 1
Generated: 2026-02-13 22:26:38
"""



import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        # Use a simple strategy: 
        # 1. Try to win if possible
        # 2. Block opponent from winning
        # 3. Prefer center columns
        # 4. Otherwise, random valid move
        
        opponent = 'R' if self.symbol == 'Y' else 'Y'
        
        # Check for winning move
        for col in range(7):
            if board[0][col] == ' ':  # Column is not full
                # Simulate dropping disc
                temp_board = [row[:] for row in board]
                self.drop_disc(temp_board, col, self.symbol)
                if self.check_winner(temp_board) == self.symbol:
                    return col
        
        # Check for blocking move
        for col in range(7):
            if board[0][col] == ' ':  # Column is not full
                # Simulate opponent dropping disc
                temp_board = [row[:] for row in board]
                self.drop_disc(temp_board, col, opponent)
                if self.check_winner(temp_board) == opponent:
                    return col
        
        # Prefer center columns
        preferred_cols = [3, 2, 4, 1, 5, 0, 6]
        for col in preferred_cols:
            if board[0][col] == ' ':
                return col
                
        # Fallback to random valid move
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        if valid_cols:
            return random.choice(valid_cols)
        return 0  # Should never happen
    
    def drop_disc(self, board, col, disc):
        """Helper function to simulate dropping a disc."""
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = disc
                return r, col
        return None
    
    def check_winner(self, board):
        """Check for 4 in a row."""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]

        # Vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]

        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]

        # Diagonal \
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]

        return None
