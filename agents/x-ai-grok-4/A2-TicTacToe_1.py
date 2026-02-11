"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-11 20:47:17
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
        if ' ' not in board:
            return 'DRAW'
        return None

    def minimax(self, board, is_maximizing):
        winner = self.check_winner(board)
        if winner is not None:
            if winner == 'DRAW':
                return 0
            empty_count = board.count(' ')
            bonus = max(empty_count, 3)
            if winner == self.symbol:
                return 10 + bonus
            else:
                return - (10 + bonus)
        
        if is_maximizing:
            max_eval = float('-inf')
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

    def make_move(self, board):
        available = [i for i in range(9) if board[i] == ' ']
        if not available:
            return None
        
        best_score = float('-inf')
        best_move = None
        for move in available:
            board[move] = self.symbol
            score = self.minimax(board, False)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
