"""
Agent Code: A5-Connect4RandomStart
Model: google-gemini-3-flash-preview
Run: 2
Generated: 2026-02-12 14:51:12
"""

import random

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        Initialize the agent with a name and piece symbol ('R' or 'Y').
        """
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.rows = 6
        self.cols = 7

    def make_move(self, board):
        """
        Decide the next move using a simplified minimax-style evaluation:
        1. Check for immediate winning moves.
        2. Check for immediate threats to block.
        3. Prefer the center column for better connectivity.
        4. Default to a random valid move if no priority is found.
        """
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        
        if not valid_moves:
            return 0

        # 1. Check if we can win in the next move
        for col in valid_moves:
            row = self._get_drop_row(board, col)
            if self._is_winning_move(board, row, col, self.symbol):
                return col

        # 2. Check if we need to block the opponent from winning
        for col in valid_moves:
            row = self._get_drop_row(board, col)
            if self._is_winning_move(board, row, col, self.opponent_symbol):
                return col

        # 3. Heuristic: Prioritize the center column, then move outwards
        center_preference = [3, 2, 4, 1, 5, 0, 6]
        for col in center_preference:
            if col in valid_moves:
                return col

        return random.choice(valid_moves)

    def _get_drop_row(self, board, col):
        """Finds the row index where a disc would land in a given column."""
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return None

    def _is_winning_move(self, board, row, col, sym):
        """Checks if placing a symbol at (row, col) creates a connect four."""
        # Temporarily place the piece
        board[row][col] = sym
        is_win = False

        # Directions: (row_delta, col_delta)
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            # Check positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r][c] == sym:
                count += 1
                r += dr
                c += dc
            # Check negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r][c] == sym:
                count += 1
                r -= dr
                c -= dc
            
            if count >= 4:
                is_win = True
                break

        # Undo the move
        board[row][col] = ' '
        return is_win