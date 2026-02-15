"""
Agent Code: A5-Connect4RandomStart
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-12 14:50:42
"""

class Connect4Agent:
    """
    Connect 4 agent using minimax with alpha-beta pruning and a heuristic
    evaluation based on 4-in-a-row windows.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'

    def make_move(self, board):
        """Return the best column (0-6) for the current board."""
        valid_moves = self._get_valid_moves(board)
        if not valid_moves:
            return 0  # should never happen in a non‑terminal game

        # Prefer centre columns for better pruning
        centre_cols = [3, 2, 4, 1, 5, 0, 6]
        valid_centre = [c for c in centre_cols if c in valid_moves]

        best_move = valid_centre[0] if valid_centre else valid_moves[0]
        best_value = -float('inf')
        depth = 5

        for col in valid_centre + [c for c in valid_moves if c not in centre_cols]:
            new_board = self._drop_disc(board, col, self.symbol)
            # Immediate win?
            winner = self._check_winner(new_board)
            if winner == self.symbol:
                return col
            value = self._minimax(new_board, depth - 1, -float('inf'), float('inf'), False,
                                   self.symbol, self.opponent)
            if value > best_value:
                best_value = value
                best_move = col

        return best_move

    # ----------------------------------------------------------------------
    # Helper methods (static to avoid accidental state modification)
    # ----------------------------------------------------------------------
    @staticmethod
    def _get_valid_moves(board):
        """Return list of columns that are not full."""
        return [c for c in range(7) if board[0][c] == ' ']

    @staticmethod
    def _drop_disc(board, col, symbol):
        """Return a new board with a disc dropped into the given column."""
        new_board = [row[:] for row in board]
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = symbol
                break
        return new_board

    @staticmethod
    def _check_winner(board):
        """Return the winning symbol ('R' or 'Y') or None."""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        # Vertical
        for c in range(7):
            for r in range(3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        return None

    @staticmethod
    def _evaluate_window(window, symbol):
        """Heuristic score for a single 4‑cell window."""
        opp = 'Y' if symbol == 'R' else 'R'
        cnt_sym = window.count(symbol)
        cnt_opp = window.count(opp)

        if cnt_sym == 4:
            return 1000000
        if cnt_opp == 4:
            return -1000000
        if cnt_sym > 0 and cnt_opp > 0:
            return 0

        # Only one colour (or empty)
        if cnt_sym == 3:
            return 1000
        if cnt_sym == 2:
            return 100
        if cnt_sym == 1:
            return 1
        if cnt_opp == 3:
            return -1000
        if cnt_opp == 2:
            return -100
        if cnt_opp == 1:
            return -1
        return 0

    def _evaluate_board(self, board, symbol):
        """Overall board evaluation from the perspective of `symbol`."""
        score = 0
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        # Vertical
        for c in range(7):
            for r in range(3):
                window = [board[r+i][c] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        # Diagonal down-right
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        # Diagonal down-left
        for r in range(3):
            for c in range(3, 7):
                window = [board[r+i][c-i] for i in range(4)]
                score += self._evaluate_window(window, symbol)
        return score

    def _minimax(self, board, depth, alpha, beta, maximizing, my_sym, opp_sym):
        """
        Minimax with alpha‑beta pruning.
        Returns evaluation from the perspective of my_sym.
        """
        winner = self._check_winner(board)
        if winner == my_sym:
            return 1000000
        if winner == opp_sym:
            return -1000000

        valid = self._get_valid_moves(board)
        if depth == 0 or not valid:
            return self._evaluate_board(board, my_sym)

        # Move ordering: prefer centre columns
        centre = [3, 2, 4, 1, 5, 0, 6]
        ordered = [c for c in centre if c in valid] + [c for c in valid if c not in centre]

        if maximizing:
            value = -float('inf')
            for col in ordered:
                new_board = self._drop_disc(board, col, my_sym)
                value = max(value, self._minimax(new_board, depth-1, alpha, beta, False,
                                                  my_sym, opp_sym))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            for col in ordered:
                new_board = self._drop_disc(board, col, opp_sym)
                value = min(value, self._minimax(new_board, depth-1, alpha, beta, True,
                                                  my_sym, opp_sym))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value