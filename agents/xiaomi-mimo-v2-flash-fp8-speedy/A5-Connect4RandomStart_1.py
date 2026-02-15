"""
Agent Code: A5-Connect4RandomStart
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 1
Generated: 2026-02-12 14:50:42
"""

import time

import random
import time

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
        # Precompute move ordering for better alpha-beta performance
        self.move_order = [3, 2, 4, 1, 5, 0, 6]  # Center columns first
        
    def get_valid_columns(self, board):
        """Return list of valid columns (non-full columns)."""
        valid_cols = []
        for col in range(7):
            if board[0][col] == ' ':  # Check top row
                valid_cols.append(col)
        return valid_cols
    
    def is_terminal(self, board):
        """Check if the game is over (win or full board)."""
        return self.check_winner(board) is not None or self.is_full(board)
    
    def is_full(self, board):
        """Check if the board is completely full."""
        return all(cell != ' ' for row in board for cell in row)
    
    def check_winner(self, board):
        """Check if there's a winner on the board."""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        
        # Vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        
        # Diagonal (top-left to bottom-right)
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        
        # Diagonal (top-right to bottom-left)
        for r in range(3):
            for c in range(3, 7):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c-1] == board[r+2][c-2] == board[r+3][c-3]:
                    return board[r][c]
        
        return None
    
    def drop_disc(self, board, col, symbol):
        """Simulate dropping a disc and return the new board state."""
        new_board = [row[:] for row in board]  # Deep copy
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = symbol
                return new_board
        return None  # Column is full
    
    def evaluate_window(self, window, symbol):
        """Evaluate a window of 4 cells and return a score."""
        opponent = 'Y' if symbol == 'R' else 'R'
        
        count_symbol = window.count(symbol)
        count_opponent = window.count(opponent)
        count_empty = window.count(' ')
        
        if count_symbol == 4:
            return 1000000  # Winning move
        elif count_symbol == 3 and count_empty == 1:
            return 100  # Very good
        elif count_symbol == 2 and count_empty == 2:
            return 10  # Good
        elif count_opponent == 3 and count_empty == 1:
            return -1000  # Must block opponent
        elif count_opponent == 2 and count_empty == 2:
            return -10  # Bad
        return 0
    
    def evaluate_board(self, board, symbol):
        """Evaluate the board and return a score for the given symbol."""
        score = 0
        
        # Center column preference
        center_column = [board[r][3] for r in range(6)]
        center_count = center_column.count(symbol)
        score += center_count * 3
        
        # Horizontal windows
        for r in range(6):
            for c in range(4):
                window = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]]
                score += self.evaluate_window(window, symbol)
        
        # Vertical windows
        for r in range(3):
            for c in range(7):
                window = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]]
                score += self.evaluate_window(window, symbol)
        
        # Diagonal (top-left to bottom-right)
        for r in range(3):
            for c in range(4):
                window = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]]
                score += self.evaluate_window(window, symbol)
        
        # Diagonal (top-right to bottom-left)
        for r in range(3):
            for c in range(3, 7):
                window = [board[r][c], board[r+1][c-1], board[r+2][c-2], board[r+3][c-3]]
                score += self.evaluate_window(window, symbol)
        
        return score
    
    def minimax(self, board, depth, alpha, beta, maximizing_player, start_time, time_limit=0.9):
        """
        Minimax algorithm with alpha-beta pruning.
        Returns (best_score, best_column)
        """
        # Check time limit
        if time.time() - start_time > time_limit:
            return self.evaluate_board(board, self.symbol), None
        
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 1000000, None  # We win
        elif winner == self.opponent_symbol:
            return -1000000, None  # We lose
        elif self.is_full(board) or depth == 0:
            return self.evaluate_board(board, self.symbol), None
        
        valid_cols = self.get_valid_columns(board)
        if not valid_cols:
            return 0, None
        
        # Order moves for better pruning
        ordered_cols = [col for col in self.move_order if col in valid_cols]
        
        if maximizing_player:
            best_score = -float('inf')
            best_col = ordered_cols[0] if ordered_cols else valid_cols[0]
            
            for col in ordered_cols:
                new_board = self.drop_disc(board, col, self.symbol)
                if new_board is None:
                    continue
                
                score, _ = self.minimax(new_board, depth - 1, alpha, beta, False, start_time, time_limit)
                
                if score > best_score:
                    best_score = score
                    best_col = col
                
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return best_score, best_col
        
        else:  # Minimizing player
            best_score = float('inf')
            best_col = ordered_cols[0] if ordered_cols else valid_cols[0]
            
            for col in ordered_cols:
                new_board = self.drop_disc(board, col, self.opponent_symbol)
                if new_board is None:
                    continue
                
                score, _ = self.minimax(new_board, depth - 1, alpha, beta, True, start_time, time_limit)
                
                if score < best_score:
                    best_score = score
                    best_col = col
                
                beta = min(beta, best_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return best_score, best_col
    
    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        """
        start_time = time.time()
        
        # Check for immediate winning move
        valid_cols = self.get_valid_columns(board)
        for col in valid_cols:
            new_board = self.drop_disc(board, col, self.symbol)
            if new_board and self.check_winner(new_board) == self.symbol:
                return col
        
        # Check for immediate blocking move (opponent can win next turn)
        for col in valid_cols:
            new_board = self.drop_disc(board, col, self.opponent_symbol)
            if new_board and self.check_winner(new_board) == self.opponent_symbol:
                return col
        
        # Use minimax to find best move
        # Adjust depth based on remaining empty cells to stay within time limit
        empty_cells = sum(row.count(' ') for row in board)
        if empty_cells > 30:
            depth = 4  # Early game: shallower search
        elif empty_cells > 15:
            depth = 5  # Mid game: medium search
        else:
            depth = 6  # End game: deeper search
        
        _, best_col = self.minimax(board, depth, -float('inf'), float('inf'), True, start_time)
        
        if best_col is not None:
            return best_col
        
        # Fallback: choose a valid column
        if valid_cols:
            return random.choice(valid_cols)
        else:
            return 0  # Should never happen if game is not over
