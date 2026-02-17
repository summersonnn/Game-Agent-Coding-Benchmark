"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3.5-plus-02-15
Run: 2
Generated: 2026-02-16 18:41:52
"""



import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.rows = 6
        self.cols = 7

    def make_move(self, board):
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        if not valid_moves:
            return random.randint(0, self.cols - 1)
        
        # 1. Check for immediate win
        for col in valid_moves:
            r = self._get_next_row(board, col)
            if r is not None and self._check_win_at(board, r, col, self.symbol):
                return col
        
        # 2. Check for immediate block
        for col in valid_moves:
            r = self._get_next_row(board, col)
            if r is not None and self._check_win_at(board, r, col, self.opponent):
                return col
        
        # 3. Minimax with Alpha-Beta Pruning
        best_col = valid_moves[0]
        best_score = -float('inf')
        
        # Order moves by centrality to improve pruning
        valid_moves.sort(key=lambda c: abs(c - 3))
        
        depth = 5
        
        for col in valid_moves:
            r = self._get_next_row(board, col)
            if r is None: continue
            
            # Place disc
            board[r][col] = self.symbol
            
            score = self._minimax(board, depth - 1, -float('inf'), float('inf'), False)
            
            # Undo disc
            board[r][col] = ' '
            
            if score > best_score:
                best_score = score
                best_col = col
                
        return best_col

    def _get_next_row(self, board, col):
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return None

    def _check_win_at(self, board, row, col, symbol):
        # Check 4 directions assuming a piece of 'symbol' is at (row, col)
        # Horizontal
        count = 1
        for c in range(col + 1, min(col + 4, self.cols)):
            if board[row][c] == symbol: count += 1
            else: break
        for c in range(col - 1, max(col - 4, -1), -1):
            if board[row][c] == symbol: count += 1
            else: break
        if count >= 4: return True
        
        # Vertical (only downwards as piece lands on top)
        count = 1
        for r in range(row + 1, min(row + 4, self.rows)):
            if board[r][col] == symbol: count += 1
            else: break
        if count >= 4: return True
        
        # Diagonal \
        count = 1
        for i in range(1, 4):
            if row + i < self.rows and col + i < self.cols and board[row+i][col+i] == symbol: count += 1
            else: break
        for i in range(1, 4):
            if row - i >= 0 and col - i >= 0 and board[row-i][col-i] == symbol: count += 1
            else: break
        if count >= 4: return True
        
        # Diagonal /
        count = 1
        for i in range(1, 4):
            if row - i >= 0 and col + i < self.cols and board[row-i][col+i] == symbol: count += 1
            else: break
        for i in range(1, 4):
            if row + i < self.rows and col - i >= 0 and board[row+i][col-i] == symbol: count += 1
            else: break
        if count >= 4: return True
        
        return False

    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        # Determine who moved last to check for win
        last_symbol = self.opponent if maximizing_player else self.symbol
        
        if self._check_win(board, last_symbol):
            if last_symbol == self.symbol:
                return 100000 + depth
            else:
                return -100000 - depth
        
        if depth == 0:
            return self._evaluate(board)
            
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        if not valid_moves:
            return 0
            
        valid_moves.sort(key=lambda c: abs(c - 3))
        
        if maximizing_player:
            value = -float('inf')
            for col in valid_moves:
                r = self._get_next_row(board, col)
                if r is None: continue
                board[r][col] = self.symbol
                value = max(value, self._minimax(board, depth - 1, alpha, beta, False))
                board[r][col] = ' '
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for col in valid_moves:
                r = self._get_next_row(board, col)
                if r is None: continue
                board[r][col] = self.opponent
                value = min(value, self._minimax(board, depth - 1, alpha, beta, True))
                board[r][col] = ' '
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def _check_win(self, board, symbol):
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
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] == symbol and board[r+1][c+1] == symbol and \
                   board[r+2][c+2] == symbol and board[r+3][c+3] == symbol:
                    return True
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == symbol and board[r-1][c+1] == symbol and \
                   board[r-2][c+2] == symbol and board[r-3][c+3] == symbol:
                    return True
        return False

    def _evaluate(self, board):
        score = 0
        # Center column preference
        center_array = [board[r][3] for r in range(self.rows)]
        score += center_array.count(self.symbol) * 3
        score -= center_array.count(self.opponent) * 3
        
        score += self._score_windows(board, self.symbol)
        score -= self._score_windows(board, self.opponent) * 1.5
        return score

    def _score_windows(self, board, symbol):
        score = 0
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._window_val(window, symbol)
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                window = [board[r+i][c] for i in range(4)]
                score += self._window_val(window, symbol)
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._window_val(window, symbol)
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._window_val(window, symbol)
        return score

    def _window_val(self, window, symbol):
        val = 0
        opp = self.opponent
        count_sym = window.count(symbol)
        count_opp = window.count(opp)
        count_empty = window.count(' ')
        
        if count_sym == 4: val += 100
        elif count_sym == 3 and count_empty == 1: val += 10
        elif count_sym == 2 and count_empty == 2: val += 5
        
        if count_opp == 3 and count_empty == 1: val -= 20
        elif count_opp == 2 and count_empty == 2: val -= 5
        
        return val
