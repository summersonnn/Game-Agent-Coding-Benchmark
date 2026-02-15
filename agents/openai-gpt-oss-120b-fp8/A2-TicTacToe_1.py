"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-14 16:45:38
"""



import random

class TicTacToeAgent:
    """
    Simple but effective 5x5 Tic‑Tac‑Toe agent (3‑in‑a‑row win condition).
    Strategy hierarchy:
        1. Win immediately if possible.
        2. Block opponent's immediate win.
        3. Choose a move that creates the most two‑in‑a‑row opportunities.
        4. Block opponent's most threatening two‑in‑a‑row setups.
        5. Prefer centre, then corners and nearby cells.
        6. Fallback to a random legal move.
    """

    # pre‑computed list of all winning triples (indices 0‑24)
    WIN_LINES = []

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol.upper()          # 'X' or 'O'
        self.opponent = 'O' if self.symbol == 'X' else 'X'

        # generate win lines once (class‑wide)
        if not TicTacToeAgent.WIN_LINES:
            TicTacToeAgent.WIN_LINES = self._generate_win_lines()

    @staticmethod
    def _generate_win_lines():
        """Return a list of all 3‑cell winning combinations for a 5×5 board."""
        lines = []

        # rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))

        # columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))

        # diagonal down‑right
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))

        # diagonal down‑left
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))

        return lines

    # --------------------------------------------------------------------- #
    # Helper methods operating directly on the mutable board list
    # --------------------------------------------------------------------- #

    def _is_winning_move(self, board, move, player):
        """Check whether placing `player` at `move` wins the game."""
        original = board[move]
        board[move] = player
        win = any(all(board[i] == player for i in line) for line in self.WIN_LINES)
        board[move] = original
        return win

    def _count_two_in_row(self, board, move, player):
        """
        After playing `move` for `player`, count how many lines contain
        exactly two of `player` and one empty cell.
        """
        original = board[move]
        board[move] = player
        cnt = 0
        for line in self.WIN_LINES:
            cells = [board[i] for i in line]
            if cells.count(player) == 2 and cells.count(' ') == 1:
                cnt += 1
        board[move] = original
        return cnt

    # --------------------------------------------------------------------- #
    # Core decision routine
    # --------------------------------------------------------------------- #

    def make_move(self, board):
        """Return the index (0‑24) of the chosen move."""
        empty_cells = [i for i, v in enumerate(board) if v == ' ']

        # 1. Win if possible
        for mv in empty_cells:
            if self._is_winning_move(board, mv, self.symbol):
                return mv

        # 2. Block opponent's immediate win
        for mv in empty_cells:
            if self._is_winning_move(board, mv, self.opponent):
                return mv

        # 3. Choose move that creates the most own two‑in‑row opportunities
        best_score = -1
        best_moves = []
        for mv in empty_cells:
            score = self._count_two_in_row(board, mv, self.symbol)
            if score > best_score:
                best_score = score
                best_moves = [mv]
            elif score == best_score:
                best_moves.append(mv)
        if best_score > 0:
            return random.choice(best_moves)

        # 4. Block opponent's most threatening two‑in‑row setups
        opp_best_score = -1
        opp_best_moves = []
        for mv in empty_cells:
            score = self._count_two_in_row(board, mv, self.opponent)
            if score > opp_best_score:
                opp_best_score = score
                opp_best_moves = [mv]
            elif score == opp_best_score:
                opp_best_moves.append(mv)
        if opp_best_score > 0:
            # Prefer a move that also helps us if possible
            intersect = set(best_moves).intersection(opp_best_moves)
            if intersect:
                return random.choice(list(intersect))
            return random.choice(opp_best_moves)

        # 5. Positional preference: centre, then corners and near‑centre cells
        preference_order = [
            12,                     # centre
            6, 8, 10, 14,           # cells adjacent to centre
            0, 4, 20, 24,           # corners
            2, 22, 18, 16, 1, 3, 5, 9, 15, 19, 21, 23, 7, 11, 13, 17
        ]
        for pos in preference_order:
            if pos in empty_cells:
                return pos

        # 6. Fallback – random legal move (should never be reached if board not full)
        return random.choice(empty_cells) if empty_cells else None
