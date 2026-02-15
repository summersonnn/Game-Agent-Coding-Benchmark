"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-13 09:23:08
"""

import time
import math

import time
import random
import math

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        name: str - agent name
        symbol: str - 'R' or 'Y'
        """
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'

    def make_move(self, board):
        """
        Decide next move given board (list of lists, 6x7).
        Returns an int column 0-6.
        """
        ROWS = 6
        COLS = 7
        EMPTY = ' '
        start_time = time.monotonic()
        time_limit = 0.95  # seconds to keep under the 1s engine limit

        def valid_moves(b):
            return [c for c in range(COLS) if b[0][c] == EMPTY]

        def get_next_open_row(b, col):
            for r in range(ROWS - 1, -1, -1):
                if b[r][col] == EMPTY:
                    return r
            return None

        def drop_piece(b, row, col, piece):
            nb = [rowcopy[:] for rowcopy in b]
            nb[row][col] = piece
            return nb

        def winning_move(b, piece):
            # Horizontal
            for r in range(ROWS):
                for c in range(COLS - 3):
                    if b[r][c] == piece and b[r][c+1] == piece and b[r][c+2] == piece and b[r][c+3] == piece:
                        return True
            # Vertical
            for r in range(ROWS - 3):
                for c in range(COLS):
                    if b[r][c] == piece and b[r+1][c] == piece and b[r+2][c] == piece and b[r+3][c] == piece:
                        return True
            # Diagonal \
            for r in range(ROWS - 3):
                for c in range(COLS - 3):
                    if b[r][c] == piece and b[r+1][c+1] == piece and b[r+2][c+2] == piece and b[r+3][c+3] == piece:
                        return True
            # Diagonal /
            for r in range(3, ROWS):
                for c in range(COLS - 3):
                    if b[r][c] == piece and b[r-1][c+1] == piece and b[r-2][c+2] == piece and b[r-3][c+3] == piece:
                        return True
            return False

        def evaluate_window(window, piece):
            score = 0
            opp = self.opponent
            count_piece = window.count(piece)
            count_opp = window.count(opp)
            count_empty = window.count(EMPTY)
            if count_piece == 4:
                score += 100000
            elif count_piece == 3 and count_empty == 1:
                score += 100
            elif count_piece == 2 and count_empty == 2:
                score += 10
            if count_opp == 3 and count_empty == 1:
                score -= 800
            elif count_opp == 2 and count_empty == 2:
                score -= 5
            return score

        def score_position(b, piece):
            score = 0
            # Center column preference
            center_col = COLS // 2
            center_count = sum(1 for r in range(ROWS) if b[r][center_col] == piece)
            score += center_count * 6

            # Horizontal
            for r in range(ROWS):
                row_array = b[r]
                for c in range(COLS - 3):
                    window = row_array[c:c+4]
                    score += evaluate_window(window, piece)

            # Vertical
            for c in range(COLS):
                col_array = [b[r][c] for r in range(ROWS)]
                for r in range(ROWS - 3):
                    window = col_array[r:r+4]
                    score += evaluate_window(window, piece)

            # Diagonal \
            for r in range(ROWS - 3):
                for c in range(COLS - 3):
                    window = [b[r+i][c+i] for i in range(4)]
                    score += evaluate_window(window, piece)

            # Diagonal /
            for r in range(3, ROWS):
                for c in range(COLS - 3):
                    window = [b[r-i][c+i] for i in range(4)]
                    score += evaluate_window(window, piece)

            return score

        # 1) Basic validity and quick returns
        valid = valid_moves(board)
        if not valid:
            # no valid columns (shouldn't happen often)
            return 0

        # 2) Immediate win
        for col in valid:
            row = get_next_open_row(board, col)
            nb = drop_piece(board, row, col, self.symbol)
            if winning_move(nb, self.symbol):
                return col

        # 3) Immediate block
        for col in valid:
            row = get_next_open_row(board, col)
            nb = drop_piece(board, row, col, self.opponent)
            if winning_move(nb, self.opponent):
                return col

        # 4) Minimax with alpha-beta + iterative deepening
        def order_moves(moves):
            center = COLS // 2
            return sorted(moves, key=lambda x: abs(x - center))

        def minimax(b, depth_left, alpha, beta, maximizingPlayer):
            # Time check
            if time.monotonic() - start_time > time_limit:
                raise TimeoutError()

            valid_loc = valid_moves(b)
            is_terminal = winning_move(b, self.symbol) or winning_move(b, self.opponent) or len(valid_loc) == 0

            if depth_left == 0 or is_terminal:
                if is_terminal:
                    if winning_move(b, self.symbol):
                        return (None, 10**12)
                    elif winning_move(b, self.opponent):
                        return (None, -10**12)
                    else:
                        return (None, 0)
                else:
                    return (None, score_position(b, self.symbol))

            if maximizingPlayer:
                value = -math.inf
                best_col = random.choice(valid_loc)
                for col in order_moves(valid_loc):
                    row = get_next_open_row(b, col)
                    nb = drop_piece(b, row, col, self.symbol)
                    new_score = minimax(nb, depth_left - 1, alpha, beta, False)[1]
                    if new_score > value:
                        value = new_score
                        best_col = col
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
                return best_col, value
            else:
                value = math.inf
                best_col = random.choice(valid_loc)
                for col in order_moves(valid_loc):
                    row = get_next_open_row(b, col)
                    nb = drop_piece(b, row, col, self.opponent)
                    new_score = minimax(nb, depth_left - 1, alpha, beta, True)[1]
                    if new_score < value:
                        value = new_score
                        best_col = col
                    beta = min(beta, value)
                    if alpha >= beta:
                        break
                return best_col, value

        # iterative deepening
        best_move = random.choice(valid)
        MAX_DEPTH = 5  # safe default to fit under 1 second; iterative deepening will stop early on timeout
        for depth in range(1, MAX_DEPTH + 1):
            try:
                col, _ = minimax(board, depth, -math.inf, math.inf, True)
                if col is not None and col in valid:
                    best_move = col
            except TimeoutError:
                # time's up; use last best_move
                break

        # final safety checks
        if not (isinstance(best_move, int) and 0 <= best_move < COLS and board[0][best_move] == EMPTY):
            best_move = random.choice(valid)

        return best_move

