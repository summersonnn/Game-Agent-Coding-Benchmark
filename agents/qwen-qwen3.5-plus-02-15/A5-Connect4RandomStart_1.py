"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3.5-plus-02-15
Run: 1
Generated: 2026-02-16 18:41:52
"""

import time

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.rows = 6
        self.cols = 7
        # Prefer center columns for better heuristic value and pruning
        self.col_order = [3, 2, 4, 1, 5, 0, 6]

    def make_move(self, board):
        # Identify valid columns based on current board state
        valid_cols = [c for c in self.col_order if board[0][c] == ' ']
        
        if not valid_cols:
            return 3 # Fallback if board is full (should be handled by engine)

        start_time = time.time()
        time_limit = 0.95 # Leave margin for 1s timeout
        
        best_col = valid_cols[0]
        best_score = -float('inf')
        
        # Iterative Deepening: Increase depth until time runs out
        # Max depth 6 is generally safe for 1s in Python with Alpha-Beta
        for depth in range(1, 7):
            current_best_col = valid_cols[0]
            current_best_score = -float('inf')
            timeout = False
            
            for col in valid_cols:
                # Check time before processing each move
                if time.time() - start_time > time_limit:
                    timeout = True
                    break
                
                row = self._get_next_open_row(board, col)
                # Simulate move
                board[row][col] = self.symbol
                # Search
                score = self._minimax(board, depth - 1, -float('inf'), float('inf'), False, start_time, time_limit, col, row)
                # Undo move
                board[row][col] = ' '
                
                if score > current_best_score:
                    current_best_score = score
                    current_best_col = col
            
            # If we timed out during this depth, stop and use best from previous completed depth
            if timeout:
                break
            
            # Update best move if this depth completed successfully
            best_col = current_best_col
            best_score = current_best_score
            
        return best_col

    def _get_next_open_row(self, board, col):
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return None

    def _minimax(self, board, depth, alpha, beta, maximizing_player, start_time, time_limit, last_col, last_row):
        # Time Check
        if time.time() - start_time > time_limit:
            return 0
        
        # Check terminal states (Win/Loss)
        # Optimized to check only around the last move made
        if self._check_win_at(board, self.symbol, last_row, last_col):
            return 100000 + depth # Prefer faster wins
        if self._check_win_at(board, self.opponent, last_row, last_col):
            return -100000 - depth # Prefer slower losses
            
        valid_cols = [c for c in self.col_order if board[0][c] == ' ']
        
        if not valid_cols:
            return 0 # Draw
        
        if depth == 0:
            return self._evaluate(board)
        
        if maximizing_player:
            value = -float('inf')
            for col in valid_cols:
                row = self._get_next_open_row(board, col)
                board[row][col] = self.symbol
                score = self._minimax(board, depth - 1, alpha, beta, False, start_time, time_limit, col, row)
                board[row][col] = ' '
                value = max(value, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            for col in valid_cols:
                row = self._get_next_open_row(board, col)
                board[row][col] = self.opponent
                score = self._minimax(board, depth - 1, alpha, beta, True, start_time, time_limit, col, row)
                board[row][col] = ' '
                value = min(value, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return value

    def _check_win_at(self, board, disc, row, col):
        if row is None or col is None:
            return False
        
        # Horizontal
        count = 0
        for c in range(col - 3, col + 4):
            if 0 <= c < self.cols and board[row][c] == disc:
                count += 1
            else:
                count = 0
            if count >= 4:
                return True
        
        # Vertical
        count = 0
        for r in range(row - 3, row + 4):
            if 0 <= r < self.rows and board[r][col] == disc:
                count += 1
            else:
                count = 0
            if count >= 4:
                return True
        
        # Diagonal \
        count = 0
        for i in range(-3, 4):
            r, c = row + i, col + i
            if 0 <= r < self.rows and 0 <= c < self.cols and board[r][c] == disc:
                count += 1
            else:
                count = 0
            if count >= 4:
                return True
        
        # Diagonal /
        count = 0
        for i in range(-3, 4):
            r, c = row - i, col + i
            if 0 <= r < self.rows and 0 <= c < self.cols and board[r][c] == disc:
                count += 1
            else:
                count = 0
            if count >= 4:
                return True
                
        return False

    def _evaluate(self, board):
        score = 0
        # Center column preference
        for r in range(self.rows):
            if board[r][3] == self.symbol:
                score += 5
            elif board[r][3] == self.opponent:
                score -= 5
        
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._score_window(window)
        
        # Vertical
        for c in range(self.cols):
            for r in range(self.rows - 3):
                window = [board[r+i][c] for i in range(4)]
                score += self._score_window(window)
        
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._score_window(window)
        
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._score_window(window)
        
        return score

    def _score_window(self, window):
        score = 0
        my_count = window.count(self.symbol)
        opp_count = window.count(self.opponent)
        empty_count = window.count(' ')
        
        if my_count == 4:
            score += 100
        elif my_count == 3 and empty_count == 1:
            score += 10
        elif my_count == 2 and empty_count == 2:
            score += 5
        
        if opp_count == 3 and empty_count == 1:
            score -= 20
        elif opp_count == 4:
            score -= 100
            
        return score