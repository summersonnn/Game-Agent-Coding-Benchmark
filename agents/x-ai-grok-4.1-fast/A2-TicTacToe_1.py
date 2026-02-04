"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4.1-fast
Run: 1
Generated: 2026-02-04 16:54:53
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'

    def make_move(self, board):
        def is_winner(b, player):
            lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
            return any(b[a] == b[b_] == b[c] == player for a, b_, c in lines)

        def get_moves(b):
            return [i for i, spot in enumerate(b) if spot == ' ']

        def minimax(b, depth, alpha, beta, maximizing):
            opp = 'O' if self.symbol == 'X' else 'X'
            if is_winner(b, self.symbol):
                return 10 - depth
            if is_winner(b, opp):
                return depth - 10
            moves = get_moves(b)
            if not moves:
                return 0
            if maximizing:
                max_eval = -float('inf')
                for m in moves:
                    b[m] = self.symbol
                    eval_score = minimax(b, depth + 1, alpha, beta, False)
                    b[m] = ' '
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, max_eval)
                    if beta <= alpha:
                        break
                return max_eval
            else:
                min_eval = float('inf')
                for m in moves:
                    b[m] = opp
                    eval_score = minimax(b, depth + 1, alpha, beta, True)
                    b[m] = ' '
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, min_eval)
                    if beta <= alpha:
                        break
                return min_eval

        moves = get_moves(board)
        if not moves:
            return None
        best_score = -float('inf')
        best_move = None
        for m in moves:
            test_board = board[:]
            test_board[m] = self.symbol
            score = minimax(test_board, 0, -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_move = m
        return best_move
