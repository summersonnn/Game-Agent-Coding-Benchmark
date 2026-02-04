"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-04 16:50:03
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'

    def check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if all(cell != ' ' for cell in board):
            return 'DRAW'
        return None

    def minimax(self, board, depth, is_maximizing):
        result = self.check_winner(board)
        if result is not None:
            if result == self.symbol:
                return 10 - depth
            elif result == 'DRAW':
                return 0
            else:
                return -10 + depth

        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    score = self.minimax(board, depth + 1, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            return best_score

    def make_move(self, board):
        best_score = -float('inf')
        best_move = None
        for i in range(9):
            if board[i] == ' ':
                board[i] = self.symbol
                score = self.minimax(board, 1, False)
                board[i] = ' '
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move
