"""
Agent Code: A2-TicTacToe
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-13 14:53:21
"""

import random
import time

class TicTacToeAgent:
    """Agent that plays 5x5 Tic Tac Toe (three in a row) using minimax with alpha-beta pruning
    and a heuristic evaluation function.  It also checks for immediate win/block before searching.
    """

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol          # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'

        # ---- Precompute all 48 winning lines ----
        self.lines = []
        # rows
        for r in range(5):
            for c in range(3):
                self.lines.append((r*5 + c, r*5 + c+1, r*5 + c+2))
        # columns
        for c in range(5):
            for r in range(3):
                self.lines.append((r*5 + c, (r+1)*5 + c, (r+2)*5 + c))
        # diagonals down-right
        for r in range(3):
            for c in range(3):
                self.lines.append((r*5 + c, (r+1)*5 + c+1, (r+2)*5 + c+2))
        # diagonals down-left
        for r in range(3):
            for c in range(2, 5):
                self.lines.append((r*5 + c, (r+1)*5 + c-1, (r+2)*5 + c-2))

        # ---- Static move ordering: cells that belong to more lines are tried first ----
        self.cell_weight = [0] * 25
        for line in self.lines:
            for idx in line:
                self.cell_weight[idx] += 1

    # ----------------------------------------------------------------------
    # Public method required by the game engine
    # ----------------------------------------------------------------------
    def make_move(self, board):
        """Return the index (0‑24) of the cell to mark."""
        empty = [i for i, c in enumerate(board) if c == ' ']
        # If only one move is possible, take it immediately
        if len(empty) == 1:
            return empty[0]

        # 1) Immediate win
        for move in empty:
            if self._is_winning_move(board, move, self.symbol):
                return move

        # 2) Block opponent's immediate win
        for move in empty:
            if self._is_winning_move(board, move, self.opponent):
                return move

        # 3) Deeper search with iterative deepening alpha‑beta
        start_time = time.time()
        time_limit = 0.9          # seconds
        best_move = None
        depth = 1
        max_depth = len(empty)    # no need to go deeper than remaining moves

        while depth <= max_depth:
            move, _ = self._alpha_beta_root(board, depth, start_time, time_limit)
            if move is not None:
                best_move = move
            # If time is running out, stop deepening
            if time.time() - start_time > time_limit * 0.8:
                break
            depth += 1

        # Fallback (should never happen)
        if best_move is None:
            best_move = random.choice(empty)
        return best_move

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------
    def _is_winning_move(self, board, move, player):
        """Test whether playing `player` at `move` creates a three‑in‑a‑row."""
        # Simulate the move
        temp = board[:]
        temp[move] = player
        return self._check_win(temp, player)

    def _check_win(self, board, player):
        """Return True iff `player` has three in a row on the board."""
        for (a, b, c) in self.lines:
            if board[a] == board[b] == board[c] == player:
                return True
        return False

    def _evaluate(self, board):
        """Heuristic score from the perspective of `self.symbol`.
        Positive = good for us, negative = good for opponent.
        """
        score = 0
        for (a, b, c) in self.lines:
            cnt_us = 0
            cnt_them = 0
            for idx in (a, b, c):
                if board[idx] == self.symbol:
                    cnt_us += 1
                elif board[idx] == self.opponent:
                    cnt_them += 1
            # A line containing both symbols is dead – ignore it
            if cnt_us and cnt_them:
                continue
            if cnt_us:
                if cnt_us == 3:
                    score += 10000
                elif cnt_us == 2:
                    score += 100
                elif cnt_us == 1:
                    score += 10
            elif cnt_them:
                if cnt_them == 3:
                    score -= 10000
                elif cnt_them == 2:
                    score -= 100
                elif cnt_them == 1:
                    score -= 10
            # all empty contributes nothing
        return score

    # ----------------------------------------------------------------------
    # Alpha‑beta search
    # ----------------------------------------------------------------------
    def _alpha_beta_root(self, board, depth, start_time, time_limit):
        """Root call for the maximizing player (our agent).  Returns (best_move, value)."""
        best_move = None
        alpha = -float('inf')
        beta = float('inf')
        empty = [i for i, c in enumerate(board) if c == ' ']

        # Order moves: cells in more lines first (static heuristic)
        empty.sort(key=lambda m: self.cell_weight[m], reverse=True)

        for move in empty:
            if time.time() - start_time > time_limit:
                return None, None   # timeout

            new_board = board[:]
            new_board[move] = self.symbol
            value = self._alpha_beta(new_board, depth - 1, alpha, beta,
                                     False, start_time, time_limit)
            if value > alpha:
                alpha = value
                best_move = move
        return best_move, alpha

    def _alpha_beta(self, board, depth, alpha, beta, maximizing, start_time, time_limit):
        """Recursive alpha‑beta."""
        # Terminal conditions
        if self._check_win(board, self.symbol):
            return 100000
        if self._check_win(board, self.opponent):
            return -100000
        if ' ' not in board:          # draw
            return 0
        if depth == 0:
            return self._evaluate(board)

        # Timeout – return evaluation (heuristic)
        if time.time() - start_time > time_limit:
            return self._evaluate(board)

        empty = [i for i, c in enumerate(board) if c == ' ']
        # Use same static move ordering
        empty.sort(key=lambda m: self.cell_weight[m], reverse=True)

        if maximizing:
            value = -float('inf')
            for move in empty:
                new_board = board[:]
                new_board[move] = self.symbol
                value = max(value, self._alpha_beta(new_board, depth - 1, alpha, beta,
                                                    False, start_time, time_limit))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for move in empty:
                new_board = board[:]
                new_board[move] = self.opponent
                value = min(value, self._alpha_beta(new_board, depth - 1, alpha, beta,
                                                    True, start_time, time_limit))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value