"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-coder-next@preset/fp8
Run: 2
Generated: 2026-02-12 14:50:42
"""

import time
from copy import deepcopy
from connect4_engine import Connect4Game

import random
import time
from copy import deepcopy

class Connect4Agent:
    ROWS = 6
    COLS = 7
    EMPTY = ' '
    RED = 'R'
    YELLOW = 'Y'
    WIN_SCORE = 10000
    BLOCK_SCORE = 100
    CENTER_SCORE = 3
    THREAT_SCORE = 50

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = self.YELLOW if symbol == self.RED else self.RED

    def make_move(self, board):
        try:
            start_time = time.time()
            # Ensure timeout safety: cap at 0.95s
            max_time = 0.95

            # Get valid columns
            valid_cols = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
            if not valid_cols:
                return 0  # should not happen, but fallback

            # If only one move, take it
            if len(valid_cols) == 1:
                return valid_cols[0]

            # Try depth-limited minimax with increasing depth (iterative deepening)
            best_col = random.choice(valid_cols)
            depth = 1
            while time.time() - start_time < max_time:
                try:
                    # Use iterative deepening: increase depth until timeout
                    _, best_col = self._minimax(board, depth, -float('inf'), float('inf'), True)
                    depth += 1
                except:
                    break  # ignore internal errors; keep last best_col

            return best_col

        except Exception:
            # Crash fallback: random valid move
            valid_cols = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
            return random.choice(valid_cols) if valid_cols else 0

    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        # Check terminal states
        winner = self._check_winner(board)
        if winner == self.symbol:
            return (self.WIN_SCORE + depth, None)
        elif winner == self.opponent_symbol:
            return (-self.WIN_SCORE - depth, None)
        elif self._is_full(board):
            return (0, None)

        if depth == 0:
            return (self._evaluate_board(board), None)

        valid_cols = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
        if not valid_cols:
            return (0, None)

        if maximizing_player:
            max_eval = -float('inf')
            best_col = valid_cols[0]
            # Order moves: center first, then alternating sides (better pruning)
            sorted_cols = sorted(valid_cols,
                                 key=lambda c: abs(c - self.COLS // 2))
            for col in sorted_cols:
                # Simulate move
                row = self._drop(board, col, self.symbol)
                eval_val, _ = self._minimax(board, depth - 1, alpha, beta, False)
                # Undo move
                board[row][col] = self.EMPTY

                if eval_val > max_eval:
                    max_eval = eval_val
                    best_col = col
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_col

        else:  # minimizing player
            min_eval = float('inf')
            best_col = valid_cols[0]
            sorted_cols = sorted(valid_cols,
                                 key=lambda c: abs(c - self.COLS // 2))
            for col in sorted_cols:
                # Simulate move
                row = self._drop(board, col, self.opponent_symbol)
                eval_val, _ = self._minimax(board, depth - 1, alpha, beta, True)
                # Undo move
                board[row][col] = self.EMPTY

                if eval_val < min_eval:
                    min_eval = eval_val
                    best_col = col
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_col

    def _drop(self, board, col, symbol):
        """Simulate drop and return row index; assumes valid move."""
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                board[r][col] = symbol
                return r
        return -1  # should not happen

    def _check_winner(self, board):
        """Check for 4 in a row."""
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]

        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]

        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]

        return None

    def _is_full(self, board):
        return all(board[0][c] != self.EMPTY for c in range(self.COLS))

    def _evaluate_board(self, board):
        """Heuristic evaluation of board state."""
        score = 0

        # Center column control
        center_col = [board[r][3] for r in range(self.ROWS)]
        center_count = center_col.count(self.symbol)
        score += center_count * self.CENTER_SCORE

        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._evaluate_window(window)

        # Vertical
        for c in range(self.COLS):
            for r in range(self.ROWS - 3):
                window = [board[r+i][c] for i in range(4)]
                score += self._evaluate_window(window)

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window)

        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window)

        return score

    def _evaluate_window(self, window):
        """Evaluate a 4-cell window."""
        score = 0
        opp = self.opponent_symbol
        my = self.symbol

        my_count = window.count(my)
        opp_count = window.count(opp)
        empty = window.count(self.EMPTY)

        if my_count == 4:
            score += self.WIN_SCORE
        elif my_count == 3 and empty == 1:
            score += self.THREAT_SCORE
        elif my_count == 2 and empty == 2:
            score += 10

        if opp_count == 3 and empty == 1:
            score -= self.THREAT_SCORE  # Block opponent's win
        elif opp_count == 4:
            score -= self.WIN_SCORE

        return score
