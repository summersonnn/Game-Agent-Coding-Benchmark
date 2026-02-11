"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-11 20:47:17
"""

from functools import lru_cache

from functools import lru_cache

class TicTacToeAgent:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opp = 'O' if symbol == 'X' else 'X'
        self.empty = ' '

        self._lines = (
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
            (0, 4, 8), (2, 4, 6),             # diags
        )
        # Deterministic tie-break preference (strong human-like ordering)
        self._pref = (4, 0, 2, 6, 8, 1, 3, 5, 7)

        # Per-instance cached solver bound to this agent's symbol
        @lru_cache(maxsize=None)
        def solve(board_tup: tuple[str, ...], player: str) -> int:
            w = winner(board_tup)
            if w is not None:
                empties = board_tup.count(self.empty)
                if w == 'DRAW':
                    return 0
                # Prefer faster wins (more empties left) and slower losses
                if w == self.symbol:
                    return 100 + empties
                return -100 - empties

            if player == self.symbol:
                best = -10**9
                for i, v in enumerate(board_tup):
                    if v == self.empty:
                        nb = list(board_tup)
                        nb[i] = player
                        best = max(best, solve(tuple(nb), self.opp))
                return best
            else:
                best = 10**9
                for i, v in enumerate(board_tup):
                    if v == self.empty:
                        nb = list(board_tup)
                        nb[i] = player
                        best = min(best, solve(tuple(nb), self.symbol))
                return best

        def winner(b: tuple[str, ...]):
            for a, c, d in self._lines:
                s = b[a]
                if s != self.empty and s == b[c] == b[d]:
                    return s
            if self.empty not in b:
                return 'DRAW'
            return None

        self._solve = solve

    def make_move(self, board: list[str]) -> int:
        empties = [i for i, v in enumerate(board) if v == self.empty]
        if not empties:
            return None

        # Quick optimal opening (also reduces compute)
        if len(empties) == 9:
            return 4  # center is optimal
        if len(empties) == 8 and board[4] == self.empty:
            return 4

        b = tuple(board)
        best_score = -10**9
        best_moves = []

        for m in empties:
            nb = list(b)
            nb[m] = self.symbol
            score = self._solve(tuple(nb), self.opp)
            if score > best_score:
                best_score = score
                best_moves = [m]
            elif score == best_score:
                best_moves.append(m)

        # Deterministic tie-break among equally optimal moves
        best_set = set(best_moves)
        for p in self._pref:
            if p in best_set:
                return p
        return best_moves[0]
