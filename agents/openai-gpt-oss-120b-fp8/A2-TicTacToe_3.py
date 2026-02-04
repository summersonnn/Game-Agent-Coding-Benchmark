"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 3
Generated: 2026-02-04 16:48:59
"""



import random

class TicTacToeAgent:
    """
    Optimal Tic‑Tac‑Toe agent using the minimax algorithm.
    Guarantees at least a draw and will win whenever the opponent
    makes a mistake.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol            # 'X' or 'O'
        # opponent symbol based on the global constants defined in the game
        self.opponent = O_MARK if symbol == X_MARK else X_MARK

    # -----------------------------------------------------------------------
    # Public API used by the game engine
    # -----------------------------------------------------------------------
    def make_move(self, board):
        """
        Return the index (0‑8) of the best move for the current board.
        board – list of 9 strings (X, O or EMPTY).
        """
        available = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available:
            return None

        best_score = -float('inf')
        best_moves = []

        # Try every legal move, evaluate with minimax, keep the best ones
        for move in available:
            board[move] = self.symbol
            score = self._minimax(board, self.opponent, depth=0)
            board[move] = EMPTY

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # If several moves are equally good, pick one at random
        return random.choice(best_moves)

    # -----------------------------------------------------------------------
    # Minimax implementation
    # -----------------------------------------------------------------------
    def _minimax(self, board, player, depth):
        """
        Return the minimax value of the given board for `player`.
        Positive values favour the agent, negative values favour the opponent.
        """
        winner = self._check_winner(board)
        if winner is not None:
            # Terminal node – assign a score
            if winner == self.symbol:
                return 10 - depth      # faster win is better
            if winner == self.opponent:
                return depth - 10      # slower loss is better
            return 0                    # draw

        # Not a terminal state – recurse
        available = [i for i, spot in enumerate(board) if spot == EMPTY]

        if player == self.symbol:          # Maximising player
            max_eval = -float('inf')
            for move in available:
                board[move] = player
                eval = self._minimax(board, self.opponent, depth + 1)
                board[move] = EMPTY
                max_eval = max(max_eval, eval)
            return max_eval
        else:                              # Minimising player
            min_eval = float('inf')
            for move in available:
                board[move] = player
                eval = self._minimax(board, self.symbol, depth + 1)
                board[move] = EMPTY
                min_eval = min(min_eval, eval)
            return min_eval

    # -----------------------------------------------------------------------
    # Helper – board evaluation
    # -----------------------------------------------------------------------
    def _check_winner(self, board):
        """Return X_MARK, O_MARK, 'DRAW' or None."""
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
