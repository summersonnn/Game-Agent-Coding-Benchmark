"""
Agent Code: A5-Connect4RandomStart
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 22:26:38
"""

import copy

import random
import copy

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.depth = 5  # Search depth
    
    def make_move(self, board):
        # Get valid columns (not full)
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        
        if not valid_cols:
            return 0
        
        # If only one valid move, take it
        if len(valid_cols) == 1:
            return valid_cols[0]
        
        # Determine opponent symbol
        opponent = 'Y' if self.symbol == 'R' else 'R'
        
        # Use iterative deepening minimax
        best_col = valid_cols[0]
        best_score = float('-inf')
        
        # Order moves: center first, then expanding outward
        valid_cols.sort(key=lambda x: abs(x - 3))
        
        for col in valid_cols:
            # Make move
            new_board = self.drop_disc(board, col, self.symbol)
            
            # Check if this move wins immediately
            if self.check_win(new_board, self.symbol):
                return col
            
            # Check if opponent wins next (must block)
            for opp_col in range(7):
                if new_board[0][opp_col] == ' ':
                    opp_board = self.drop_disc(new_board, opp_col, opponent)
                    if self.check_win(opp_board, opponent):
                        # Must block this
                        best_col = col
                        best_score = float('inf')
                        break
            else:
                # Not an immediate block, do full evaluation
                score = self.minimax(new_board, self.depth - 1, float('-inf'), float('inf'), False, opponent)
                
                if score > best_score:
                    best_score = score
                    best_col = col
        
        return best_col
    
    def drop_disc(self, board, col, disc):
        """Return a new board with disc dropped in column"""
        new_board = [row[:] for row in board]
        
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = disc
                return new_board
        
        return new_board  # Column full (shouldn't happen)
    
    def check_win(self, board, disc):
        """Check if disc has won"""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3] == disc:
                    return True
        
        # Vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c] == disc:
                    return True
        
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3] == disc:
                    return True
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3] == disc:
                    return True
        
        return False
    
    def check_terminal(self, board):
        """Check if board is terminal (win or draw)"""
        if self.check_win(board, self.symbol):
            return True
        if self.check_win(board, 'Y' if self.symbol == 'R' else 'R'):
            return True
        return all(board[0][c] != ' ' for c in range(7))
    
    def evaluate_window(self, window, disc):
        """Evaluate a window of 4 cells"""
        score = 0
        opp_disc = 'Y' if disc == 'R' else 'R'
        
        count_disc = window.count(disc)
        count_opp = window.count(opp_disc)
        count_empty = window.count(' ')
        
        # Winning line
        if count_disc == 4:
            score += 100
        # Three with open end
        elif count_disc == 3 and count_empty == 1:
            score += 5
        # Two with open ends
        elif count_disc == 2 and count_empty == 2:
            score += 2
        
        # Block opponent's three
        if count_opp == 3 and count_empty == 1:
            score -= 4
        # Block opponent's two
        elif count_opp == 2 and count_empty == 2:
            score -= 1
        
        return score
    
    def evaluate_board(self, board, disc):
        """Evaluate entire board"""
        score = 0
        
        # Center column preference
        center_col = 3
        center_count = sum(1 for r in range(6) if board[r][center_col] == disc)
        score += center_count * 3
        
        # Horizontal windows
        for r in range(6):
            for c in range(4):
                window = [board[r][c+i] for i in range(4)]
                score += self.evaluate_window(window, disc)
        
        # Vertical windows
        for r in range(3):
            for c in range(7):
                window = [board[r+i][c] for i in range(4)]
                score += self.evaluate_window(window, disc)
        
        # Diagonal / windows
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, disc)
        
        # Diagonal \ windows
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, disc)
        
        return score
    
    def minimax(self, board, depth, alpha, beta, maximizing, disc):
        """Minimax with alpha-beta pruning"""
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        
        # Terminal states
        if depth == 0 or self.check_terminal(board):
            if self.check_win(board, self.symbol):
                return float('inf')
            if self.check_win(board, 'Y' if self.symbol == 'R' else 'R'):
                return float('-inf')
            if all(board[0][c] != ' ' for c in range(7)):
                return 0
            return self.evaluate_board(board, self.symbol)
        
        if maximizing:
            max_eval = float('-inf')
            for col in valid_cols:
                new_board = self.drop_disc(board, col, disc)
                eval_score = self.minimax(new_board, depth - 1, alpha, beta, False, 
                                         'Y' if disc == 'R' else 'R')
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_cols:
                new_board = self.drop_disc(board, col, disc)
                eval_score = self.minimax(new_board, depth - 1, alpha, beta, True,
                                         'Y' if disc == 'R' else 'R')
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
