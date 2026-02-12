"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-12 14:50:42
"""

import time

import time
import random

class Connect4Agent:
    ROWS = 6
    COLS = 7
    EMPTY = ' '

    def __init__(self, name, symbol, time_limit=0.95, max_depth=6):
        """
        name: str
        symbol: 'R' or 'Y'
        time_limit: seconds allowed for make_move (keep <1.0 to be safe)
        max_depth: maximum search depth for minimax (iterative deepening up to this)
        """
        if symbol not in ('R', 'Y'):
            raise ValueError("symbol must be 'R' or 'Y'")
        self.name = name
        self.symbol = symbol
        self.time_limit = time_limit
        self.max_depth = max_depth

    def make_move(self, board):
        """
        Decide next move given the board (6 rows x 7 cols).
        Returns an int column index 0-6.
        """
        try:
            start_time = time.time()
            def time_left():
                return (time.time() - start_time) < self.time_limit

            opponent = 'Y' if self.symbol == 'R' else 'R'
            center_col = self.COLS // 2
            INF = 10**9

            # Helpers
            def valid_locations(b):
                return [c for c in range(self.COLS) if b[0][c] == self.EMPTY]

            def get_next_open_row(b, col):
                for r in range(self.ROWS - 1, -1, -1):
                    if b[r][col] == self.EMPTY:
                        return r
                return None

            def drop_piece(b, row, col, piece):
                b[row][col] = piece

            def undo_piece(b, row, col):
                b[row][col] = self.EMPTY

            def check_winner(b):
                # Horizontal
                for r in range(self.ROWS):
                    for c in range(self.COLS - 3):
                        if b[r][c] != self.EMPTY and \
                           b[r][c] == b[r][c+1] == b[r][c+2] == b[r][c+3]:
                            return b[r][c]
                # Vertical
                for r in range(self.ROWS - 3):
                    for c in range(self.COLS):
                        if b[r][c] != self.EMPTY and \
                           b[r][c] == b[r+1][c] == b[r+2][c] == b[r+3][c]:
                            return b[r][c]
                # Diagonal /
                for r in range(3, self.ROWS):
                    for c in range(self.COLS - 3):
                        if b[r][c] != self.EMPTY and \
                           b[r][c] == b[r-1][c+1] == b[r-2][c+2] == b[r-3][c+3]:
                            return b[r][c]
                # Diagonal \
                for r in range(self.ROWS - 3):
                    for c in range(self.COLS - 3):
                        if b[r][c] != self.EMPTY and \
                           b[r][c] == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3]:
                            return b[r][c]
                return None

            def is_full(b):
                return all(b[0][c] != self.EMPTY for c in range(self.COLS))

            def evaluate_window(window, piece):
                score = 0
                opp = 'Y' if piece == 'R' else 'R'
                count_piece = window.count(piece)
                count_opp = window.count(opp)
                count_empty = window.count(self.EMPTY)
                if count_piece == 4:
                    score += 1000000
                elif count_piece == 3 and count_empty == 1:
                    score += 100
                elif count_piece == 2 and count_empty == 2:
                    score += 10
                if count_opp == 3 and count_empty == 1:
                    score -= 90
                elif count_opp == 2 and count_empty == 2:
                    score -= 5
                return score

            def score_position(b, piece):
                score = 0
                # center column preference
                center_array = [b[r][center_col] for r in range(self.ROWS)]
                score += center_array.count(piece) * 6
                # Horizontal
                for r in range(self.ROWS):
                    row_array = [b[r][c] for c in range(self.COLS)]
                    for c in range(self.COLS - 3):
                        window = row_array[c:c+4]
                        score += evaluate_window(window, piece)
                # Vertical
                for c in range(self.COLS):
                    col_array = [b[r][c] for r in range(self.ROWS)]
                    for r in range(self.ROWS - 3):
                        window = col_array[r:r+4]
                        score += evaluate_window(window, piece)
                # Diagonal /
                for r in range(3, self.ROWS):
                    for c in range(self.COLS - 3):
                        window = [b[r - i][c + i] for i in range(4)]
                        score += evaluate_window(window, piece)
                # Diagonal \
                for r in range(self.ROWS - 3):
                    for c in range(self.COLS - 3):
                        window = [b[r + i][c + i] for i in range(4)]
                        score += evaluate_window(window, piece)
                return score

            # Obtain valid columns now (used also in fallback)
            valid_cols = valid_locations(board)
            if not valid_cols:
                return 0

            # Immediate win
            for col in valid_cols:
                row = get_next_open_row(board, col)
                if row is None:
                    continue
                drop_piece(board, row, col, self.symbol)
                if check_winner(board) == self.symbol:
                    undo_piece(board, row, col)
                    return col
                undo_piece(board, row, col)

            # Immediate block
            for col in valid_cols:
                row = get_next_open_row(board, col)
                if row is None:
                    continue
                drop_piece(board, row, col, opponent)
                if check_winner(board) == opponent:
                    undo_piece(board, row, col)
                    return col
                undo_piece(board, row, col)

            # Minimax with alpha-beta and iterative deepening
            def minimax(b, depth, alpha, beta, maximizingPlayer):
                if not time_left():
                    return (None, score_position(b, self.symbol))
                valid_cols_local = valid_locations(b)
                terminal = (check_winner(b) is not None) or is_full(b)
                if depth == 0 or terminal:
                    if terminal:
                        w = check_winner(b)
                        if w == self.symbol:
                            return (None, INF)
                        elif w == opponent:
                            return (None, -INF)
                        else:
                            return (None, 0)
                    else:
                        return (None, score_position(b, self.symbol))
                if maximizingPlayer:
                    value = -INF
                    chosen_col = random.choice(valid_cols_local)
                    # move ordering: prefer center outward
                    for col in sorted(valid_cols_local, key=lambda c: abs(center_col - c)):
                        if not time_left():
                            break
                        row = get_next_open_row(b, col)
                        if row is None:
                            continue
                        drop_piece(b, row, col, self.symbol)
                        new_score = minimax(b, depth - 1, alpha, beta, False)[1]
                        undo_piece(b, row, col)
                        if new_score > value:
                            value = new_score
                            chosen_col = col
                        alpha = max(alpha, value)
                        if alpha >= beta:
                            break
                    return (chosen_col, value)
                else:
                    value = INF
                    chosen_col = random.choice(valid_cols_local)
                    for col in sorted(valid_cols_local, key=lambda c: abs(center_col - c)):
                        if not time_left():
                            break
                        row = get_next_open_row(b, col)
                        if row is None:
                            continue
                        drop_piece(b, row, col, opponent)
                        new_score = minimax(b, depth - 1, alpha, beta, True)[1]
                        undo_piece(b, row, col)
                        if new_score < value:
                            value = new_score
                            chosen_col = col
                        beta = min(beta, value)
                        if alpha >= beta:
                            break
                    return (chosen_col, value)

            best_move = random.choice(valid_cols)
            last_completed = best_move
            for depth in range(1, self.max_depth + 1):
                if not time_left():
                    break
                move, score = minimax(board, depth, -INF, INF, True)
                if not time_left():
                    break
                if move is not None:
                    last_completed = move

            if last_completed not in valid_cols:
                last_completed = random.choice(valid_cols)
            return last_completed

        # If unexpected path, choose a random valid column
        return random.choice(valid_cols if valid_cols else [0])

    except Exception:
        # Always return a valid column on any internal error
        try:
            valid_cols = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
            return random.choice(valid_cols) if valid_cols else 0
        except Exception:
            return 0
