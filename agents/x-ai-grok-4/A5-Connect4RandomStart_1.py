"""
Agent Code: A5-Connect4RandomStart
Model: x-ai-grok-4
Run: 1
Generated: 2026-02-12 14:50:42
"""

import random
import copy

class Connect4Agent:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        
        # Tuned scoring weights
        self.WIN_SCORE = 100_000
        self.THREE_SCORE = 500
        self.TWO_SCORE = 50
        self.CENTER_BONUS = 8

    # ====================== HELPERS ======================

    def _is_valid_move(self, board, col: int) -> bool:
        return 0 <= col < 7 and board[0][col] == ' '

    def _get_valid_moves(self, board) -> list[int]:
        return [c for c in range(7) if self._is_valid_move(board, c)]

    def _drop_disc(self, board, col: int, player: str):
        """Returns a new board with the disc dropped (does not modify original)."""
        new_board = copy.deepcopy(board)
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = player
                return new_board
        return new_board  # should never happen if move was valid

    def _check_winner(self, board):
        """Returns 'R', 'Y', or None (same logic as the official engine)."""
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

    def _is_full(self, board) -> bool:
        return all(board[0][c] != ' ' for c in range(7))

    def _evaluate_window(self, window: list, player: str) -> int:
        opp = self.opponent
        count_p = window.count(player)
        count_o = window.count(opp)
        count_e = window.count(' ')

        if count_p == 4:
            return self.WIN_SCORE
        if count_p == 3 and count_e == 1:
            return self.THREE_SCORE
        if count_p == 2 and count_e == 2:
            return self.TWO_SCORE
        if count_o == 3 and count_e == 1:
            return -self.THREE_SCORE * 2   # strong penalty for opponent threat
        if count_o == 4:
            return -self.WIN_SCORE
        return 0

    def _score_board(self, board) -> int:
        """Positional heuristic (very effective in Connect 4)."""
        score = 0
        player = self.symbol

        # Center control (very important)
        for r in range(6):
            if board[r][3] == player:
                score += self.CENTER_BONUS
            elif board[r][2] == player or board[r][4] == player:
                score += self.CENTER_BONUS // 2

        # All possible 4-cell windows
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c+i] for i in range(4)]
                score += self._evaluate_window(window, player)

        # Vertical
        for c in range(7):
            for r in range(3):
                window = [board[r+i][c] for i in range(4)]
                score += self._evaluate_window(window, player)

        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window, player)

        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window, player)

        return score

    # ====================== MINIMAX ======================

    def _minimax(self, board, depth: int, maximizing: bool, alpha: float, beta: float) -> int:
        winner = self._check_winner(board)

        if winner == self.symbol:
            return self.WIN_SCORE - depth          # quicker win = slightly better
        if winner == self.opponent:
            return -self.WIN_SCORE + depth
        if self._is_full(board) or depth == 0:
            return self._score_board(board)

        valid_moves = self._get_valid_moves(board)

        if maximizing:  # our turn
            max_eval = -float('inf')
            for col in valid_moves:
                new_board = self._drop_disc(board, col, self.symbol)
                eval_score = self._minimax(new_board, depth-1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:  # opponent's turn
            min_eval = float('inf')
            for col in valid_moves:
                new_board = self._drop_disc(board, col, self.opponent)
                eval_score = self._minimax(new_board, depth-1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # ====================== PUBLIC API ======================

    def make_move(self, board):
        valid_moves = self._get_valid_moves(board)
        if not valid_moves:
            return 3  # fallback (should never happen)

        # Simple but effective move ordering: center first
        valid_moves.sort(key=lambda c: -abs(c - 3))   # 3, 2, 4, 1, 5, 0, 6

        best_score = -float('inf')
        best_col = valid_moves[0]

        # Depth 6 is very strong in this variant (especially with random start)
        # Depth 7 is possible in late game, but 6 is safe within 1s.
        search_depth = 6

        for col in valid_moves:
            new_board = self._drop_disc(board, col, self.symbol)
            score = self._minimax(new_board, search_depth - 1, False, -float('inf'), float('inf'))

            if score > best_score:
                best_score = score
                best_col = col

        return best_col