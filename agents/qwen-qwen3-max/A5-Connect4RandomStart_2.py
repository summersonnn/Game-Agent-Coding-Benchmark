"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-max
Run: 2
Generated: 2026-02-12 14:50:42
"""



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
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'

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
        # Get all valid moves (columns that aren't full)
        valid_moves = self.get_valid_moves(board)
        
        # If no valid moves, return 0 (though game should be over by then)
        if not valid_moves:
            return 0
        
        # Check for immediate winning move
        for col in valid_moves:
            if self.is_winning_move(board, col, self.symbol):
                return col
        
        # Block opponent's immediate winning move
        for col in valid_moves:
            if self.is_winning_move(board, col, self.opponent_symbol):
                return col
        
        # Try to build a threat (create a 3-in-a-row with open ends)
        for col in valid_moves:
            if self.creates_threat(board, col, self.symbol):
                return col
        
        # Block opponent's threat
        for col in valid_moves:
            if self.creates_threat(board, col, self.opponent_symbol):
                return col
        
        # Prefer center columns (3, 2, 4, 1, 5, 0, 6)
        center_first = [3, 2, 4, 1, 5, 0, 6]
        for col in center_first:
            if col in valid_moves:
                return col
        
        # If all else fails, pick a random valid move
        return random.choice(valid_moves)
    
    def get_valid_moves(self, board):
        """Return a list of valid column indices (not full)."""
        valid_moves = []
        for col in range(7):
            if board[0][col] == ' ':  # Top row empty means column isn't full
                valid_moves.append(col)
        return valid_moves
    
    def get_next_open_row(self, board, col):
        """Get the next open row in the given column."""
        for row in range(5, -1, -1):  # Start from bottom (row 5)
            if board[row][col] == ' ':
                return row
        return -1  # Column is full
    
    def is_winning_move(self, board, col, symbol):
        """Check if placing a disc in the given column would win the game."""
        row = self.get_next_open_row(board, col)
        if row == -1:
            return False
        
        # Temporarily place the disc
        board[row][col] = symbol
        
        # Check if this creates a win
        is_winning = self.check_win_at_position(board, row, col, symbol)
        
        # Undo the temporary placement
        board[row][col] = ' '
        
        return is_winning
    
    def check_win_at_position(self, board, row, col, symbol):
        """Check if there's a win at the given position."""
        # Check horizontal
        for c in range(max(0, col-3), min(4, col+1)):
            if (board[row][c] == symbol and 
                board[row][c+1] == symbol and 
                board[row][c+2] == symbol and 
                board[row][c+3] == symbol):
                return True
        
        # Check vertical
        if row <= 2:  # Need at least 4 rows from this position down
            if (board[row][col] == symbol and 
                board[row+1][col] == symbol and 
                board[row+2][col] == symbol and 
                board[row+3][col] == symbol):
                return True
        
        # Check diagonal (positive slope)
        for r in range(max(0, row-3), min(3, row+1)):
            c = col - (row - r)
            if 0 <= c <= 3:
                if (board[r][c] == symbol and 
                    board[r+1][c+1] == symbol and 
                    board[r+2][c+2] == symbol and 
                    board[r+3][c+3] == symbol):
                    return True
        
        # Check diagonal (negative slope)
        for r in range(max(3, row), min(6, row+4)):
            c = col - (row - r)
            if 0 <= c <= 3:
                if (board[r][c] == symbol and 
                    board[r-1][c+1] == symbol and 
                    board[r-2][c+2] == symbol and 
                    board[r-3][c+3] == symbol):
                    return True
        
        return False
    
    def creates_threat(self, board, col, symbol):
        """Check if placing a disc in the given column creates a 3-in-a-row with open ends."""
        row = self.get_next_open_row(board, col)
        if row == -1:
            return False
        
        # Temporarily place the disc
        board[row][col] = symbol
        
        # Check if this creates a threat (3 in a row with at least one open end)
        creates_threat = self.has_threat_at_position(board, row, col, symbol)
        
        # Undo the temporary placement
        board[row][col] = ' '
        
        return creates_threat
    
    def has_threat_at_position(self, board, row, col, symbol):
        """Check if there's a 3-in-a-row threat at the given position."""
        # Check horizontal threats
        for offset in range(-3, 1):
            if 0 <= col + offset <= 3:
                segment = [board[row][col + offset + i] for i in range(4)]
                if segment.count(symbol) == 3 and segment.count(' ') == 1:
                    return True
        
        # Check vertical threats (only if there's room above)
        if row >= 3:
            segment = [board[row - i][col] for i in range(4)]
            if segment.count(symbol) == 3 and segment.count(' ') == 1:
                return True
        
        # Check diagonal (\) threats
        for r_offset in range(-3, 1):
            c_offset = r_offset
            r, c = row + r_offset, col + c_offset
            if 0 <= r <= 2 and 0 <= c <= 3:
                segment = [board[r + i][c + i] for i in range(4)]
                if segment.count(symbol) == 3 and segment.count(' ') == 1:
                    return True
        
        # Check diagonal (/) threats
        for r_offset in range(-3, 1):
            c_offset = -r_offset
            r, c = row + r_offset, col + c_offset
            if 3 <= r <= 5 and 0 <= c <= 3:
                segment = [board[r - i][c + i] for i in range(4)]
                if segment.count(symbol) == 3 and segment.count(' ') == 1:
                    return True
        
        return False
