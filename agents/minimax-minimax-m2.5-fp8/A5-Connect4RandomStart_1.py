"""
Agent Code: A5-Connect4RandomStart
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:10:12
"""

import sys
from Connect4Game import Connect4Game   # assuming the engine is in the same folder

import random
import sys

# ----------------------------------------------------------------------
#  Connect4Agent
# ----------------------------------------------------------------------
class Connect4Agent:
    """
    A Connect 4 player that uses:
        * depth‑limited Minimax (depth = 5, adjustable)
        * α‑β pruning
        * a hand‑crafted heuristic that rewards centre‑column control,
          3‑in‑a‑row, 2‑in‑a‑row and penalises opponent threats.
    """

    ROWS = 6
    COLS = 7
    EMPTY = ' '
    INF = 1_000_000          # large score that dwarfs any heuristic

    def __init__(self, name: str, symbol: str):
        """
        :param name:   agent name (used by the competition harness)
        :param symbol: 'R' or 'Y'
        """
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'

    # ------------------------------------------------------------------
    #  Public API – called by the game engine
    # ------------------------------------------------------------------
    def make_move(self, board):
        """
        Choose the next column (0‑6) in which to drop a disc.

        The board is a copy of the 6×7 grid, so we may mutate it locally
        during the search.
        """
        # columns that are not full
        valid = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

        # sanity (should never happen)
        if not valid:
            return 0

        # ------------------------------------------------------------------
        #  Quick win – if any move wins immediately, take it.
        # ------------------------------------------------------------------
        for col in valid:
            row = self._drop_row(board, col)
            if row is None:
                continue
            tmp = [r[:] for r in board]
            tmp[row][col] = self.symbol
            if self._winner(tmp) == self.symbol:
                return col

        # ------------------------------------------------------------------
        #  Otherwise run minimax.
        # ------------------------------------------------------------------
        # depth can be increased if the agent gets more time – 5 works comfortably
        depth = 5
        best_move, _ = self._minimax_root(board, depth, valid)
        return best_move

    # ------------------------------------------------------------------
    #  Minimax with α‑β pruning
    # ------------------------------------------------------------------
    def _minimax_root(self, board, depth, valid_cols):
        """Start the recursive search (our turn, i.e. maximizing)."""
        # order moves: columns closest to the centre are tried first – better pruning
        ordered = sorted(valid_cols, key=lambda c: abs(c - 3))

        best_score = -float('inf')
        best_col = ordered[0]
        alpha = -float('inf')
        beta = float('inf')

        for col in ordered:
            row = self._drop_row(board, col)
            if row is None:
                continue
            new_board = [r[:] for r in board]
            new_board[row][col] = self.symbol
            # immediate win?
            if self._winner(new_board) == self.symbol:
                # highest possible score – no need to search further
                return col, self.INF

            score = self._minimax(new_board, depth - 1, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_col = col
            alpha = max(alpha, score)

        # tie‑break: shuffle among equally good moves
        equally_good = [c for c in ordered
                        if self._score_of_move(board, c, depth) == best_score]
        if len(equally_good) > 1:
            best_col = random.choice(equally_good)

        return best_col, best_score

    def _minimax(self, board, depth, alpha, beta, maximizing):
        """Recursive minimax (depth‑first)."""
        # terminal tests
        win = self._winner(board)
        if win == self.symbol:
            return self.INF               # we win
        if win == self.opponent:
            return -self.INF              # opponent wins
        if depth == 0 or self._is_full(board):
            return self._heuristic(board)

        valid = [c for c in range(self.COLS) if board[0][c] == self.EMPTY]
        # move ordering – centre first
        ordered = sorted(valid, key=lambda c: abs(c - 3))

        if maximizing:          # our turn
            max_eval = -float('inf')
            for col in ordered:
                row = self._drop_row(board, col)
                if row is None:
                    continue
                new_board = [r[:] for r in board]
                new_board[row][col] = self.symbol
                if self._winner(new_board) == self.symbol:
                    # win as soon as possible – a tiny penalty for depth
                    return self.INF - 1
                eval_score = self._minimax(new_board, depth - 1,
                                            alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:                   # opponent's turn (minimizing)
            min_eval = float('inf')
            for col in ordered:
                row = self._drop_row(board, col)
                if row is None:
                    continue
                new_board = [r[:] for r in board]
                new_board[row][col] = self.opponent
                if self._winner(new_board) == self.opponent:
                    return -self.INF + 1
                eval_score = self._minimax(new_board, depth - 1,
                                            alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # ------------------------------------------------------------------
    #  Helpers – board manipulation & evaluation
    # ------------------------------------------------------------------
    def _drop_row(self, board, col):
        """Return the row index where a disc would land in column col,
           or None if the column is already full."""
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return None

    def _winner(self, board):
        """Return 'R', 'Y' if there is a four‑in‑a‑row, otherwise None."""
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                w = board[r][c]
                if w != self.EMPTY and w == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return w
        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                w = board[r][c]
                if w != self.EMPTY and w == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return w
        # Diagonal “\”
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                w = board[r][c]
                if w != self.EMPTY and w == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return w
        # Diagonal “/”
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                w = board[r][c]
                if w != self.EMPTY and w == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return w
        return None

    def _is_full(self, board):
        return all(board[0][c] != self.EMPTY for c in range(self.COLS))

    # ------------------------------------------------------------------
    #  Heuristic evaluation (our perspective)
    # ------------------------------------------------------------------
    def _heuristic(self, board):
        """Score the board for the player using self.symbol."""
        score = 0

        # 1️⃣  Centre column is most valuable
        centre = 3
        centre_cnt = sum(1 for r in range(self.ROWS) if board[r][centre] == self.symbol)
        score += centre_cnt * 3

        # 2️⃣  Examine every length‑4 window
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._score_window(window)

        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                window = [board[r+i][c] for i in range(4)]
                score += self._score_window(window)

        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._score_window(window)

        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._score_window(window)

        return score

    def _score_window(self, win):
        """Score a single 4‑cell window (list of 4 symbols)."""
        my = sum(1 for c in win if c == self.symbol)
        op = sum(1 for c in win if c == self.opponent)
        empty = sum(1 for c in win if c == self.EMPTY)

        # Terminal states are handled elsewhere, but guard anyway
        if op == 4:
            return -100_000
        if my == 4:
            return 100_000

        pts = 0

        # Our own opportunities
        if my == 3 and empty == 1:
            pts += 5
        elif my == 2 and empty == 2:
            pts += 2

        # Opponent threats – we prefer to block them
        if op == 3 and empty == 1:
            pts -= 4

        return pts

    # ------------------------------------------------------------------
    #  Helper used only for tie‑breaking (not essential)
    # ------------------------------------------------------------------
    def _score_of_move(self, board, col, depth):
        """Quick static evaluation of a single move – used for tie‑break."""
        row = self._drop_row(board, col)
        if row is None:
            return -float('inf')
        tmp = [r[:] for r in board]
        tmp[row][col] = self.symbol
        return self._heuristic(tmp)


# ----------------------------------------------------------------------
#  Example usage (you can delete this part when submitting)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Very simple test: two agents play each other
    from Connect4Game import Connect4Game   # assuming the engine is in the same folder

    agent_red = Connect4Agent("RedBot", "R")
    agent_yellow = Connect4Agent("YellowBot", "Y")

    game = Connect4Game()
    result = game.play_game(agent_red, agent_yellow)
    print(f"Game finished: {result}")
