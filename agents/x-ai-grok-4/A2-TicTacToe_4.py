"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 4
Generated: 2026-02-04 16:50:03
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        best_score = -float('inf')
        best_move = None
        for i in range(9):
            if board[i] == ' ':
                board[i] = self.symbol
                score = self.minimax(board, 0, False)
                board[i] = ' '
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move

    def minimax(self, board, depth, is_maximizing):
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 10 - depth
        elif winner == self.opponent:
            return depth - 10
        elif winner == 'DRAW':
            return 0

        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval = self.minimax(board, depth + 1, False)
                    board[i] = ' '
                    max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    eval = self.minimax(board, depth + 1, True)
                    board[i] = ' '
                    min_eval = min(min_eval, eval)
            return min_eval

    def check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None
