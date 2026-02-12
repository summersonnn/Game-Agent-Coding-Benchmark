"""
Agent Code: A5-Connect4RandomStart
Model: moonshotai/kimi-k2.5
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
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.time_limit = 0.9  # 900ms to ensure we don't timeout
        self.start_time = None
        
    def make_move(self, board):
        """
        Decide the next move based on the current board state using iterative deepening
        minimax with alpha-beta pruning.
        
        Args:
            board: A list of lists representing the 6x7 grid.
                   board[row][col] contains 'R', 'Y', or ' ' (empty).
                   Row 0 is the top, Row 5 is the bottom.
                   
        Returns:
            int: The column index (0-6) where the agent wants to drop a disc.
        """
        try:
            self.start_time = time.time()
            valid_moves = self._get_valid_moves(board)
            
            if not valid_moves:
                return random.randint(0, 6)
            
            # Check for immediate win
            for col in valid_moves:
                if self._is_winning_move(board, col, self.symbol):
                    return col
            
            # Check for immediate block (opponent win)
            for col in valid_moves:
                if self._is_winning_move(board, col, self.opponent):
                    return col
            
            # Iterative deepening search
            best_move = valid_moves[len(valid_moves) // 2]  # Default to center-ish
            depth = 1
            max_depth = 42  # Maximum possible moves
            
            while depth <= max_depth:
                if time.time() - self.start_time > self.time_limit:
                    break
                
                move, score = self._minimax(board, depth, float('-inf'), float('inf'), True)
                if move is not None:
                    best_move = move
                depth += 1
            
            return best_move
            
        except Exception:
            # Fallback to random valid move on any error
            valid_moves = [c for c in range(7) if board[0][c] == ' ']
            return random.choice(valid_moves) if valid_moves else 0
    
    def _get_valid_moves(self, board):
        """Return list of columns that are not full."""
        return [c for c in range(7) if board[0][c] == ' ']
    
    def _get_next_open_row(self, board, col):
        """Find the lowest empty row in a column."""
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                return r
        return None
    
    def _is_winning_move(self, board, col, symbol):
        """Check if dropping a piece in col results in a win for symbol."""
        row = self._get_next_open_row(board, col)
        if row is None:
            return False
        
        board[row][col] = symbol
        win = self._check_win_at(board, row, col, symbol)
        board[row][col] = ' '
        return win
    
    def _check_win_at(self, board, row, col, symbol):
        """Check if there's a 4-in-a-row through (row, col)."""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            
            # Check positive direction
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == symbol:
                count += 1
                r += dr
                c += dc
            
            # Check negative direction
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == symbol:
                count += 1
                r -= dr
                c -= dc
            
            if count >= 4:
                return True
        
        return False
    
    def _minimax(self, board, depth, alpha, beta, maximizing):
        """
        Minimax algorithm with alpha-beta pruning.
        Returns (best_move, score)
        """
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError()
        
        valid_moves = self._get_valid_moves(board)
        
        # Terminal state checks
        if len(valid_moves) == 0:
            return (None, 0)  # Draw
        
        score = self._evaluate(board)
        if abs(score) > 9000:  # Someone has won
            return (None, score)
        
        if depth == 0:
            return (None, score)
        
        # Move ordering: prioritize center columns for better pruning
        ordered_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
        
        if maximizing:
            value = float('-inf')
            best_move = None
            
            for col in ordered_moves:
                row = self._get_next_open_row(board, col)
                if row is None:
                    continue
                
                board[row][col] = self.symbol
                _, new_score = self._minimax(board, depth - 1, alpha, beta, False)
                board[row][col] = ' '
                
                if new_score > value:
                    value = new_score
                    best_move = col
                
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            
            return (best_move, value)
        else:
            value = float('inf')
            best_move = None
            
            for col in ordered_moves:
                row = self._get_next_open_row(board, col)
                if row is None:
                    continue
                
                board[row][col] = self.opponent
                _, new_score = self._minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = ' '
                
                if new_score < value:
                    value = new_score
                    best_move = col
                
                beta = min(beta, value)
                if alpha >= beta:
                    break
            
            return (best_move, value)
    
    def _evaluate(self, board):
        """
        Heuristic evaluation of the board.
        Positive scores favor the agent, negative favor the opponent.
        """
        score = 0
        
        # Center column control (column 3 is most valuable)
        center_col = 3
        center_count = sum(1 for r in range(6) if board[r][center_col] == self.symbol)
        score += center_count * 6
        
        opp_center_count = sum(1 for r in range(6) if board[r][center_col] == self.opponent)
        score -= opp_center_count * 6
        
        # Evaluate all possible windows of 4 cells
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c + i] for i in range(4)]
                score += self._evaluate_window(window)
        
        # Vertical
        for r in range(3):
            for c in range(7):
                window = [board[r + i][c] for i in range(4)]
                score += self._evaluate_window(window)
        
        # Diagonal / (up-right)
        for r in range(3, 6):
            for c in range(4):
                window = [board[r - i][c + i] for i in range(4)]
                score += self._evaluate_window(window)
        
        # Diagonal \ (down-right)
        for r in range(3):
            for c in range(4):
                window = [board[r + i][c + i] for i in range(4)]
                score += self._evaluate_window(window)
        
        return score
    
    def _evaluate_window(self, window):
        """Score a single window of 4 cells."""
        score = 0
        my_count = window.count(self.symbol)
        opp_count = window.count(self.opponent)
        empty_count = window.count(' ')
        
        # Scoring based on piece counts
        if my_count == 4:
            score += 100000  # Win
        elif my_count == 3 and empty_count == 1:
            score += 100     # Strong threat
        elif my_count == 2 and empty_count == 2:
            score += 10      # Potential threat
        elif my_count == 1 and empty_count == 3:
            score += 1       # Weak potential
        
        if opp_count == 4:
            score -= 100000  # Loss (block needed)
        elif opp_count == 3 and empty_count == 1:
            score -= 100     # Urgent block needed
        elif opp_count == 2 and empty_count == 2:
            score -= 10      # Block potential
        elif opp_count == 1 and empty_count == 3:
            score -= 1       # Weak block
        
        return score
