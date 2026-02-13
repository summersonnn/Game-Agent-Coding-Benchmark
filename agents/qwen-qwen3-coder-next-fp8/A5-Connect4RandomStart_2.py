"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-coder-next@preset/fp8
Run: 2
Generated: 2026-02-13 22:27:02
"""

import math
import time

import random
import math
import time

class Connect4Agent:
    ROWS = 6
    COLS = 7
    EMPTY = ' '
    RED = 'R'
    YELLOW = 'Y'
    
    # Evaluation weights for heuristic scoring
    SCORE_WIN = 100000
    SCORE_THREE = 100
    SCORE_TWO = 10
    SCORE_ONE = 1
    
    # For move ordering and time management
    MAX_DEPTH = 5  # Reasonable depth for 1s limit
    TIME_LIMIT = 0.9  # Use 0.9s to leave buffer

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = self.YELLOW if symbol == self.RED else self.RED

    def make_move(self, board):
        start_time = time.time()
        
        # Get valid columns
        valid_cols = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
        if not valid_cols:
            return 0  # Shouldn't happen in practice
        
        # If it's the very first move for Yellow (i.e., only 1 piece on board), 
        # we can use a smart heuristic to pick the center or near-center
        # Count non-empty cells
        total_nonempty = sum(1 for r in range(self.ROWS) for c in range(self.COLS) if board[r][c] != self.EMPTY)
        if total_nonempty == 1 and self.symbol == self.YELLOW:
            # If Red started in center (col 3), play col 2 or 4
            # Find where the red piece is
            red_col = None
            for c in range(self.COLS):
                for r in range(self.ROWS):
                    if board[r][c] == self.RED:
                        red_col = c
                        break
                if red_col is not None:
                    break
            
            if red_col == 3:
                return random.choice([2, 4])
            else:
                # If Red started on edge, play center
                return 3
        
        # Use iterative deepening with alpha-beta pruning
        best_col = random.choice(valid_cols)
        best_score = -math.inf
        
        # Sort moves by heuristics for better pruning
        def move_ordering(col):
            # Make a temporary move to evaluate
            temp_board = [row[:] for row in board]
            for r in range(self.ROWS-1, -1, -1):
                if temp_board[r][col] == self.EMPTY:
                    temp_board[r][col] = self.symbol
                    break
            return self._evaluate_position(temp_board, self.symbol)
        
        # Sort valid columns by heuristic value (descending)
        sorted_cols = sorted(valid_cols, key=move_ordering, reverse=True)
        
        # Try deeper depths until time runs out
        for depth in range(1, self.MAX_DEPTH + 1):
            if time.time() - start_time > self.TIME_LIMIT:
                break
            try:
                col, score = self._minimax(board, depth, -math.inf, math.inf, True, start_time)
                if score > best_score:
                    best_score = score
                    best_col = col
            except:
                # If any error occurs, just keep current best
                pass
        
        return best_col

    def _minimax(self, board, depth, alpha, beta, maximizing, start_time):
        # Check time
        if time.time() - start_time > self.TIME_LIMIT:
            raise TimeoutError("Time limit exceeded")
        
        # Check terminal states
        winner = self._check_winner(board)
        if winner == self.symbol:
            return (None, self.SCORE_WIN)
        elif winner == self.opponent_symbol:
            return (None, -self.SCORE_WIN)
        elif self._is_full(board):
            return (None, 0)
        elif depth == 0:
            return (None, self._evaluate_position(board, self.symbol))
        
        valid_cols = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
        if not valid_cols:
            return (None, 0)
        
        if maximizing:
            max_eval = -math.inf
            best_col = valid_cols[0]
            for col in valid_cols:
                # Make move
                row = self._get_row(board, col)
                board[row][col] = self.symbol
                
                eval_score = self._minimax(board, depth - 1, alpha, beta, False, start_time)[1]
                
                # Undo move
                board[row][col] = self.EMPTY
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return (best_col, max_eval)
        else:
            min_eval = math.inf
            best_col = valid_cols[0]
            for col in valid_cols:
                # Make move
                row = self._get_row(board, col)
                board[row][col] = self.opponent_symbol
                
                eval_score = self._minimax(board, depth - 1, alpha, beta, True, start_time)[1]
                
                # Undo move
                board[row][col] = self.EMPTY
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return (best_col, min_eval)

    def _get_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return -1

    def _check_winner(self, board):
        # Check horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]

        # Check vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]

        # Check diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]

        # Check diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]

        return None

    def _is_full(self, board):
        return all(board[0][c] != self.EMPTY for c in range(self.COLS))

    def _evaluate_position(self, board, player):
        # Heuristic evaluation: score based on potential 4-in-a-rows
        score = 0
        
        # Center column control (more valuable)
        center_count = sum(1 for r in range(self.ROWS) if board[r][3] == player)
        score += center_count * 3
        
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._evaluate_window(window, player)
        
        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                window = [board[r+i][c] for i in range(4)]
                score += self._evaluate_window(window, player)
        
        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window, player)
        
        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window, player)
        
        return score

    def _evaluate_window(self, window, player):
        opponent = self.opponent_symbol
        
        player_count = window.count(player)
        empty_count = window.count(self.EMPTY)
        opponent_count = window.count(opponent)
        
        if player_count == 4:
            return self.SCORE_WIN
        elif player_count == 3 and empty_count == 1:
            return self.SCORE_THREE
        elif player_count == 2 and empty_count == 2:
            return self.SCORE_TWO
        elif player_count == 1 and empty_count == 3:
            return self.SCORE_ONE
        
        # Penalize opponent's potential
        if opponent_count == 3 and empty_count == 1:
            return -self.SCORE_THREE
        elif opponent_count == 2 and empty_count == 2:
            return -self.SCORE_TWO
        
        return 0
