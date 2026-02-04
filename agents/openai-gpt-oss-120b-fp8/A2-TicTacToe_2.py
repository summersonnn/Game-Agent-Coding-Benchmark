"""
Agent Code: A2-TicTacToe
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-04 16:48:59
"""



import random

EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'

WIN_COMBINATIONS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
    (0, 4, 8), (2, 4, 6)               # diagonals
]

class TicTacToeAgent:
    """
    A minimax based Tic‑Tac‑Toe agent.
    It plays perfectly (never loses) and tries to win as quickly as possible.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol               # 'X' or 'O'
        self.opponent = O_MARK if symbol == X_MARK else X_MARK

    # ----------------------------------------------------------------------
    # Helper functions
    # ----------------------------------------------------------------------
    @staticmethod
    def _available_moves(board):
        return [i for i, cell in enumerate(board) if cell == EMPTY]

    @staticmethod
    def _winner(board):
        """Return 'X', 'O', 'DRAW' or None."""
        for a, b, c in WIN_COMBINATIONS:
            if board[a] == board[b] == board[c] != EMPTY:
                return board[a]
        return 'DRAW' if EMPTY not in board else None

    # ----------------------------------------------------------------------
    # Minimax implementation
    # ----------------------------------------------------------------------
    def _minimax(self, board, player):
        """
        Returns a tuple (score, depth, move):
        - score: 1 if self wins, -1 if self loses, 0 for draw.
        - depth: how many moves until the terminal state (used to prefer
                 faster wins / slower losses).
        - move: the index that leads to this score (None for terminal nodes).
        """
        winner = self._winner(board)
        if winner is not None:
            if winner == self.symbol:
                return (1, 0, None)          # win
            elif winner == self.opponent:
                return (-1, 0, None)         # loss
            else:  # draw
                return (0, 0, None)

        moves = self._available_moves(board)

        # Initialize best values
        if player == self.symbol:
            best_score = -float('inf')
            best_depth = float('inf')
            best_move = None
            for m in moves:
                board[m] = player
                score, depth, _ = self._minimax(board, self.opponent)
                board[m] = EMPTY
                # Prefer higher score; for equal scores prefer shallower depth
                if (score > best_score) or (score == best_score and depth + 1 < best_depth):
                    best_score, best_depth, best_move = score, depth + 1, m
            return (best_score, best_depth, best_move)
        else:  # opponent's turn – they minimise our outcome
            best_score = float('inf')
            best_depth = float('inf')
            best_move = None
            for m in moves:
                board[m] = player
                score, depth, _ = self._minimax(board, self.symbol)
                board[m] = EMPTY
                if (score < best_score) or (score == best_score and depth + 1 < best_depth):
                    best_score, best_depth, best_move = score, depth + 1, m
            return (best_score, best_depth, best_move)

    # ----------------------------------------------------------------------
    # Public API used by the game engine
    # ----------------------------------------------------------------------
    def make_move(self, board):
        """
        Returns the index (0‑8) of the cell to mark.
        Uses minimax to select the optimal move.
        """
        # If only one move is possible, skip the recursion.
        available = self._available_moves(board)
        if not available:
            return None
        if len(available) == 1:
            return available[0]

        _, _, best_move = self._minimax(board[:], self.symbol)

        # In the extremely rare case minimax fails (shouldn't happen), fall back to random.
        if best_move is None:
            best_move = random.choice(available)
        return best_move
