"""
Agent Code: A5-Connect4RandomStart
Model: minimax/minimax-m2.1:nitro
Run: 1
Generated: 2026-02-12 13:21:31
"""

import time
import math

import random
import time
import math

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
        
        # Search parameters
        self.max_depth = 5  # Search depth for minimax
        self.time_limit = 0.9  # Leave buffer for overhead
        self.transposition_table = {}  # Cache for evaluated positions
        
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
        start_time = time.time()
        
        # Get valid moves
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return random.randint(0, 6)  # Should not happen, but safety net
        
        # Check for immediate winning move
        for col in valid_moves:
            if self.wins_on_move(board, col, self.symbol):
                return col
        
        # Check for immediate blocking move (opponent would win next)
        for col in valid_moves:
            if self.wins_on_move(board, col, self.opponent_symbol):
                return col
        
        # Use minimax with iterative deepening
        best_move = valid_moves[0]
        alpha = -math.inf
        beta = math.inf
        
        for depth in range(1, self.max_depth + 1):
            if time.time() - start_time > self.time_limit:
                break
                
            self.transposition_table.clear()  # Clear cache at each depth
            
            _, best_move = self.minimax(
                board, depth, alpha, beta, True, 
                start_time, valid_moves
            )
        
        return best_move
    
    def get_valid_moves(self, board):
        """Return list of columns that are not full."""
        valid = []
        for col in range(7):
            if board[0][col] == ' ':
                valid.append(col)
        return valid
    
    def get_row_to_drop(self, board, col):
        """Find the row where a disc would land in the given column."""
        for row in range(5, -1, -1):
            if board[row][col] == ' ':
                return row
        return -1  # Column is full
    
    def wins_on_move(self, board, col, symbol):
        """Check if dropping in column wins the game."""
        row = self.get_row_to_drop(board, col)
        if row == -1:
            return False
        
        # Temporarily place the disc
        board[row][col] = symbol
        wins = self.check_winner(board) == symbol
        board[row][col] = ' '  # Restore
        
        return wins
    
    def check_winner(self, board):
        """Check for 4 in a row. Returns winning symbol or None."""
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
    
    def is_full(self, board):
        """Check if board is full."""
        return all(board[0][c] != ' ' for c in range(7))
    
    def minimax(self, board, depth, alpha, beta, maximizing_player, start_time, valid_moves):
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            board: Current board state
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing_player: True if maximizing (our turn)
            start_time: Time when move calculation started
            valid_moves: List of valid column moves
            
        Returns:
            (score, best_column)
        """
        # Check for terminal states
        winner = self.check_winner(board)
        if winner == self.symbol:
            return (10000 + self.count_total_discs(board), None)
        elif winner == self.opponent_symbol:
            return (-10000 - self.count_total_discs(board), None)
        elif self.is_full(board):
            return (0, None)
        
        # Time check
        if time.time() - start_time > self.time_limit:
            return (self.evaluate_board(board), None)
        
        # Generate valid moves for current state
        current_valid_moves = self.get_valid_moves(board)
        if not current_valid_moves:
            return (0, None)
        
        # Order moves for better pruning (center first)
        current_valid_moves.sort(key=lambda x: abs(3 - x))
        
        # Hash position for transposition table
        board_hash = self.hash_board(board)
        if board_hash in self.transposition_table and depth <= 3:
            cached_score, cached_move = self.transposition_table[board_hash]
            return (cached_score, cached_move)
        
        if maximizing_player:
            max_eval = -math.inf
            best_move = current_valid_moves[0]
            
            for col in current_valid_moves:
                row = self.get_row_to_drop(board, col)
                board[row][col] = self.symbol
                
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, False, start_time, valid_moves)
                
                board[row][col] = ' '
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = col
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            # Cache the result
            if depth <= 3:
                self.transposition_table[board_hash] = (max_eval, best_move)
            
            return (max_eval, best_move)
        
        else:
            min_eval = math.inf
            best_move = current_valid_moves[0]
            
            for col in current_valid_moves:
                row = self.get_row_to_drop(board, col)
                board[row][col] = self.opponent_symbol
                
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, True, start_time, valid_moves)
                
                board[row][col] = ' '
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = col
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            # Cache the result
            if depth <= 3:
                self.transposition_table[board_hash] = (min_eval, best_move)
            
            return (min_eval, best_move)
    
    def evaluate_board(self, board):
        """
        Evaluate board position using multiple heuristics.
        Higher score = better for current player.
        """
        score = 0
        
        # Center column preference
        center_col = 3
        center_count = sum(1 for r in range(6) if board[r][center_col] == self.symbol)
        score += center_count * 3
        
        # Evaluate all possible 4-disc windows
        score += self.evaluate_windows(board, self.symbol) * 1
        score -= self.evaluate_windows(board, self.opponent_symbol) * 1.1
        
        # Prefer positions with more connections
        score += self.count_threats(board, self.symbol) * 5
        score -= self.count_threats(board, self.opponent_symbol) * 6
        
        return score
    
    def evaluate_windows(self, board, symbol):
        """Evaluate all 4-disc windows for a given symbol."""
        score = 0
        windows = self.get_all_windows(board)
        
        for window in windows:
            count = window.count(symbol)
            empty = window.count(' ')
            
            if count == 4:
                score += 100
            elif count == 3 and empty == 1:
                score += 5
            elif count == 2 and empty == 2:
                score += 2
        
        return score
    
    def get_all_windows(self, board):
        """Generate all possible 4-disc windows (horizontal, vertical, diagonal)."""
        windows = []
        
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c+i] for i in range(4)]
                windows.append(window)
        
        # Vertical
        for r in range(3):
            for c in range(7):
                window = [board[r+i][c] for i in range(4)]
                windows.append(window)
        
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                windows.append(window)
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                windows.append(window)
        
        return windows
    
    def count_threats(self, board, symbol):
        """
        Count potential winning threats (3 in a row with empty space).
        These are positions that need to be blocked or completed.
        """
        threats = 0
        windows = self.get_all_windows(board)
        
        for window in windows:
            if window.count(symbol) == 3 and window.count(' ') == 1:
                threats += 1
        
        return threats
    
    def count_total_discs(self, board):
        """Count total discs on board (for depth bonus in terminal evaluation)."""
        return sum(row.count(self.symbol) + row.count(self.opponent_symbol) for row in board)
    
    def hash_board(self, board):
        """Create a simple hash of the board for transposition table."""
        hash_val = 0
        for r in range(6):
            for c in range(7):
                val = 0 if board[r][c] == ' ' else (1 if board[r][c] == self.symbol else 2)
                hash_val = hash_val * 3 + val
        return hash_val
