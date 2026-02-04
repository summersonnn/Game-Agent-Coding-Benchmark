"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4.1-fast
Run: 5
Generated: 2026-02-04 17:08:17
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'

    def available_moves(self, board):
        return [i for i, spot in enumerate(board) if spot == ' ']

    def get_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def minimax(self, board, depth, alpha, beta, is_maximizing, opp_symbol):
        winner = self.get_winner(board)
        if winner == self.symbol:
            return 10 - depth
        if winner == opp_symbol:
            return depth - 10
        if winner == 'DRAW':
            return 0

        if is_maximizing:
            value = -float('inf')
            for move in self.available_moves(board):
                board[move] = self.symbol
                value = max(value, self.minimax(board, depth + 1, alpha, beta, False, opp_symbol))
                board[move] = ' '
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for move in self.available_moves(board):
                board[move] = opp_symbol
                value = min(value, self.minimax(board, depth + 1, alpha, beta, True, opp_symbol))
                board[move] = ' '
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def make_move(self, board):
        available = self.available_moves(board)
        if not available:
            return None
        opp_symbol = 'O' if self.symbol == 'X' else 'X'
        move_priority = {4: 3, 0: 2, 2: 2, 6: 2, 8: 2, 1: 1, 3: 1, 5: 1, 7: 1}
        available.sort(key=lambda m: move_priority.get(m, 0), reverse=True)
        best_score = -float('inf')
        best_move = None
        for move in available:
            board[move] = self.symbol
            score = self.minimax(board, 0, -float('inf'), float('inf'), False, opp_symbol)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
            if best_score == 10:
                break
        return best_move
