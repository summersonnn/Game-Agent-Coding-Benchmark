"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-04 16:49:47
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return None

        maximizing_symbol = self.symbol
        minimizing_symbol = O_MARK if self.symbol == X_MARK else X_MARK

        best_score = -float('inf')
        best_moves = []
        
        for move in available_moves:
            new_board = board[:]
            new_board[move] = self.symbol
            score = self.minimax(new_board, False, -float('inf'), float('inf'), 
                                 maximizing_symbol, minimizing_symbol, 1)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
                
        return random.choice(best_moves)

    def minimax(self, board, is_maximizing, alpha, beta, maximizing_symbol, minimizing_symbol, depth):
        winner = self.check_winner(board)
        if winner == maximizing_symbol:
            return 10 - depth
        elif winner == minimizing_symbol:
            return depth - 10
        elif winner == 'DRAW':
            return 0

        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        
        if is_maximizing:
            best_score = -float('inf')
            for move in available_moves:
                new_board = board[:]
                new_board[move] = maximizing_symbol
                score = self.minimax(new_board, False, alpha, beta, 
                                     maximizing_symbol, minimizing_symbol, depth + 1)
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score
        else:
            best_score = float('inf')
            for move in available_moves:
                new_board = board[:]
                new_board[move] = minimizing_symbol
                score = self.minimax(new_board, True, alpha, beta, 
                                     maximizing_symbol, minimizing_symbol, depth + 1)
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score

    def check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        if EMPTY not in board:
            return 'DRAW'
        return None
