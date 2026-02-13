"""
Agent Code: A2-TicTacToe
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:53:21
"""



import random


class TicTacToeAgent:
    """
    A simple but effective agent for 5x5 Tic‑Tac‑Toe (3‑in‑a‑row).
    It looks for immediate wins, blocks opponent wins, and otherwise
    selects the move with the highest heuristic score.
    """

    # --------------------------------------------------------------
    # Pre‑computed winning lines (48 triples of indices)
    WIN_LINES = []

    # Cells in the centre of the board – a slight tie‑breaker
    CENTER_INDICES = {6, 7, 8, 11, 12, 13, 17, 18, 19}

    # --------------------------------------------------------------
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'

        # Initialise the list of winning lines once
        if not TicTacToeAgent.WIN_LINES:
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
            TicTacToeAgent.WIN_LINES = lines

    # --------------------------------------------------------------
    @staticmethod
    def _is_winning(board, symbol) -> bool:
        """Return True if `symbol` already has a three‑in‑a‑row."""
        for a, b, c in TicTacToeAgent.WIN_LINES:
            if board[a] == board[b] == board[c] == symbol:
                return True
        return False

    @classmethod
    def _score_board(cls, board, symbol) -> int:
        """
        Static evaluation of the board from the perspective of `symbol`.
        Positive scores favour `symbol`, negative scores favour the opponent.
        """
        opponent = 'O' if symbol == 'X' else 'X'
        score = 0
        for a, b, c in cls.WIN_LINES:
            cells = (board[a], board[b], board[c])
            my_cnt = sum(1 for x in cells if x == symbol)
            opp_cnt = sum(1 for x in cells if x == opponent)
            empty = 3 - my_cnt - opp_cnt

            if my_cnt == 3:
                score += 10000
            elif opp_cnt == 3:
                score -= 10000
            elif my_cnt == 2 and empty == 1:
                score += 10
            elif my_cnt == 1 and empty == 2:
                score += 1
            elif opp_cnt == 2 and empty == 1:
                score -= 10
            elif opp_cnt == 1 and empty == 2:
                score -= 1
        return score

    # --------------------------------------------------------------
    def make_move(self, board) -> int:
        """
        Choose an index (0‑24) of an empty cell to mark.
        board – list of 25 strings: 'X', 'O', or ' ' (space).
        """
        me = self.symbol
        opponent = 'O' if me == 'X' else 'X'

        # All currently empty squares
        empties = [i for i, cell in enumerate(board) if cell == ' ']
        if not empties:                     # board full – should not happen
            return 0

        # 1) Can I win right now?
        for move in empties:
            board[move] = me
            if self._is_winning(board, me):
                board[move] = ' '
                return move
            board[move] = ' '

        # 2) Must I block opponent's immediate win?
        for move in empties:
            board[move] = opponent
            if self._is_winning(board, opponent):
                board[move] = ' '
                return move
            board[move] = ' '

        # 3) Use heuristic evaluation for the remaining moves
        best_score = -10**9
        best_moves = []

        for move in empties:
            board[move] = me
            score = self._score_board(board, me)
            # tiny bias towards central cells when scores are equal
            if move in self.CENTER_INDICES:
                score += 0.1
            board[move] = ' '

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # Randomly pick among the best to keep the agent non‑deterministic
        return random.choice(best_moves)
