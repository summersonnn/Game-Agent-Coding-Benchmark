"""
Agent Code: A5-Connect4RandomStart
Model: anthropic-claude-sonnet-4.5
Run: 2
Generated: 2026-02-12 14:50:42
"""


class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.ROWS = 6
        self.COLS = 7
        
    def make_move(self, board):
        valid_cols = [c for c in range(self.COLS) if board[0][c] == ' ']
        if not valid_cols:
            return 0
        
        for col in valid_cols:
            if self._is_winning_move(board, col, self.symbol):
                return col
        
        for col in valid_cols:
            if self._is_winning_move(board, col, self.opponent):
                return col
        
        _, best_col = self._minimax(board, 6, float('-inf'), float('inf'), True)
        return best_col if best_col is not None else valid_cols[len(valid_cols)//2]
    
    def _minimax(self, board, depth, alpha, beta, maximizing):
        valid_cols = [c for c in range(self.COLS) if board[0][c] == ' ']
        
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 100000, None
        elif winner == self.opponent:
            return -100000, None
        elif not valid_cols or depth == 0:
            return self._evaluate_board(board), None
        
        valid_cols.sort(key=lambda c: abs(c - 3))
        
        if maximizing:
            max_eval = float('-inf')
            best_col = valid_cols[0]
            for col in valid_cols:
                new_board = self._drop_disc(board, col, self.symbol)
                eval_score, _ = self._minimax(new_board, depth - 1, alpha, beta, False)
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
                new_board = self._drop_disc(board, col, self.opponent)
                eval_score, _ = self._minimax(new_board, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_col
    
    def _evaluate_board(self, board):
        score = 0
        
        score += self._score_position(board, self.symbol)
        score -= self._score_position(board, self.opponent)
        
        for c in range(self.COLS):
            if board[0][c] == ' ':
                col_count = sum(1 for r in range(self.ROWS) if board[r][c] == self.symbol)
                score += col_count * (1 if c == 3 else 0.5)
        
        return score
    
    def _score_position(self, board, symbol):
        score = 0
        
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                window = [board[r+i][c] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        
        return score
    
    def _evaluate_window(self, window, symbol):
        opponent = 'Y' if symbol == 'R' else 'R'
        
        count = window.count(symbol)
        empty = window.count(' ')
        opp_count = window.count(opponent)
        
        if count == 4:
            return 100
        elif count == 3 and empty == 1:
            return 10
        elif count == 2 and empty == 2:
            return 5
        elif opp_count > 0:
            return 0
        
        return 0
    
    def _is_winning_move(self, board, col, symbol):
        new_board = self._drop_disc(board, col, symbol)
        return self._check_winner(new_board) == symbol
    
    def _drop_disc(self, board, col, symbol):
        new_board = [row[:] for row in board]
        for r in range(self.ROWS - 1, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = symbol
                break
        return new_board
    
    def _check_winner(self, board):
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        
        return None