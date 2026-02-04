"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-04 16:48:59
"""

import math

import random
import math

# Assuming the constants EMPTY, X_MARK, O_MARK are defined globally in the game file.
# If not, uncomment the following lines:
# EMPTY = ' '
# X_MARK = 'X'
# O_MARK = 'O'

class TicTacToeAgent:
    """
    An optimal Tic‑Tac‑Toe agent using minimax with alpha‑beta pruning.
    It never loses and will win whenever the opponent makes a sub‑optimal move.
    """
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol               # 'X' or 'O'
        self.opponent = O_MARK if symbol == X_MARK else X_MARK

    # -----------------------------------------------------------------------
    # Public interface expected by the game engine
    # -----------------------------------------------------------------------
    def make_move(self, board):
        """
        Return the index (0‑8) of the best move for the current board.
        board – list of 9 strings (EMPTY, X_MARK or O_MARK)
        """
        # If only one move is possible, just take it.
        available = [i for i, spot in enumerate(board) if spot == EMPTY]
        if len(available) == 1:
            return available[0]

        # Run minimax to find the optimal move.
        _, best_move = self._minimax(board, self.symbol, -math.inf, math.inf)
        # As a safe fallback (should never happen), pick a random legal move.
        return best_move if best_move is not None else random.choice(available)

    # -----------------------------------------------------------------------
    # Minimax implementation with alpha‑beta pruning
    # -----------------------------------------------------------------------
    def _minimax(self, board, player, alpha, beta):
        """
        Returns a tuple (score, move) where:
          - score is the minimax evaluation from the perspective of self.symbol
          - move is the board index that yields that score (or None at terminal nodes)
        """
        winner = self._check_winner(board)
        if winner is not None:
            if winner == self.symbol:
                return 1, None          # win
            if winner == self.opponent:
                return -1, None         # loss
            return 0, None              # draw

        available = [i for i, spot in enumerate(board) if spot == EMPTY]

        if player == self.symbol:          # Maximising player
            max_eval = -math.inf
            best_moves = []
            for move in available:
                board[move] = player
                eval_score, _ = self._minimax(board, self.opponent, alpha, beta)
                board[move] = EMPTY

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_moves = [move]
                elif eval_score == max_eval:
                    best_moves.append(move)

                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # prune

            chosen_move = random.choice(best_moves) if best_moves else None
            return max_eval, chosen_move

        else:                              # Minimising player (opponent)
            min_eval = math.inf
            best_moves = []
            for move in available:
                board[move] = player
                eval_score, _ = self._minimax(board, self.symbol, alpha, beta)
                board[move] = EMPTY

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_moves = [move]
                elif eval_score == min_eval:
                    best_moves.append(move)

                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # prune

            chosen_move = random.choice(best_moves) if best_moves else None
            return min_eval, chosen_move

    # -----------------------------------------------------------------------
    # Helper: evaluate terminal board states
    # -----------------------------------------------------------------------
    def _check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != EMPTY:
                return board[a]

        if EMPTY not in board:
            return 'DRAW'
        return None
