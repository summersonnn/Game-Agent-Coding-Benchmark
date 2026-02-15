"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-14 17:00:49
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_conditions = []
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 1, start + 2))
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 5, start + 10))
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 6, start + 12))
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_conditions.append((start, start + 4, start + 8))

    def check_winner(self, board):
        for a, b, c in self.win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if all(s != ' ' for s in board):
            return 'DRAW'
        return None

    def minimax(self, board, depth, is_max, alpha, beta):
        winner = self.check_winner(board)
        if winner is not None:
            if winner == self.symbol:
                return 100 - depth
            elif winner == self.opponent:
                return -100 + depth
            else:
                return 0

        available = [i for i in range(25) if board[i] == ' ']

        if is_max:
            max_eval = float('-inf')
            for move in available:
                board[move] = self.symbol
                eval = self.minimax(board, depth + 1, False, alpha, beta)
                board[move] = ' '
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available:
                board[move] = self.opponent
                eval = self.minimax(board, depth + 1, True, alpha, beta)
                board[move] = ' '
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, board):
        available = [i for i in range(25) if board[i] == ' ']
        if not available:
            return None

        best_score = float('-inf')
        best_move = available[0]
        for move in available:
            board[move] = self.symbol
            score = self.minimax(board, 1, False, float('-inf'), float('inf'))
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
