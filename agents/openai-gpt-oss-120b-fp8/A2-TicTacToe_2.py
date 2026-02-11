"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-11 20:47:17
"""

import math

class TicTacToeAgent:
    """
    Perfect-play Tic‑Tac‑Toe agent using minimax with alpha‑beta pruning.
    It evaluates wins/losses with a depth bias so it prefers faster victories
    and delays defeats, matching the secondary scoring metric of the competition.
    """

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol.upper()          # 'X' or 'O'
        self.opponent = "O" if self.symbol == "X" else "X"

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------
    def make_move(self, board):
        """
        Return the index (0‑8) of the best move for the current board.
        `board` is a list of 9 strings: ' ', 'X' or 'O'.
        """
        EMPTY = " "

        # Gather empty cells
        empty_cells = [i for i, v in enumerate(board) if v == EMPTY]
        if not empty_cells:
            return None  # No move possible (should not happen)

        # If only one move left, just take it
        if len(empty_cells) == 1:
            return empty_cells[0]

        best_score = -math.inf
        best_move = empty_cells[0]

        # Try each possible move and pick the one with the highest minimax score
        for move in empty_cells:
            board[move] = self.symbol
            score = self._minimax(board, maximizing=False, depth=1,
                                 alpha=-math.inf, beta=math.inf)
            board[move] = EMPTY

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    # ------------------------------------------------------------
    # Minimax implementation
    # ------------------------------------------------------------
    def _minimax(self, board, maximizing: bool, depth: int, alpha: float, beta: float):
        """
        Returns a numeric evaluation of the board from the perspective of `self.symbol`.
        Positive values favor the agent, negative values favor the opponent.
        Depth is used to prefer quicker wins / slower losses.
        """
        winner = self._check_winner(board)
        if winner is not None:
            if winner == self.symbol:
                return 10 - depth      # faster win = higher score
            if winner == self.opponent:
                return depth - 10      # slower loss = higher (less negative) score
            return 0                    # draw

        EMPTY = " "
        moves = [i for i, v in enumerate(board) if v == EMPTY]

        if maximizing:
            max_eval = -math.inf
            for move in moves:
                board[move] = self.symbol
                eval = self._minimax(board, False, depth + 1, alpha, beta)
                board[move] = EMPTY
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # beta cut‑off
            return max_eval
        else:
            min_eval = math.inf
            for move in moves:
                board[move] = self.opponent
                eval = self._minimax(board, True, depth + 1, alpha, beta)
                board[move] = EMPTY
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # alpha cut‑off
            return min_eval

    # ------------------------------------------------------------
    # Helper: check winner / draw
    # ------------------------------------------------------------
    def _check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != " ":
                return board[a]
        if " " not in board:
            return "DRAW"
        return None
