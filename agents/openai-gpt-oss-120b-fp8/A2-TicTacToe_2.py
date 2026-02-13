"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-13 14:53:21
"""

import math

import math

class TicTacToeAgent:
    """
    A minimax‑based agent for 5×5 Tic‑Tac‑Toe (3‑in‑a‑row).
    It looks for immediate wins / blocks, then searches a few plies
    using alpha‑beta pruning and a simple line‑based evaluation.
    """

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol.upper()          # 'X' or 'O'
        self.opponent = 'O' if self.symbol == 'X' else 'X'

        # Pre‑compute all winning triples (rows, columns, diagonals)
        self.wins = []
        # rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.wins.append((start, start + 1, start + 2))
        # columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.wins.append((start, start + 5, start + 10))
        # diagonal down‑right
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.wins.append((start, start + 6, start + 12))
        # diagonal down‑left
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.wins.append((start, start + 4, start + 8))

        # depth of the minimax search (adjustable if time permits)
        self.max_depth = 3

    # ----------------------------------------------------------------------
    # Public interface
    def make_move(self, board):
        """Return the index (0‑24) of the chosen move."""
        empty = [i for i, v in enumerate(board) if v == ' ']

        # 1️⃣  Immediate winning move
        for m in empty:
            trial = board.copy()
            trial[m] = self.symbol
            if self._winner(trial) == self.symbol:
                return m

        # 2️⃣  Block opponent's immediate win
        for m in empty:
            trial = board.copy()
            trial[m] = self.opponent
            if self._winner(trial) == self.opponent:
                return m

        # 3️⃣  Minimax search
        best_score = -math.inf
        best_move = random.choice(empty)   # fallback
        for m in empty:
            trial = board.copy()
            trial[m] = self.symbol
            score = self._minimax(trial, self.max_depth - 1, False,
                                 -math.inf, math.inf)
            if score > best_score:
                best_score = score
                best_move = m

        return best_move

    # ----------------------------------------------------------------------
    # Game helpers
    def _winner(self, board):
        """Return 'X', 'O', 'DRAW' or None."""
        for a, b, c in self.wins:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    # ----------------------------------------------------------------------
    # Evaluation
    def _evaluate(self, board):
        """Simple heuristic: count open lines weighted by owned marks."""
        score = 0
        for a, b, c in self.wins:
            line = (board[a], board[b], board[c])

            # lines that can still be completed by us
            if self.opponent not in line:
                cnt = line.count(self.symbol)
                if cnt == 2:
                    score += 50          # two in a row, one empty
                elif cnt == 1:
                    score += 10

            # lines that can be completed by opponent
            if self.symbol not in line:
                cnt = line.count(self.opponent)
                if cnt == 2:
                    score -= 50
                elif cnt == 1:
                    score -= 10
        return score

    # ----------------------------------------------------------------------
    # Minimax with alpha‑beta pruning
    def _minimax(self, board, depth, maximizing, alpha, beta):
        winner = self._winner(board)
        if winner == self.symbol:
            # Prefer faster wins
            return 1000 + depth
        if winner == self.opponent:
            return -1000 - depth
        if winner == 'DRAW':
            return 0
        if depth == 0:
            return self._evaluate(board)

        empty = [i for i, v in enumerate(board) if v == ' ']

        if maximizing:
            max_eval = -math.inf
            for m in empty:
                board[m] = self.symbol
                eval_ = self._minimax(board, depth - 1, False, alpha, beta)
                board[m] = ' '
                max_eval = max(max_eval, eval_)
                alpha = max(alpha, eval_)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for m in empty:
                board[m] = self.opponent
                eval_ = self._minimax(board, depth - 1, True, alpha, beta)
                board[m] = ' '
                min_eval = min(min_eval, eval_)
                beta = min(beta, eval_)
                if beta <= alpha:
                    break
            return min_eval
