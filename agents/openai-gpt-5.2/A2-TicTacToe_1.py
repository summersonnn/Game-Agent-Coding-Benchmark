"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-11 20:47:17
"""

from functools import lru_cache

from functools import lru_cache

class TicTacToeAgent:
    WIN_LINES = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    )
    MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)  # center, corners, edges

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol

    @staticmethod
    def _other(mark: str) -> str:
        return 'O' if mark == 'X' else 'X'

    @classmethod
    def _winner(cls, b: str):
        for a, c, d in cls.WIN_LINES:
            m = b[a]
            if m != ' ' and m == b[c] == b[d]:
                return m
        if ' ' not in b:
            return 'DRAW'
        return None

    @classmethod
    def _heuristic(cls, b: str, me: str) -> int:
        """Light tie-breaker among equal minimax values (never overrides win/draw/loss)."""
        opp = cls._other(me)
        score = 0
        twos = 0
        for a, c, d in cls.WIN_LINES:
            line = (b[a], b[c], b[d])
            m_cnt = (line[0] == me) + (line[1] == me) + (line[2] == me)
            o_cnt = (line[0] == opp) + (line[1] == opp) + (line[2] == opp)
            e_cnt = (line[0] == ' ') + (line[1] == ' ') + (line[2] == ' ')
            if o_cnt == 0:
                if m_cnt == 2 and e_cnt == 1:
                    score += 10
                    twos += 1
                elif m_cnt == 1 and e_cnt == 2:
                    score += 2
            if m_cnt == 0 and o_cnt == 2 and e_cnt == 1:
                score -= 9  # discourage allowing opponent threats
        if twos >= 2:
            score += 6  # prefer creating forks when available
        return score

    @classmethod
    @lru_cache(maxsize=None)
    def _solve(cls, board: str, turn: str, me: str):
        """
        Returns (value, best_move) where value is from 'me' perspective.
        best_move is meaningful for the player whose turn it is in this state.
        """
        w = cls._winner(board)
        if w is not None:
            empties = board.count(' ')
            tiebreak = empties if empties >= 3 else 3
            if w == 'DRAW':
                return 0, None
            if w == me:
                return 1000 + tiebreak, None  # win sooner => more empties => higher value
            return -1000 - tiebreak, None      # lose later => fewer empties => less negative

        opp = cls._other(turn)
        maximizing = (turn == me)

        best_val = -10**9 if maximizing else 10**9
        best_moves = []

        for mv in cls.MOVE_ORDER:
            if board[mv] != ' ':
                continue
            nb = board[:mv] + turn + board[mv + 1:]
            val, _ = cls._solve(nb, opp, me)

            if maximizing:
                if val > best_val:
                    best_val = val
                    best_moves = [mv]
                elif val == best_val:
                    best_moves.append(mv)
            else:
                if val < best_val:
                    best_val = val
                    best_moves = [mv]
                elif val == best_val:
                    best_moves.append(mv)

        # Tie-break among equally good minimax moves (doesn't change minimax value).
        if not best_moves:
            return 0, None

        chosen = best_moves[0]
        chosen_h = None
        for mv in best_moves:
            nb = board[:mv] + turn + board[mv + 1:]
            h = cls._heuristic(nb, me)
            if chosen_h is None:
                chosen, chosen_h = mv, h
                continue
            if maximizing:
                if h > chosen_h:
                    chosen, chosen_h = mv, h
            else:
                if h < chosen_h:
                    chosen, chosen_h = mv, h

        return best_val, chosen

    def make_move(self, board: list[str]) -> int:
        b = ''.join(board)

        # Normal case: it's always our turn when called.
        _, mv = self._solve(b, self.symbol, self.symbol)
        if mv is not None and 0 <= mv < 9 and board[mv] == ' ':
            return mv

        # Fallback (should be rare)
        for i, s in enumerate(board):
            if s == ' ':
                return i
        return 0
