"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3.5-397b-a17b
Run: 2
Generated: 2026-02-16 18:16:11
"""



import random

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
        self.max_depth = 5  # Depth limit for minimax to ensure move time < 1s

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        """
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        if not valid_cols:
            return random.randint(0, 6)

        # 1. Check for immediate win
        for col in valid_cols:
            if self._check_winning_move(board, col, self.symbol):
                return col
        
        # 2. Check for immediate block (opponent win)
        for col in valid_cols:
            if self._check_winning_move(board, col, self.opponent_symbol):
                return col

        # 3. Minimax with Alpha-Beta Pruning
        best_score = -float('inf')
        best_col = random.choice(valid_cols)
        
        # Order moves by centrality to improve pruning efficiency
        ordered_cols = sorted(valid_cols, key=lambda c: abs(3 - c))
        
        alpha = -float('inf')
        beta = float('inf')
        
        for col in ordered_cols:
            row = self._get_next_row(board, col)
            if row == -1: continue
            
            # Simulate move
            board[row][col] = self.symbol
            score = self._minimax(board, 1, False, alpha, beta)
            # Backtrack
            board[row][col] = ' '
            
            if score > best_score:
                best_score = score
                best_col = col
            
            alpha = max(alpha, score)
            if beta <= alpha:
                break
                
        return best_col

    def _get_next_row(self, board, col):
        """Find the lowest empty row in a column."""
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                return r
        return -1

    def _check_winning_move(self, board, col, symbol):
        """Check if dropping a disc in col results in a win for symbol."""
        row = self._get_next_row(board, col)
        if row == -1: return False
        board[row][col] = symbol
        win = self._check_win(board, symbol)
        board[row][col] = ' '
        return win

    def _check_win(self, board, symbol):
        """Check if the symbol has 4 in a row."""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if all(board[r][c+i] == symbol for i in range(4)):
                    return True
        # Vertical
        for r in range(3):
            for c in range(7):
                if all(board[r+i][c] == symbol for i in range(4)):
                    return True
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if all(board[r-i][c+i] == symbol for i in range(4)):
                    return True
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if all(board[r+i][c+i] == symbol for i in range(4)):
                    return True
        return False

    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with Alpha-Beta pruning."""
        # Terminal states
        if self._check_win(board, self.symbol):
            return 10000 - depth
        if self._check_win(board, self.opponent_symbol):
            return -10000 + depth
        
        # Draw
        if all(board[0][c] != ' ' for c in range(7)):
            return 0

        # Depth limit
        if depth >= self.max_depth:
            return self._evaluate(board)

        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        # Order moves by centrality
        valid_cols.sort(key=lambda c: abs(3 - c))

        if is_maximizing:
            max_eval = -float('inf')
            for col in valid_cols:
                row = self._get_next_row(board, col)
                if row == -1: continue
                
                board[row][col] = self.symbol
                eval = self._minimax(board, depth + 1, False, alpha, beta)
                board[row][col] = ' '
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_cols:
                row = self._get_next_row(board, col)
                if row == -1: continue

                board[row][col] = self.opponent_symbol
                eval = self._minimax(board, depth + 1, True, alpha, beta)
                board[row][col] = ' '
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, board):
        """Heuristic evaluation of the board state."""
        score = 0
        
        # Center column preference
        for r in range(6):
            if board[r][3] == self.symbol:
                score += 3
            elif board[r][3] == self.opponent_symbol:
                score -= 3
        
        # Evaluate all windows of 4
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c+i] for i in range(4)]
                score += self._evaluate_window(window)
        
        # Vertical
        for c in range(7):
            for r in range(3):
                window = [board[r+i][c] for i in range(4)]
                score += self._evaluate_window(window)
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window)
                
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window)
                
        return score

    def _evaluate_window(self, window):
        """Score a specific window of 4 cells."""
        score = 0
        count_symbol = window.count(self.symbol)
        count_opp = window.count(self.opponent_symbol)
        count_empty = window.count(' ')
        
        if count_symbol == 4:
            score += 1000
        elif count_symbol == 3 and count_empty == 1:
            score += 100
        elif count_symbol == 2 and count_empty == 2:
            score += 10
            
        if count_opp == 3 and count_empty == 1:
            score -= 100
        elif count_opp == 2 and count_empty == 2:
            score -= 10
            
        return score
