"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-14 19:46:39
"""

import time

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        name: str
        symbol: 'R' or 'Y'
        """
        self.name = name
        self.symbol = symbol
        self.opp_symbol = 'Y' if symbol == 'R' else 'R'
        self.ROWS = 6
        self.COLS = 7
        self.TIME_LIMIT = 0.95  # seconds per move budget
        # Preferred move ordering (center first)
        self.ORDER = [3, 2, 4, 1, 5, 0, 6]
        self.CENTER = self.COLS // 2

    def make_move(self, board):
        """
        Decide next move (column index 0-6).
        Uses iterative deepening alpha-beta search with a simple heuristic.
        """
        start_time = time.time()
        self.start_time = start_time

        valid_cols = self.get_valid_columns(board)
        if not valid_cols:
            return 0

        # Quick immediate win
        for col in valid_cols:
            row = self.get_next_open_row(board, col)
            if row is None:
                continue
            board[row][col] = self.symbol
            if self.check_win(board, self.symbol):
                board[row][col] = ' '
                return col
            board[row][col] = ' '

        # Block opponent immediate win
        for col in valid_cols:
            row = self.get_next_open_row(board, col)
            if row is None:
                continue
            board[row][col] = self.opp_symbol
            if self.check_win(board, self.opp_symbol):
                board[row][col] = ' '
                return col
            board[row][col] = ' '

        # If center open, prefer center
        if self.CENTER in valid_cols:
            return self.CENTER

        # Choose max depth depending on remaining empties
        empty_slots = sum(1 for r in range(self.ROWS) for c in range(self.COLS) if board[r][c] == ' ')
        if empty_slots <= 10:
            max_depth = 8
        elif empty_slots <= 20:
            max_depth = 6
        else:
            max_depth = 5

        # Fallback random valid move
        best_col = random.choice(valid_cols)
        best_score = -10**9

        # Iterative deepening
        for depth in range(1, max_depth + 1):
            # stop if out of time
            if time.time() - self.start_time > self.TIME_LIMIT:
                break
            score, col, aborted = self._minimax_root(board, depth)
            if aborted:
                break
            if col is not None:
                best_col = col
                best_score = score

        # Ensure returned column is valid
        if not isinstance(best_col, int) or best_col not in valid_cols:
            best_col = random.choice(valid_cols)
        return best_col

    # Helper functions

    def get_valid_columns(self, board):
        return [c for c in range(self.COLS) if board[0][c] == ' ']

    def get_next_open_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return None

    def check_win(self, board, piece):
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] == piece and board[r][c + 1] == piece and board[r][c + 2] == piece and board[r][c + 3] == piece:
                    return True
        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if board[r][c] == piece and board[r + 1][c] == piece and board[r + 2][c] == piece and board[r + 3][c] == piece:
                    return True
        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] == piece and board[r - 1][c + 1] == piece and board[r - 2][c + 2] == piece and board[r - 3][c + 3] == piece:
                    return True
        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if board[r][c] == piece and board[r + 1][c + 1] == piece and board[r + 2][c + 2] == piece and board[r + 3][c + 3] == piece:
                    return True
        return False

    def is_terminal_node(self, board):
        return self.check_win(board, self.symbol) or self.check_win(board, self.opp_symbol) or not self.get_valid_columns(board)

    def evaluate_window(self, window, piece):
        opp = self.opp_symbol
        score = 0
        piece_count = window.count(piece)
        opp_count = window.count(opp)
        empty_count = window.count(' ')
        if piece_count == 4:
            score += 10000
        elif piece_count == 3 and empty_count == 1:
            score += 100
        elif piece_count == 2 and empty_count == 2:
            score += 10
        if opp_count == 3 and empty_count == 1:
            score -= 90
        elif opp_count == 2 and empty_count == 2:
            score -= 5
        return score

    def score_position(self, board, piece):
        score = 0
        # Center column preference
        center_count = sum(1 for r in range(self.ROWS) if board[r][self.CENTER] == piece)
        score += center_count * 3

        # Horizontal windows
        for r in range(self.ROWS):
            row_array = board[r]
            for c in range(self.COLS - 3):
                window = row_array[c:c + 4]
                score += self.evaluate_window(window, piece)

        # Vertical windows
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r + 4]
                score += self.evaluate_window(window, piece)

        # Diagonal down-right (\)
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        # Diagonal up-right (/)
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        return score

    # Minimax with alpha-beta and time checks
    def _minimax_root(self, board, depth):
        alpha = -10**9
        beta = 10**9
        best_score = -10**9
        best_col = None
        aborted = False

        for col in self.ORDER:
            if time.time() - self.start_time > self.TIME_LIMIT:
                aborted = True
                break
            if board[0][col] != ' ':
                continue
            row = self.get_next_open_row(board, col)
            if row is None:
                continue
            board[row][col] = self.symbol
            score, _, child_aborted = self._minimax(board, depth - 1, alpha, beta, False)
            board[row][col] = ' '
            if child_aborted:
                aborted = True
                break
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_col = col
            alpha = max(alpha, best_score)
        return best_score, best_col, aborted

    def _minimax(self, board, depth, alpha, beta, maximizingPlayer):
        # Time check
        if time.time() - self.start_time > self.TIME_LIMIT:
            return None, None, True

        valid_cols = self.get_valid_columns(board)
        terminal = self.is_terminal_node(board)
        if depth == 0 or terminal:
            if terminal:
                if self.check_win(board, self.symbol):
                    return 10**7, None, False
                elif self.check_win(board, self.opp_symbol):
                    return -10**7, None, False
                else:
                    return 0, None, False
            else:
                return self.score_position(board, self.symbol), None, False

        if maximizingPlayer:
            value = -10**9
            best_col = random.choice(valid_cols)
            for col in self.ORDER:
                if time.time() - self.start_time > self.TIME_LIMIT:
                    return None, None, True
                if col not in valid_cols:
                    continue
                row = self.get_next_open_row(board, col)
                if row is None:
                    continue
                board[row][col] = self.symbol
                new_score, _, aborted = self._minimax(board, depth - 1, alpha, beta, False)
                board[row][col] = ' '
                if aborted:
                    return None, None, True
                if new_score is None:
                    continue
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_col, False
        else:
            value = 10**9
            best_col = random.choice(valid_cols)
            for col in self.ORDER:
                if time.time() - self.start_time > self.TIME_LIMIT:
                    return None, None, True
                if col not in valid_cols:
                    continue
                row = self.get_next_open_row(board, col)
                if row is None:
                    continue
                board[row][col] = self.opp_symbol
                new_score, _, aborted = self._minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = ' '
                if aborted:
                    return None, None, True
                if new_score is None:
                    continue
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, best_col, False
