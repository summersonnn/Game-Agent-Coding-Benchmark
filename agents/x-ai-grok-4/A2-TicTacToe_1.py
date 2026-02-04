"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 1
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
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        if ' ' not in board:
            return 'DRAW'
        return None

    def minimax(self, board, is_maximizing):
        terminal = self.check_winner(board)
        if terminal:
            if terminal == 'DRAW':
                return 0
            return 1 if terminal == self.symbol else -1

        if is_maximizing:
            max_score = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, False)
                    board[i] = ' '
                    max_score = max(max_score, score)
            return max_score
        else:
            min_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    score = self.minimax(board, True)
                    board[i] = ' '
                    min_score = min(min_score, score)
            return min_score

    def make_move(self, board):
        available = [i for i in range(9) if board[i] == ' ']
        if not available:
            return None

        best_score = -float('inf')
        best_move = None
        for move in available:
            board[move] = self.symbol
            score = self.minimax(board, False)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
