"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-coder-next@preset/fp8
Run: 1
Generated: 2026-02-12 14:50:42
"""

import time
import math
from connect4_engine import Connect4Game  # assuming engine code saved as connect4_engine.py

import time
import random
import math

class Connect4Agent:
    ROWS = 6
    COLS = 7
    EMPTY = ' '
    RED = 'R'
    YELLOW = 'Y'
    TIMEOUT_THRESHOLD = 0.9  # seconds before actual timeout (safety margin)

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = self.YELLOW if symbol == self.RED else self.RED
        # Precomputed weights for heuristic scoring (center preference)
        self.center_weights = [3, 4, 5, 7, 5, 4, 3]  # column value for position bias

    def make_move(self, board):
        """Return best move using depth-limited minimax with alpha-beta & time limit."""
        start_time = time.time()

        # First, check for immediate win or block (fast path)
        for col in range(self.COLS):
            # Simulate drop in this column
            if self._is_valid(board, col):
                # Try placing move
                row = self._get_next_open_row(board, col)
                board[row][col] = self.symbol
                if self._check_win_at(board, row, col, self.symbol):
                    # Restore board before returning
                    board[row][col] = self.EMPTY
                    return col
                board[row][col] = self.EMPTY

        # Also check if opponent has immediate win (block it)
        for col in range(self.COLS):
            if self._is_valid(board, col):
                row = self._get_next_open_row(board, col)
                board[row][col] = self.opponent_symbol
                if self._check_win_at(board, row, col, self.opponent_symbol):
                    board[row][col] = self.EMPTY
                    return col
                board[row][col] = self.EMPTY

        # If no immediate win/block, use minimax (with time limit)
        try:
            best_col = self._minimax(board, depth=4, alpha=-math.inf, beta=math.inf, maximizing_player=True, start_time=start_time)
            if best_col is not None and self._is_valid(board, best_col):
                return best_col
        except TimeoutError:
            pass  # Fall back to heuristic

        # Last resort: heuristic-based best move
        return self._best_heuristic_move(board)

    def _is_valid(self, board, col):
        """Check if column is not full."""
        return 0 <= col < self.COLS and board[0][col] == self.EMPTY

    def _get_next_open_row(self, board, col):
        """Find lowest empty row in column."""
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return -1

    def _check_win_at(self, board, row, col, symbol):
        """Check if placing at (row, col) with symbol creates 4-in-a-row."""
        # Horizontal
        count = 1
        # left
        c = col - 1
        while c >= 0 and board[row][c] == symbol:
            count += 1
            c -= 1
        # right
        c = col + 1
        while c < self.COLS and board[row][c] == symbol:
            count += 1
            c += 1
        if count >= 4:
            return True

        # Vertical
        count = 1
        r = row - 1
        while r >= 0 and board[r][col] == symbol:
            count += 1
            r -= 1
        if count >= 4:
            return True

        # Diagonal /
        count = 1
        r, c = row - 1, col + 1
        while r >= 0 and c < self.COLS and board[r][c] == symbol:
            count += 1
            r -= 1
            c += 1
        r, c = row + 1, col - 1
        while r < self.ROWS and c >= 0 and board[r][c] == symbol:
            count += 1
            r += 1
            c -= 1
        if count >= 4:
            return True

        # Diagonal \
        count = 1
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and board[r][c] == symbol:
            count += 1
            r -= 1
            c -= 1
        r, c = row + 1, col + 1
        while r < self.ROWS and c < self.COLS and board[r][c] == symbol:
            count += 1
            r += 1
            c += 1
        if count >= 4:
            return True

        return False

    def _minimax(self, board, depth, alpha, beta, maximizing_player, start_time):
        # Time check
        if time.time() - start_time > self.TIMEOUT_THRESHOLD:
            raise TimeoutError("Time limit exceeded")

        valid_cols = [c for c in range(self.COLS) if self._is_valid(board, c)]
        if not valid_cols:
            return None  # draw

        # Terminal check: win/loss/draw
        # For speed, we approximate win/loss by checking if any move wins *now*
        # But better: check full board state
        if depth == 0 or self._is_terminal(board):
            return self._evaluate_board(board)

        if maximizing_player:
            value = -math.inf
            best_col = random.choice(valid_cols)
            # Move ordering: prefer center
            valid_cols.sort(key=lambda c: abs(c - 3))
            for col in valid_cols:
                row = self._get_next_open_row(board, col)
                board[row][col] = self.symbol
                # Check if this move wins (prune early)
                if self._check_win_at(board, row, col, self.symbol):
                    board[row][col] = self.EMPTY
                    return col  # immediate win

                result = self._minimax(board, depth - 1, alpha, beta, False, start_time)
                # If result is a column index (i.e., terminal win), return it
                if isinstance(result, int):
                    board[row][col] = self.EMPTY
                    return result
                board[row][col] = self.EMPTY

                if isinstance(result, (int, float)) and result > value:
                    value = result
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col
        else:
            value = math.inf
            best_col = random.choice(valid_cols)
            valid_cols.sort(key=lambda c: abs(c - 3))
            for col in valid_cols:
                row = self._get_next_open_row(board, col)
                board[row][col] = self.opponent_symbol
                if self._check_win_at(board, row, col, self.opponent_symbol):
                    board[row][col] = self.EMPTY
                    return col  # opponent wins → we want to avoid, but return move for engine to play

                result = self._minimax(board, depth - 1, alpha, beta, True, start_time)
                if isinstance(result, int):
                    board[row][col] = self.EMPTY
                    return result
                board[row][col] = self.EMPTY

                if isinstance(result, (int, float)) and result < value:
                    value = result
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col

    def _is_terminal(self, board):
        # Check if game is over (win or full)
        # Fast path: only check win for last move? Too slow. Just check win for both.
        # Instead, use heuristic: if board full or someone has 4-in-a-row (but expensive)
        # Simplify: we only call this when depth=0, so skip full check here.
        return self._is_full(board)

    def _is_full(self, board):
        return all(board[0][c] != self.EMPTY for c in range(self.COLS))

    def _evaluate_board(self, board):
        """Heuristic evaluation of board state."""
        score = 0

        # Center column control
        center_count = sum(1 for r in range(self.ROWS) if board[r][3] == self.symbol)
        center_opp = sum(1 for r in range(self.ROWS) if board[r][3] == self.opponent_symbol)
        score += center_count * 3 - center_opp * 3

        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r][c + i] for i in range(4)]
                score += self._score_window(window)

        # Vertical
        for c in range(self.COLS):
            for r in range(self.ROWS - 3):
                window = [board[r + i][c] for i in range(4)]
                score += self._score_window(window)

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += self._score_window(window)

        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += self._score_window(window)

        return score

    def _score_window(self, window):
        """Score a 4-cell window."""
        my_count = window.count(self.symbol)
        opp_count = window.count(self.opponent_symbol)
        empty = window.count(self.EMPTY)

        if my_count == 4:
            return 100
        elif my_count == 3 and empty == 1:
            return 5
        elif my_count == 2 and empty == 2:
            return 2
        elif opp_count == 3 and empty == 1:
            return -4  # Block opponent's 3-in-a-row
        elif opp_count == 2 and empty == 2:
            return -1
        return 0

    def _best_heuristic_move(self, board):
        """Fallback: pick best column by heuristic (no search)."""
        best_score = -math.inf
        best_cols = []

        for col in range(self.COLS):
            if not self._is_valid(board, col):
                continue
            row = self._get_next_open_row(board, col)
            board[row][col] = self.symbol
            # Evaluate board after move
            score = self._evaluate_board(board)
            board[row][col] = self.EMPTY

            # Prefer center in tie
            score += self.center_weights[col] * 0.1

            if score > best_score:
                best_score = score
                best_cols = [col]
            elif score == best_score:
                best_cols.append(col)

        return random.choice(best_cols) if best_cols else random.choice([c for c in range(self.COLS) if self._is_valid(board, c)])
