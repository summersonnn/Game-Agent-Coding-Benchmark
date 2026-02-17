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
        _, col = self._minimax(board, 4, float('-inf'), float('inf'), True)
        return col

    def _minimax(self, board, depth, alpha, beta, is_max):
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 1000 + depth, None
        if winner == self.opponent:
            return -1000 - depth, None
        if depth == 0:
            return self._evaluate(board), None
        
        valid = [c for c in range(7) if board[0][c] == ' ']
        if not valid:
            return 0, None
        
        best_col = valid[0]
        if is_max:
            max_val = float('-inf')
            for col in valid:
                b = [row[:] for row in board]
                self._drop(b, col, self.symbol)
                val, _ = self._minimax(b, depth - 1, alpha, beta, False)
                if val > max_val:
                    max_val = val
                    best_col = col
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_val, best_col
        else:
            min_val = float('inf')
            for col in valid:
                b = [row[:] for row in board]
                self._drop(b, col, self.opponent)
                val, _ = self._minimax(b, depth - 1, alpha, beta, True)
                if val < min_val:
                    min_val = val
                    best_col = col
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_val, best_col

    def _evaluate(self, board):
        score = 0
        for r in range(6):
            for c in range(7):
                score += self._count_threats(board, r, c, self.symbol) * 10
                score -= self._count_threats(board, r, c, self.opponent) * 10
        return score

    def _count_threats(self, board, r, c, symbol):
        if board[r][c] != symbol:
            return 0
        
        score = 0
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            count = 1
            for i in range(1, 4):
                nr, nc = r + i * dr, c + i * dc
                if 0 <= nr < 6 and 0 <= nc < 7 and board[nr][nc] == symbol:
                    count += 1
                else:
                    break
            
            if count >= 4:
                return 1000
            elif count == 3:
                score += 5
            elif count == 2:
                score += 1
        
        return score

    def _drop(self, board, col, symbol):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return

    def _check_winner(self, board):
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        return None