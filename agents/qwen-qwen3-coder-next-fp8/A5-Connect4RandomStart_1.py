"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-coder-next@preset/fp8
Run: 1
Generated: 2026-02-13 22:27:02
"""

import time
import math

import random
import time
import math

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.start_time = None
        self.max_depth = 6  # Reasonable depth for 1s timeout
        self.nodes_searched = 0

    def make_move(self, board):
        self.start_time = time.time()
        self.nodes_searched = 0
        
        # Get valid columns
        valid_cols = []
        for c in range(7):
            if board[0][c] == ' ':
                valid_cols.append(c)
        
        if not valid_cols:
            return 0  # Should not happen, but fallback
        
        # If first move (only one piece on board and it's opponent's), try center
        # Count non-empty cells to detect early game
        non_empty = sum(1 for row in board for cell in row if cell != ' ')
        if non_empty == 1 and self.symbol == 'Y':
            # First decision move — prefer center (col 3)
            if 3 in valid_cols:
                return 3
        
        # Try iterative deepening with increasing depth
        best_col = random.choice(valid_cols)
        best_score = -math.inf
        
        for depth in range(1, self.max_depth + 1):
            try:
                if time.time() - self.start_time > 0.95:  # Leave margin
                    break
                col, score = self._minimax(board, depth, -math.inf, math.inf, True)
                if col is not None and score > best_score:
                    best_score = score
                    best_col = col
            except Exception:
                break  # Time's up or error
        
        return best_col if best_col in valid_cols else random.choice(valid_cols)

    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        self.nodes_searched += 1
        
        # Time check
        if time.time() - self.start_time > 0.95:
            return None, -math.inf if maximizing_player else math.inf
        
        # Check terminal states
        winner = self._check_winner(board)
        if winner == self.symbol:
            return None, 1000000 + (42 - sum(row.count(' ') for row in board))  # Prefer faster wins
        elif winner == self.opponent_symbol:
            return None, -1000000 - (42 - sum(row.count(' ') for row in board))
        elif all(board[0][c] != ' ' for c in range(7)):
            return None, 0  # Draw
        
        # Depth limit reached
        if depth == 0:
            return None, self._evaluate(board)
        
        # Get valid moves
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        if not valid_cols:
            return None, 0
        
        # Move ordering: prefer center, then columns near center
        def col_score(c):
            return abs(c - 3)
        valid_cols.sort(key=col_score)
        
        if maximizing_player:
            max_eval = -math.inf
            best_col = valid_cols[0]
            for col in valid_cols:
                # Simulate move
                row = self._get_drop_row(board, col)
                board[row][col] = self.symbol
                
                _, eval_score = self._minimax(board, depth - 1, alpha, beta, False)
                
                board[row][col] = ' '  # Undo move
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return best_col, max_eval
        else:
            min_eval = math.inf
            best_col = valid_cols[0]
            for col in valid_cols:
                row = self._get_drop_row(board, col)
                board[row][col] = self.opponent_symbol
                
                _, eval_score = self._minimax(board, depth - 1, alpha, beta, True)
                
                board[row][col] = ' '  # Undo move
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return best_col, min_eval

    def _get_drop_row(self, board, col):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                return r
        return -1

    def _check_winner(self, board):
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        # Vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        return None

    def _evaluate(self, board):
        score = 0
        # Evaluate center column control
        center_count = sum(1 for r in range(6) if board[r][3] == self.symbol)
        score += center_count * 3
        
        # Evaluate all windows of 4
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c+i] for i in range(4)]
                score += self._score_window(window)
        
        # Vertical
        for r in range(3):
            for c in range(7):
                window = [board[r+i][c] for i in range(4)]
                score += self._score_window(window)
        
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._score_window(window)
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._score_window(window)
        
        return score

    def _score_window(self, window):
        count_r = window.count('R')
        count_y = window.count('Y')
        count_empty = window.count(' ')
        
        if self.symbol == 'R':
            my_count = count_r
            opp_count = count_y
        else:
            my_count = count_y
            opp_count = count_r
        
        if my_count == 4:
            return 100
        elif my_count == 3 and count_empty == 1:
            return 5
        elif my_count == 2 and count_empty == 2:
            return 2
        elif opp_count == 3 and count_empty == 1:
            return -4
        elif opp_count == 2 and count_empty == 2:
            return -1
        return 0
