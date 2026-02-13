"""
Agent Code: A2-TicTacToe
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-13 14:10:12
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'
    
    def make_move(self, board):
        # First, check if there's an immediate winning move
        for move in self.get_available_moves(board):
            if self.would_win(board, move, self.symbol):
                return move
        
        # Second, check if opponent is about to win and block
        for move in self.get_available_moves(board):
            if self.would_win(board, move, self.opponent):
                return move
        
        # Use minimax to find the best move
        best_score = float('-inf')
        best_move = None
        for move in self.get_available_moves(board):
            new_board = board[:]
            new_board[move] = self.symbol
            score = self.minimax(new_board, 0, False, float('-inf'), float('inf'))
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move is not None else random.choice(self.get_available_moves(board))
    
    def get_available_moves(self, board):
        return [i for i in range(9) if board[i] == ' ']
    
    def would_win(self, board, move, player):
        new_board = board[:]
        new_board[move] = player
        return self.check_winner(new_board) == player
    
    def check_winner(self, board):
        win_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in win_combinations:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        return None
    
    def minimax(self, board, depth, is_maximizing, alpha, beta):
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 10 - depth
        if winner == self.opponent:
            return depth - 10
        if not self.get_available_moves(board):
            return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in self.get_available_moves(board):
                new_board = board[:]
                new_board[move] = self.symbol
                eval = self.minimax(new_board, depth + 1, False, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in self.get_available_moves(board):
                new_board = board[:]
                new_board[move] = self.opponent
                eval = self.minimax(new_board, depth + 1, True, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
