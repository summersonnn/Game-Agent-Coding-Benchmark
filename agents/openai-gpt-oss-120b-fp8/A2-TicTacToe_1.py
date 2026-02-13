"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-13 14:53:21
"""

from typing import List, Tuple, Optional

import random
from typing import List, Tuple, Optional

# Pre‑compute all possible 3‑in‑a‑row triples on the 5×5 board
WIN_LINES: List[Tuple[int, int, int]] = []

# rows
for r in range(5):
    for c in range(3):
        start = r * 5 + c
        WIN_LINES.append((start, start + 1, start + 2))

# columns
for c in range(5):
    for r in range(3):
        start = r * 5 + c
        WIN_LINES.append((start, start + 5, start + 10))

# diagonals ↘ (down‑right)
for r in range(3):
    for c in range(3):
        start = r * 5 + c
        WIN_LINES.append((start, start + 6, start + 12))

# diagonals ↙ (down‑left)
for r in range(3):
    for c in range(2, 5):
        start = r * 5 + c
        WIN_LINES.append((start, start + 4, start + 8))


def _winner(board: List[str]) -> Optional[str]:
    """Return 'X', 'O', 'DRAW', or None."""
    for a, b, c in WIN_LINES:
        if board[a] == board[b] == board[c] != ' ':
            return board[a]
    if ' ' not in board:
        return 'DRAW'
    return None


class TicTacToeAgent:
    """
    Mini‑max agent with alpha‑beta pruning for 5×5 Tic‑Tac‑Toe (3‑in‑a‑row).
    It looks a few moves ahead, blocks opponent threats and tries to create
    forks.  If the search does not finish (e.g., because of depth limit),
    it falls back to a random legal move.
    """

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol            # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.max_depth = 4              # depth of minimax search (adjustable)

    # ----------------------------------------------------------------------
    # Evaluation function ----------------------------------------------------
    def _evaluate(self, board: List[str]) -> int:
        """
        Simple heuristic:
          +1000 for a win, -1000 for a loss.
          +50 for a line with two own marks, +10 for a line with one.
          -50 for a line with two opponent marks, -10 for a line with one.
        """
        win = _winner(board)
        if win == self.symbol:
            return 1000 + board.count(' ')          # reward quick wins
        if win == self.opponent:
            return -1000 - board.count(' ')         # penalise quick losses
        if win == 'DRAW':
            return 0

        score = 0
        for a, b, c in WIN_LINES:
            line = (board[a], board[b], board[c])
            own = line.count(self.symbol)
            opp = line.count(self.opponent)

            if own > 0 and opp == 0:          # only my marks in the line
                if own == 2:
                    score += 50
                elif own == 1:
                    score += 10
            elif opp > 0 and own == 0:        # only opponent marks
                if opp == 2:
                    score -= 50
                elif opp == 1:
                    score -= 10
        return score

    # ----------------------------------------------------------------------
    # Mini‑max with alpha‑beta ------------------------------------------------
    def _minimax(self,
                 board: List[str],
                 depth: int,
                 alpha: int,
                 beta: int,
                 maximizing: bool) -> Tuple[int, Optional[int]]:
        """
        Returns (score, best_move).  `best_move` is None when depth == 0
        or the board is terminal.
        """
        win = _winner(board)
        if win or depth == 0:
            return self._evaluate(board), None

        moves = [i for i, v in enumerate(board) if v == ' ']
        best_move: Optional[int] = None

        if maximizing:
            max_eval = -float('inf')
            for m in moves:
                board[m] = self.symbol
                eval_score, _ = self._minimax(board, depth - 1, alpha, beta, False)
                board[m] = ' '
                if eval_score > max_eval:
                    max_eval, best_move = eval_score, m
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for m in moves:
                board[m] = self.opponent
                eval_score, _ = self._minimax(board, depth - 1, alpha, beta, True)
                board[m] = ' '
                if eval_score < min_eval:
                    min_eval, best_move = eval_score, m
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # ----------------------------------------------------------------------
    # Public interface -------------------------------------------------------
    def make_move(self, board: List[str]) -> int:
        """
        Choose a move:
          1. Win immediately if possible.
          2. Block opponent's immediate win.
          3. Use minimax to pick the best continuation.
          4. Fallback to a random legal move.
        """
        empty = [i for i, v in enumerate(board) if v == ' ']

        # --- 1. Immediate winning move ------------------------------------------------
        for a, b, c in WIN_LINES:
            line = (board[a], board[b], board[c])
            if line.count(self.symbol) == 2 and line.count(' ') == 1:
                win_idx = (a, b, c)[line.index(' ')]
                return win_idx

        # --- 2. Block opponent's immediate win ----------------------------------------
        for a, b, c in WIN_LINES:
            line = (board[a], board[b], board[c])
            if line.count(self.opponent) == 2 and line.count(' ') == 1:
                block_idx = (a, b, c)[line.index(' ')]
                return block_idx

        # --- 3. Mini‑max search ---------------------------------------------------------
        _, best = self._minimax(board[:], self.max_depth, -float('inf'), float('inf'), True)
        if best is not None and board[best] == ' ':
            return best

        # --- 4. Random fallback ---------------------------------------------------------
        return random.choice(empty) if empty else -1
