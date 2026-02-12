"""
Agent Code: A5-Connect4RandomStart
Model: moonshotai/kimi-k2.5
Run: 2
Generated: 2026-02-12 14:50:42
"""



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
        self.rows = 6
        self.cols = 7
    
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
        # Get valid moves (columns that aren't full)
        valid_moves = self._get_valid_moves(board)
        
        if not valid_moves:
            return 0  # Fallback, should not happen during active game
        
        # 1. Check for immediate win
        for col in valid_moves:
            row = self._get_next_open_row(board, col)
            if row != -1:
                board[row][col] = self.symbol
                if self._check_win(board, self.symbol):
                    return col
                board[row][col] = ' '  # Undo
        
        # 2. Check for immediate block (opponent wins next move)
        for col in valid_moves:
            row = self._get_next_open_row(board, col)
            if row != -1:
                board[row][col] = self.opponent
                if self._check_win(board, self.opponent):
                    return col
                board[row][col] = ' '  # Undo
        
        # 3. Use Minimax with Alpha-Beta pruning for strategic play
        # Order moves by center preference for better pruning
        ordered_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
        
        best_col = ordered_moves[0]
        best_score = -float('inf')
        
        # Search depth of 4 provides good balance of strength and speed
        for col in ordered_moves:
            row = self._get_next_open_row(board, col)
            if row == -1:
                continue
            
            board[row][col] = self.symbol
            score = self._minimax(board, 4, -float('inf'), float('inf'), False)
            board[row][col] = ' '
            
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col
    
    def _get_valid_moves(self, board):
        """Return list of columns that are not full."""
        return [c for c in range(self.cols) if board[0][c] == ' ']
    
    def _get_next_open_row(self, board, col):
        """Find the next open row in a column (bottom-up)."""
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return -1
    
    def _check_win(self, board, symbol):
        """Check if the given symbol has won."""
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == symbol and board[r][c+1] == symbol and \
                   board[r][c+2] == symbol and board[r][c+3] == symbol:
                    return True
        
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] == symbol and board[r+1][c] == symbol and \
                   board[r+2][c] == symbol and board[r+3][c] == symbol:
                    return True
        
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == symbol and board[r-1][c+1] == symbol and \
                   board[r-2][c+2] == symbol and board[r-3][c+3] == symbol:
                    return True
        
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] == symbol and board[r+1][c+1] == symbol and \
                   board[r+2][c+2] == symbol and board[r+3][c+3] == symbol:
                    return True
        
        return False
    
    def _evaluate_window(self, window, symbol):
        """Score a window of 4 cells."""
        score = 0
        opp = self.opponent
        
        if window.count(symbol) == 4:
            score += 100
        elif window.count(symbol) == 3 and window.count(' ') == 1:
            score += 5
        elif window.count(symbol) == 2 and window.count(' ') == 2:
            score += 2
        
        # Block opponent's potential wins
        if window.count(opp) == 3 and window.count(' ') == 1:
            score -= 4
        
        return score
    
    def _score_position(self, board, symbol):
        """Heuristic evaluation of board state."""
        score = 0
        
        # Prefer center column (strategic advantage)
        center_col = [board[r][3] for r in range(self.rows)]
        center_count = center_col.count(symbol)
        score += center_count * 3
        
        # Horizontal windows
        for r in range(self.rows):
            row = board[r]
            for c in range(self.cols - 3):
                window = row[c:c+4]
                score += self._evaluate_window(window, symbol)
        
        # Vertical windows
        for c in range(self.cols):
            col = [board[r][c] for r in range(self.rows)]
            for r in range(self.rows - 3):
                window = col[r:r+4]
                score += self._evaluate_window(window, symbol)
        
        # Diagonal / windows
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        
        # Diagonal \ windows
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        
        return score
    
    def _minimax(self, board, depth, alpha, beta, maximizing):
        """
        Minimax algorithm with Alpha-Beta pruning.
        """
        valid_moves = self._get_valid_moves(board)
        
        # Terminal states
        is_terminal = (self._check_win(board, self.symbol) or 
                        self._check_win(board, self.opponent) or 
                        len(valid_moves) == 0)
        
        if depth == 0 or is_terminal:
            if self._check_win(board, self.symbol):
                return 1000000
            elif self._check_win(board, self.opponent):
                return -1000000
            else:
                return self._score_position(board, self.symbol)
        
        if maximizing:
            value = -float('inf')
            ordered = sorted(valid_moves, key=lambda x: abs(x - 3))
            for col in ordered:
                row = self._get_next_open_row(board, col)
                if row == -1:
                    continue
                board[row][col] = self.symbol
                value = max(value, self._minimax(board, depth-1, alpha, beta, False))
                board[row][col] = ' '
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            ordered = sorted(valid_moves, key=lambda x: abs(x - 3))
            for col in ordered:
                row = self._get_next_open_row(board, col)
                if row == -1:
                    continue
                board[row][col] = self.opponent
                value = min(value, self._minimax(board, depth-1, alpha, beta, True))
                board[row][col] = ' '
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value
