"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-code-fast-1
Run: 2
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    """
    An agent that uses the minimax algorithm to play Tic Tac Toe optimally.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)               # Diagonals
        ]

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return None
        best_score = -float('inf')
        best_move = None
        for move in available_moves:
            board[move] = self.symbol
            score = self.minimax(board, False)
            board[move] = ' '  # Undo move
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def minimax(self, board, is_maximizing):
        if self.is_winner(board, self.symbol):
            return 1
        if self.is_winner(board, self.opponent):
            return -1
        if ' ' not in board:
            return 0
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval = self.minimax(board, False)
                    board[i] = ' '
                    max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    eval = self.minimax(board, True)
                    board[i] = ' '
                    min_eval = min(min_eval, eval)
            return min_eval

    def is_winner(self, board, player):
        for a, b, c in self.win_conditions:
            if board[a] == board[b] == board[c] == player:
                return True
        return False
