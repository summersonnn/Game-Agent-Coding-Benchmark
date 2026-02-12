"""
Agent Code: A2-TicTacToe
Model: xiaomi/mimo-v2-flash
Run: 1
Generated: 2026-02-11 20:47:17
"""



import random

EMPTY = ' '

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        
    def check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != EMPTY:
                return board[a]
        if EMPTY not in board:
            return 'DRAW'
        return None

    def minimax(self, board, depth, is_maximizing, alpha, beta):
        winner = self.check_winner(board)
        if winner is not None:
            if winner == self.symbol:
                return 10 - depth
            elif winner == self.opponent_symbol:
                return depth - 10
            else:
                return 0
        
        available_moves = [i for i, cell in enumerate(board) if cell == EMPTY]
        
        if is_maximizing:
            best_score = float('-inf')
            for move in available_moves:
                new_board = board[:]
                new_board[move] = self.symbol
                score = self.minimax(new_board, depth + 1, False, alpha, beta)
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score
        else:
            best_score = float('inf')
            for move in available_moves:
                new_board = board[:]
                new_board[move] = self.opponent_symbol
                score = self.minimax(new_board, depth + 1, True, alpha, beta)
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score

    def make_move(self, board):
        available_moves = [i for i, cell in enumerate(board) if cell == EMPTY]
        if not available_moves:
            return None
            
        best_score = float('-inf')
        best_moves = []
        alpha = float('-inf')
        beta = float('inf')
        
        for move in available_moves:
            new_board = board[:]
            new_board[move] = self.symbol
            score = self.minimax(new_board, 0, False, alpha, beta)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
            alpha = max(alpha, best_score)
            
        return random.choice(best_moves)
