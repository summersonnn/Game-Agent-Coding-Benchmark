"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4.1-fast
Run: 3
Generated: 2026-02-04 16:54:53
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'

    def check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def minimax(self, board, is_maximizing, depth):
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 10 - depth
        elif winner == self.opponent:
            return depth - 10
        elif winner == 'DRAW':
            return 0

        if is_maximizing:
            max_eval = float('-inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval_score = self.minimax(board, False, depth + 1)
                    board[i] = ' '
                    max_eval = max(max_eval, eval_score)
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    eval_score = self.minimax(board, True, depth + 1)
                    board[i] = ' '
                    min_eval = min(min_eval, eval_score)
            return min_eval

    def make_move(self, board):
        available_moves = [i for i in range(9) if board[i] == ' ']
        if not available_moves:
            return None

        best_move = None
        best_score = float('-inf')
        for move in available_moves:
            board[move] = self.symbol
            score = self.minimax(board, False, 1)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
