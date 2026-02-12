"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-5.2-codex
Run: 1
Generated: 2026-02-12 15:02:53
"""

import math

import math
import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opp = 'R' if symbol == 'Y' else 'Y'
        self.EMPTY = ' '
        self.ROWS = 6
        self.COLS = 7
        self.pref_order = [3, 2, 4, 1, 5, 0, 6]  # center‑first ordering

    # ---------- Main Move Function ----------
    def make_move(self, board):
        valid = self.get_valid_locations(board)
        if not valid:
            return 0

        # 1) Check immediate winning move
        for col in valid:
            row = self.get_next_open_row(board, col)
            b_copy = [r[:] for r in board]
            b_copy[row][col] = self.symbol
            if self.check_winner(b_copy, self.symbol):
                return col

        # 2) Block opponent winning move
        for col in valid:
            row = self.get_next_open_row(board, col)
            b_copy = [r[:] for r in board]
            b_copy[row][col] = self.opp
            if self.check_winner(b_copy, self.opp):
                return col

        # 3) Minimax (depth 4)
        _, col = self.minimax(board, depth=4, alpha=-math.inf, beta=math.inf, maximizing=True)
        if col is None:
            return random.choice(valid)
        return col

    # ---------- Minimax + Alpha Beta ----------
    def minimax(self, board, depth, alpha, beta, maximizing):
        valid_locations = self.get_valid_locations(board)
        is_terminal = self.is_terminal_node(board)

        if depth == 0 or is_terminal:
            if is_terminal:
                if self.check_winner(board, self.symbol):
                    return (10**9, None)
                elif self.check_winner(board, self.opp):
                    return (-10**9, None)
                else:
                    return (0, None)
            else:
                return (self.score_position(board, self.symbol), None)

        # Order columns: center first
        ordered_cols = [c for c in self.pref_order if c in valid_locations]

        if maximizing:
            value = -math.inf
            best_col = random.choice(valid_locations)
            for col in ordered_cols:
                row = self.get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                b_copy[row][col] = self.symbol
                new_score, _ = self.minimax(b_copy, depth-1, alpha, beta, False)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_col
        else:
            value = math.inf
            best_col = random.choice(valid_locations)
            for col in ordered_cols:
                row = self.get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                b_copy[row][col] = self.opp
                new_score, _ = self.minimax(b_copy, depth-1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, best_col

    # ---------- Helpers ----------
    def get_valid_locations(self, board):
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    def get_next_open_row(self, board, col):
        for r in range(self.ROWS-1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return None

    def is_terminal_node(self, board):
        return (self.check_winner(board, self.symbol) or
                self.check_winner(board, self.opp) or
                len(self.get_valid_locations(board)) == 0)

    def check_winner(self, board, piece):
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS-3):
                if all(board[r][c+i] == piece for i in range(4)):
                    return True
        # Vertical
        for r in range(self.ROWS-3):
            for c in range(self.COLS):
                if all(board[r+i][c] == piece for i in range(4)):
                    return True
        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS-3):
                if all(board[r-i][c+i] == piece for i in range(4)):
                    return True
        # Diagonal \
        for r in range(self.ROWS-3):
            for c in range(self.COLS-3):
                if all(board[r+i][c+i] == piece for i in range(4)):
                    return True
        return False

    def score_position(self, board, piece):
        score = 0

        # Center column preference
        center_array = [board[r][self.COLS//2] for r in range(self.ROWS)]
        score += center_array.count(piece) * 3

        # Horizontal, Vertical, Diagonal windows
        for r in range(self.ROWS):
            for c in range(self.COLS-3):
                window = [board[r][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        for c in range(self.COLS):
            for r in range(self.ROWS-3):
                window = [board[r+i][c] for i in range(4)]
                score += self.evaluate_window(window, piece)

        for r in range(self.ROWS-3):
            for c in range(self.COLS-3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        for r in range(3, self.ROWS):
            for c in range(self.COLS-3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        return score

    def evaluate_window(self, window, piece):
        opp = 'R' if piece == 'Y' else 'Y'
        score = 0
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(self.EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(self.EMPTY) == 2:
            score += 2

        if window.count(opp) == 3 and window.count(self.EMPTY) == 1:
            score -= 4
        return score
