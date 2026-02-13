"""
Agent Code: A5-Connect4RandomStart
Model: anthropic-claude-sonnet-4.5
Run: 1
Generated: 2026-02-12 14:50:42
"""


class Connect4Agent:
    ROWS = 6
    COLS = 7
    EMPTY = ' '
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        
    def make_move(self, board):
        valid_cols = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
        
        for col in valid_cols:
            if self._creates_win(board, col, self.symbol):
                return col
        
        for col in valid_cols:
            if self._creates_win(board, col, self.opponent):
                return col
        
        _, best_col = self._minimax(board, 6, float('-inf'), float('inf'), True)
        return best_col if best_col is not None else valid_cols[len(valid_cols)//2]
    
    def _creates_win(self, board, col, symbol):
        row = self._get_drop_row(board, col)
        if row is None:
            return False
        board[row][col] = symbol
        wins = self._check_win_at(board, row, col, symbol)
        board[row][col] = self.EMPTY
        return wins
    
    def _get_drop_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return None
    
    def _minimax(self, board, depth, alpha, beta, maximizing):
        valid_cols = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
        
        if depth == 0 or not valid_cols:
            return self._evaluate(board), None
        
        valid_cols.sort(key=lambda c: abs(c - 3))
        
        if maximizing:
            max_eval = float('-inf')
            best_col = valid_cols[0]
            for col in valid_cols:
                row = self._get_drop_row(board, col)
                board[row][col] = self.symbol
                
                if self._check_win_at(board, row, col, self.symbol):
                    board[row][col] = self.EMPTY
                    return 100000, col
                
                eval_score, _ = self._minimax(board, depth - 1, alpha, beta, False)
                board[row][col] = self.EMPTY
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_col
        else:
            min_eval = float('inf')
            best_col = valid_cols[0]
            for col in valid_cols:
                row = self._get_drop_row(board, col)
                board[row][col] = self.opponent
                
                if self._check_win_at(board, row, col, self.opponent):
                    board[row][col] = self.EMPTY
                    return -100000, col
                
                eval_score, _ = self._minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = self.EMPTY
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_col
    
    def _evaluate(self, board):
        score = 0
        score += self._score_position(board, self.symbol)
        score -= self._score_position(board, self.opponent)
        return score
    
    def _score_position(self, board, symbol):
        score = 0
        
        center_col = [board[r][3] for r in range(self.ROWS)]
        score += center_col.count(symbol) * 3
        
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._score_window(window, symbol)
        
        for c in range(self.COLS):
            for r in range(self.ROWS - 3):
                window = [board[r+i][c] for i in range(4)]
                score += self._score_window(window, symbol)
        
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._score_window(window, symbol)
        
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._score_window(window, symbol)
        
        return score
    
    def _score_window(self, window, symbol):
        opponent = 'Y' if symbol == 'R' else 'R'
        score = 0
        
        if window.count(symbol) == 4:
            score += 100
        elif window.count(symbol) == 3 and window.count(self.EMPTY) == 1:
            score += 5
        elif window.count(symbol) == 2 and window.count(self.EMPTY) == 2:
            score += 2
        
        if window.count(opponent) == 3 and window.count(self.EMPTY) == 1:
            score -= 4
        
        return score
    
    def _check_win_at(self, board, row, col, symbol):
        directions = [(0,1), (1,0), (1,1), (1,-1)]
        
        for dr, dc in directions:
            count = 1
            for direction in [1, -1]:
                r, c = row + dr * direction, col + dc * direction
                while 0 <= r < self.ROWS and 0 <= c < self.COLS and board[r][c] == symbol:
                    count += 1
                    r += dr * direction
                    c += dc * direction
            if count >= 4:
                return True
        return False