"""
Agent Code: A5-Connect4RandomStart
Model: x-ai-grok-4
Run: 2
Generated: 2026-02-12 14:50:42
"""

import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'

    # ===================================================================
    # Public interface
    # ===================================================================
    def make_move(self, board):
        valid_moves = self._get_valid_moves(board)
        if not valid_moves:
            return 0

        # Center-first ordering greatly improves alpha-beta pruning
        ordered_moves = sorted(valid_moves, key=lambda c: -abs(c - 3))

        best_score = -float('inf')
        best_col = ordered_moves[0]

        depth = 7 if len(valid_moves) > 4 else 8   # go a bit deeper in endgame

        for col in ordered_moves:
            new_board = [row[:] for row in board]
            self._drop_disc(new_board, col, self.symbol)

            # After our move it's opponent's turn → maximizing_player=False
            score = self._minimax(new_board, depth, -float('inf'), float('inf'), False)

            if score > best_score:
                best_score = score
                best_col = col

        return best_col

    # ===================================================================
    # Core minimax with alpha-beta
    # ===================================================================
    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        winner = self._check_winner(board)
        if winner is not None:
            return 100_000 + depth * 10 if winner == self.symbol else -100_000 - depth * 10

        if self._is_full(board):
            return 0

        if depth == 0:
            return self._evaluate_board(board)

        if maximizing_player:  # our turn
            max_eval = -float('inf')
            for col in self._get_valid_moves(board):
                new_board = [row[:] for row in board]
                self._drop_disc(new_board, col, self.symbol)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:  # opponent's turn
            min_eval = float('inf')
            for col in self._get_valid_moves(board):
                new_board = [row[:] for row in board]
                self._drop_disc(new_board, col, self.opponent)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # ===================================================================
    # Board helpers (copied & adapted from the engine)
    # ===================================================================
    def _get_valid_moves(self, board):
        return [c for c in range(7) if board[0][c] == ' ']

    def _drop_disc(self, board, col, disc):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = disc
                return

    def _check_winner(self, board):
        # Horizontal
        for r in range(6):
            for c in range(4):
                p = board[r][c]
                if p != ' ' and p == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return p

        # Vertical
        for r in range(3):
            for c in range(7):
                p = board[r][c]
                if p != ' ' and p == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return p

        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                p = board[r][c]
                if p != ' ' and p == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return p

        # Diagonal \
        for r in range(3):
            for c in range(4):
                p = board[r][c]
                if p != ' ' and p == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return p

        return None

    def _is_full(self, board):
        return all(board[0][c] != ' ' for c in range(7))

    # ===================================================================
    # Evaluation (heuristic)
    # ===================================================================
    def _evaluate_board(self, board):
        score = 0

        # Center bonus
        for r in range(6):
            if board[r][3] == self.symbol:
                score += 6
            elif board[r][3] == self.opponent:
                score -= 6

        # Score all possible 4-cell windows
        score += self._score_all_windows(board)

        return score

    def _score_all_windows(self, board):
        score = 0

        def evaluate_window(window):
            my = window.count(self.symbol)
            opp = window.count(self.opponent)
            empty = window.count(' ')

            if my == 4:
                return 1000
            if my == 3 and empty == 1:
                return 80
            if my == 2 and empty == 2:
                return 12
            if my == 1 and empty == 3:
                return 2

            if opp == 4:
                return -1000
            if opp == 3 and empty == 1:
                return -120   # blocking is very important
            if opp == 2 and empty == 2:
                return -25
            if opp == 1 and empty == 3:
                return -3

            return 0

        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c+i] for i in range(4)]
                score += evaluate_window(window)

        # Vertical
        for r in range(3):
            for c in range(7):
                window = [board[r+i][c] for i in range(4)]
                score += evaluate_window(window)

        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += evaluate_window(window)

        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window)

        return score