"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-11 20:47:17
"""

from typing import List, Tuple, Optional

from typing import List, Tuple, Optional

EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'

class TicTacToeAgent:
    """
    Minimax (with depth‑aware scoring) Tic‑Tac‑Toe agent.
    Plays optimally and prefers faster wins / slower losses.
    """

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol.upper()          # 'X' or 'O'
        self.opponent = X_MARK if self.symbol == O_MARK else O_MARK

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def make_move(self, board: List[str]) -> int:
        """
        Return the index (0‑8) of the move to play.
        """
        # List of empty cells
        empty = [i for i, cell in enumerate(board) if cell == EMPTY]
        if not empty:
            raise ValueError("No moves left on the board")

        # If only one move left, no need to search
        if len(empty) == 1:
            return empty[0]

        # Minimax search
        best_score = -float('inf')
        best_move = empty[0]

        for move in empty:
            board[move] = self.symbol
            score = self._minimax(board, depth=0, maximizing=False, alpha=-float('inf'), beta=float('inf'))
            board[move] = EMPTY

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    # --------------------------------------------------------------------- #
    # Minimax implementation
    # --------------------------------------------------------------------- #
    def _minimax(self,
                 board: List[str],
                 depth: int,
                 maximizing: bool,
                 alpha: float,
                 beta: float) -> float:
        """
        Returns a numeric evaluation of the board from the perspective of self.symbol.
        Positive values favour the agent, negative values favour the opponent.
        The magnitude incorporates depth so that quicker wins are higher.
        """
        winner = self._check_winner(board)
        if winner is not None:
            if winner == self.symbol:
                return 10 - depth          # faster win = higher score
            elif winner == self.opponent:
                return depth - 10          # slower loss = higher (less negative) score
            else:  # draw
                return 0

        empty = [i for i, cell in enumerate(board) if cell == EMPTY]
        if not empty:                       # should not happen because winner check covers full board
            return 0

        if maximizing:
            max_eval = -float('inf')
            for move in empty:
                board[move] = self.symbol
                eval = self._minimax(board, depth + 1, False, alpha, beta)
                board[move] = EMPTY
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break                # beta cut‑off
            return max_eval
        else:
            min_eval = float('inf')
            for move in empty:
                board[move] = self.opponent
                eval = self._minimax(board, depth + 1, True, alpha, beta)
                board[move] = EMPTY
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break                # alpha cut‑off
            return min_eval

    # --------------------------------------------------------------------- #
    # Helper: evaluate winner
    # --------------------------------------------------------------------- #
    @staticmethod
    def _check_winner(board: List[str]) -> Optional[str]:
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
            (0, 4, 8), (2, 4, 6)               # diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != EMPTY:
                return board[a]
        if EMPTY not in board:
            return 'DRAW'
        return None
