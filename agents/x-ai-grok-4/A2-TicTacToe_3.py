"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 3
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
                score = self.minimax(board, False)
                board[i] = ' '
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move

    def minimax(self, board, is_maximizing):
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 1
        elif winner == self.opponent:
            return -1
        elif winner == 'DRAW':
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    score = self.minimax(board, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            return best_score

    def check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        if ' ' not in board:
            return 'DRAW'
        return None
