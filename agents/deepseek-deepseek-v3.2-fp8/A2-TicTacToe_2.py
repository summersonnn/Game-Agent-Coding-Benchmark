"""
Agent Code: A2-TicTacToe
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-13 14:53:21
"""

import random

class TicTacToeAgent:
    """Agent for 5x5 Tic Tac Toe (three in a row). Uses minimax with alpha-beta pruning."""

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol          # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.EMPTY = ' '

        # Precompute all 48 winning lines (three consecutive cells)
        self.win_lines = []
        # rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 1, start + 2))
        # columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 5, start + 10))
        # diagonals down-right
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 6, start + 12))
        # diagonals down-left
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_lines.append((start, start + 4, start + 8))

    def make_move(self, board):
        """Return the index (0-24) of the chosen move."""
        # 1. Immediate win
        for move in self._empty_cells(board):
            if self._is_winning_move(board, move, self.symbol):
                return move

        # 2. Block opponent's immediate win
        for move in self._empty_cells(board):
            if self._is_winning_move(board, move, self.opponent):
                return move

        # 3. Search with minimax
        empty_count = len(self._empty_cells(board))
        # Depth adapts to remaining empty cells (shallow early, deeper late)
        if empty_count > 15:
            depth = 2
        elif empty_count > 10:
            depth = 3
        elif empty_count > 5:
            depth = 4
        else:
            depth = 5

        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        for move in self._order_moves(board):
            # play move
            board[move] = self.symbol
            if self._is_winning_move(board, move, self.symbol):
                # immediate win – no need to search deeper
                board[move] = self.EMPTY
                return move
            score = self._minimax(board, depth - 1, alpha, beta, False)
            board[move] = self.EMPTY

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)

        # Fallback (should never happen if there are legal moves)
        if best_move is None:
            best_move = random.choice(self._empty_cells(board))
        return best_move

    def _minimax(self, board, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        empty = self._empty_cells(board)
        if depth == 0 or not empty:
            return self._evaluate(board)

        if maximizing:
            value = -float('inf')
            for move in self._order_moves(board):
                board[move] = self.symbol
                if self._is_winning_move(board, move, self.symbol):
                    # winning move – give high score (sooner wins better)
                    value = max(value, 10000 + depth)
                else:
                    value = max(value, self._minimax(board, depth - 1, alpha, beta, False))
                board[move] = self.EMPTY
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for move in self._order_moves(board):
                board[move] = self.opponent
                if self._is_winning_move(board, move, self.opponent):
                    value = min(value, -10000 - depth)
                else:
                    value = min(value, self._minimax(board, depth - 1, alpha, beta, True))
                board[move] = self.EMPTY
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def _evaluate(self, board):
        """Heuristic evaluation from the agent's perspective."""
        score = 0
        for line in self.win_lines:
            ours = 0
            theirs = 0
            for idx in line:
                if board[idx] == self.symbol:
                    ours += 1
                elif board[idx] == self.opponent:
                    theirs += 1
            # Mixed lines are dead – ignore
            if ours and theirs:
                continue
            if ours:
                if ours == 1:
                    score += 1
                elif ours == 2:
                    score += 10
                elif ours == 3:
                    score += 1000   # should have been caught earlier
            elif theirs:
                if theirs == 1:
                    score -= 1
                elif theirs == 2:
                    score -= 10
                elif theirs == 3:
                    score -= 1000
        # small bonus for centre control
        centre = 12
        if board[centre] == self.symbol:
            score += 5
        elif board[centre] == self.opponent:
            score -= 5
        return score

    def _is_winning_move(self, board, move, player):
        """Check if placing `player` at `move` creates a three‑in‑a‑row."""
        board[move] = player
        win = False
        for line in self.win_lines:
            if move in line and all(board[i] == player for i in line):
                win = True
                break
        board[move] = self.EMPTY
        return win

    def _empty_cells(self, board):
        """Return list of indices of empty cells."""
        return [i for i, c in enumerate(board) if c == self.EMPTY]

    def _order_moves(self, board):
        """Static move ordering: centre, corners, edges."""
        empty = self._empty_cells(board)
        # priority groups: centre (0), corners (1), near‑centre (2), rest (3)
        def priority(cell):
            if cell == 12:
                return 0
            if cell in (0, 4, 20, 24):
                return 1
            if cell in (2, 10, 14, 22):   # approximate edge centres
                return 2
            return 3
        return sorted(empty, key=priority)