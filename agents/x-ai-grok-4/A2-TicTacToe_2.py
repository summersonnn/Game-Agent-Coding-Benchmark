"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 2
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

    def get_possible_moves(self, board):
        order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        return [i for i in order if board[i] == ' ']

    def minimax(self, board, player, depth, alpha, beta):
        winner = self.check_winner(board)
        if winner is not None:
            if winner == 'DRAW':
                return 0
            elif winner == self.symbol:
                return 10 - depth
            else:
                return -(10 - depth)

        if player == self.symbol:
            max_score = -float('inf')
            for i in self.get_possible_moves(board):
                board[i] = player
                score = self.minimax(board, self.opponent, depth + 1, alpha, beta)
                board[i] = ' '
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = float('inf')
            for i in self.get_possible_moves(board):
                board[i] = player
                score = self.minimax(board, self.symbol, depth + 1, alpha, beta)
                board[i] = ' '
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score

    def make_move(self, board):
        best_score = -float('inf')
        best_move = None
        for i in self.get_possible_moves(board):
            board[i] = self.symbol
            score = self.minimax(board, self.opponent, 1, -float('inf'), float('inf'))
            board[i] = ' '
            if score > best_score:
                best_score = score
                best_move = i
        return best_move
