"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-5@preset/fp8
Run: 1
Generated: 2026-02-11 21:23:38
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'X' if symbol == 'O' else 'O'

    def make_move(self, board):
        empty = self._empty_cells(board)
        if len(empty) == 1:
            return empty[0]

        # Immediate win check
        for move in empty:
            board[move] = self.symbol
            if self._check_winner(board) == self.symbol:
                board[move] = ' '
                return move
            board[move] = ' '

        # Minimax with alpha-beta pruning
        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        for move in empty:
            board[move] = self.symbol
            score = self._minimax(board, self.opponent, 1, alpha, beta)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)

        return best_move

    def _minimax(self, board, player, depth, alpha, beta):
        result = self._check_winner(board)
        if result is not None:
            if result == self.symbol:
                return 10 - depth
            elif result == self.opponent:
                return -10 + depth
            else:
                return 0

        empty = self._empty_cells(board)
        if player == self.symbol:  # maximizing turn
            max_eval = -float('inf')
            for move in empty:
                board[move] = player
                eval_score = self._minimax(board, self.opponent, depth+1, alpha, beta)
                board[move] = ' '
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:  # minimizing turn
            min_eval = float('inf')
            for move in empty:
                board[move] = player
                eval_score = self._minimax(board, self.symbol, depth+1, alpha, beta)
                board[move] = ' '
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def _check_winner(self, board):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a,b,c in wins:
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _empty_cells(self, board):
        return [i for i, v in enumerate(board) if v == ' ']
