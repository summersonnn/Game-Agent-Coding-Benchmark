"""
Agent Code: A5-Connect4RandomStart
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-14 19:46:39
"""

import time

import time
import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'R' if symbol == 'Y' else 'Y'
        self.rows = 6
        self.cols = 7
        self.start_time = 0
        self.time_limit = 0.85
        
    def make_move(self, board):
        self.start_time = time.time()
        
        valid_cols = [c for c in range(self.cols) if board[0][c] == ' ']
        if not valid_cols:
            return 0
            
        # Check for immediate win
        for c in valid_cols:
            if self.is_winning_move(board, c, self.symbol):
                return c
                
        # Check for opponent's immediate win (block it)
        for c in valid_cols:
            if self.is_winning_move(board, c, self.opponent):
                return c
        
        # Sort by center preference for better alpha-beta pruning
        valid_cols.sort(key=lambda x: abs(x - 3))
        
        best_move = valid_cols[0]
        
        # Iterative deepening search
        for depth in range(1, 7):
            if time.time() - self.start_time > self.time_limit:
                break
                
            current_best = None
            current_best_score = -float('inf')
            
            for c in valid_cols:
                new_board = self.simulate_drop(board, c, self.symbol)
                score = self.minimax(new_board, depth - 1, -float('inf'), float('inf'), False)
                
                if time.time() - self.start_time > self.time_limit:
                    break
                    
                if score > current_best_score:
                    current_best_score = score
                    current_best = c
            
            if current_best is not None and time.time() - self.start_time <= self.time_limit:
                best_move = current_best
        
        return best_move
    
    def get_valid_cols(self, board):
        return [c for c in range(self.cols) if board[0][c] == ' ']
    
    def simulate_drop(self, board, col, symbol):
        new_board = [row[:] for row in board]
        for r in range(self.rows - 1, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = symbol
                break
        return new_board
    
    def is_winning_move(self, board, col, symbol):
        # Find landing row
        row = -1
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                row = r
                break
        if row == -1:
            return False
            
        # Check all four directions
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            # Positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r][c] == symbol:
                count += 1
                r += dr
                c += dc
            # Negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r][c] == symbol:
                count += 1
                r -= dr
                c -= dc
            if count >= 4:
                return True
        return False
    
    def check_winner(self, board):
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        return None
    
    def minimax(self, board, depth, alpha, beta, is_maximizing):
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 1000000
        elif winner == self.opponent:
            return -1000000
        
        valid_cols = self.get_valid_cols(board)
        if not valid_cols or depth == 0:
            return self.evaluate(board)
        
        if is_maximizing:
            max_eval = -float('inf')
            for c in valid_cols:
                new_board = self.simulate_drop(board, c, self.symbol)
                eval = self.minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for c in valid_cols:
                new_board = self.simulate_drop(board, c, self.opponent)
                eval = self.minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    def evaluate(self, board):
        score = 0
        # Center column preference
        for r in range(self.rows):
            if board[r][3] == self.symbol:
                score += 6
            elif board[r][3] == self.opponent:
                score -= 4
        
        # Evaluate windows of 4
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self.eval_window(window)
        
        # Vertical
        for c in range(self.cols):
            for r in range(self.rows - 3):
                window = [board[r+i][c] for i in range(4)]
                score += self.eval_window(window)
        
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.eval_window(window)
        
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.eval_window(window)
        
        return score
    
    def eval_window(self, window):
        my_count = window.count(self.symbol)
        opp_count = window.count(self.opponent)
        empty_count = window.count(' ')
        
        if my_count == 4:
            return 100
        elif my_count == 3 and empty_count == 1:
            return 20
        elif my_count == 2 and empty_count == 2:
            return 5
            
        if opp_count == 3 and empty_count == 1:
            return -15
        elif opp_count == 2 and empty_count == 2:
            return -2
            
        return 0
