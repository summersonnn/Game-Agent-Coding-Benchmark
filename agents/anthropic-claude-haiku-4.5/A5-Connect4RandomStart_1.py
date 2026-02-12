"""
Agent Code: A5-Connect4RandomStart
Model: anthropic/claude-haiku-4.5
Run: 1
Generated: 2026-02-12 14:50:42
"""



class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
    
    def make_move(self, board):
        """
        Decision-making strategy:
        1. Win immediately if possible
        2. Block opponent's winning move
        3. Use minimax with alpha-beta pruning to find best move
        """
        valid_moves = self._get_valid_moves(board)
        
        if not valid_moves:
            return 0
        
        # Priority 1: Win immediately
        for col in valid_moves:
            if self._is_winning_move(board, col, self.symbol):
                return col
        
        # Priority 2: Block opponent's win
        for col in valid_moves:
            if self._is_winning_move(board, col, self.opponent):
                return col
        
        # Priority 3: Best move via minimax
        best_col = valid_moves[0]
        best_score = float('-inf')
        
        for col in valid_moves:
            board_copy = [row[:] for row in board]
            self._drop_disc(board_copy, col, self.symbol)
            score = self._minimax(board_copy, depth=6, is_maximizing=False)
            
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col
    
    def _get_valid_moves(self, board):
        """Get all valid column indices (not full)"""
        return [c for c in range(7) if board[0][c] == ' ']
    
    def _drop_disc(self, board, col, symbol):
        """Drop disc in column, return landing row or None if full"""
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return r
        return None
    
    def _is_winning_move(self, board, col, symbol):
        """Check if moving in col creates 4-in-a-row for symbol"""
        board_copy = [row[:] for row in board]
        row = self._drop_disc(board_copy, col, symbol)
        return row is not None and self._check_winner(board_copy, row, col, symbol)
    
    def _check_winner(self, board, row, col, symbol):
        """Check if (row, col) completes 4-in-a-row"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # H, V, Diag, Diag
        
        for dr, dc in directions:
            count = 1
            
            # Count in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == symbol:
                count += 1
                r += dr
                c += dc
            
            # Count in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == symbol:
                count += 1
                r -= dr
                c -= dc
            
            if count >= 4:
                return True
        
        return False
    
    def _minimax(self, board, depth, alpha=float('-inf'), beta=float('inf'),
                 is_maximizing=True):
        """Minimax algorithm with alpha-beta pruning"""
        
        # Terminal state: check for winner
        for r in range(6):
            for c in range(7):
                if board[r][c] != ' ' and self._check_winner(board, r, c, board[r][c]):
                    if board[r][c] == self.symbol:
                        return 1000 + depth  # Prefer faster wins
                    else:
                        return -1000 - depth  # Prefer slower losses
        
        # Terminal state: no valid moves (draw)
        valid_moves = self._get_valid_moves(board)
        if not valid_moves:
            return 0
        
        # Terminal state: depth limit reached
        if depth == 0:
            return self._evaluate_board(board)
        
        if is_maximizing:  # My turn (maximize score)
            max_eval = float('-inf')
            for col in valid_moves:
                board_copy = [row[:] for row in board]
                self._drop_disc(board_copy, col, self.symbol)
                value = self._minimax(board_copy, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, value)
                alpha = max(alpha, value)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:  # Opponent's turn (minimize score)
            min_eval = float('inf')
            for col in valid_moves:
                board_copy = [row[:] for row in board]
                self._drop_disc(board_copy, col, self.opponent)
                value = self._minimax(board_copy, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, value)
                beta = min(beta, value)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    def _evaluate_board(self, board):
        """Heuristic evaluation when depth limit reached"""
        score = 0
        
        # Evaluate each piece on board
        for r in range(6):
            for c in range(7):
                if board[r][c] == self.symbol:
                    score += self._evaluate_cell(board, r, c, self.symbol)
                elif board[r][c] == self.opponent:
                    score -= self._evaluate_cell(board, r, c, self.opponent)
        
        return score
    
    def _evaluate_cell(self, board, row, col, symbol):
        """Evaluate value of a single cell"""
        value = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            
            # Count consecutive pieces in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == symbol:
                count += 1
                r += dr
                c += dc
            
            # Count consecutive pieces in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == symbol:
                count += 1
                r -= dr
                c -= dc
            
            # Award points based on line strength
            if count == 3:
                value += 50
            elif count == 2:
                value += 10
            elif count == 1:
                value += 1
        
        # Bonus for center column control
        if col == 3:
            value += 3
        elif col in [2, 4]:
            value += 1
        
        return value
