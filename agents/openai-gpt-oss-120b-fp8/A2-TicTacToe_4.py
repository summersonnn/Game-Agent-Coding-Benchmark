"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 4
Generated: 2026-02-04 16:48:59
"""



import random

class TicTacToeAgent:
    """
    Minimax (with alpha‑beta pruning) Tic‑Tac‑Toe agent.
    Plays optimally – never loses and tries to win whenever possible.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol            # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'

    # -----------------------------------------------------------------------
    # Public API used by the game engine
    # -----------------------------------------------------------------------
    def make_move(self, board):
        """
        Return the index (0‑8) of the best move for the current board.
        board – list of 9 strings (X, O, or ' ') representing the state.
        """
        # If only one move left, just take it
        moves = self._available_moves(board)
        if len(moves) == 1:
            return moves[0]

        best_score = -float('inf')
        best_moves = []

        for move in moves:
            board[move] = self.symbol                 # try move
            score = self._minimax(board, False,
                                  -float('inf'), float('inf'))
            board[move] = ' '                         # undo move

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # If several equally good moves, pick one at random for variety
        return random.choice(best_moves) if best_moves else None

    # -----------------------------------------------------------------------
    # Minimax implementation
    # -----------------------------------------------------------------------
    def _minimax(self, board, is_maximizing, alpha, beta):
        winner = self._check_winner(board)
        if winner is not None:                 # terminal node
            return self._evaluate(winner)

        if is_maximizing:
            max_eval = -float('inf')
            for move in self._available_moves(board):
                board[move] = self.symbol
                eval = self._minimax(board, False, alpha, beta)
                board[move] = ' '
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break                       # β‑cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in self._available_moves(board):
                board[move] = self.opponent
                eval = self._minimax(board, True, alpha, beta)
                board[move] = ' '
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break                       # α‑cutoff
            return min_eval

    # -----------------------------------------------------------------------
    # Helper utilities
    # -----------------------------------------------------------------------
    def _available_moves(self, board):
        return [i for i, spot in enumerate(board) if spot == ' ']

    def _evaluate(self, winner):
        """Score from the perspective of self.symbol."""
        if winner == self.symbol:
            return 1
        if winner == self.opponent:
            return -1
        return 0                     # draw

    def _check_winner(self, board):
        """Return 'X', 'O', 'DRAW', or None if the game is ongoing."""
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
            (0, 4, 8), (2, 4, 6)               # diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None
