"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-04 16:49:47
"""



import random

class TicTacToeAgent:
    WIN_CONDITIONS = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def check_terminal(self, board, agent_symbol, opponent_symbol):
        for a, b, c in self.WIN_CONDITIONS:
            if board[a] == board[b] == board[c] == agent_symbol:
                return 10
            if board[a] == board[b] == board[c] == opponent_symbol:
                return -10
        if ' ' not in board:
            return 0
        return None

    def minimax(self, board, depth, alpha, beta, is_maximizing, agent_symbol, opponent_symbol):
        result = self.check_terminal(board, agent_symbol, opponent_symbol)
        if result is not None:
            if result == 10:
                return 10 - depth
            elif result == -10:
                return -10 + depth
            else:
                return 0
        
        if is_maximizing:
            best = -1000
            for i in range(9):
                if board[i] == ' ':
                    board[i] = agent_symbol
                    score = self.minimax(board, depth + 1, alpha, beta, False, agent_symbol, opponent_symbol)
                    board[i] = ' '
                    best = max(best, score)
                    alpha = max(alpha, best)
                    if beta <= alpha:
                        break
            return best
        else:
            best = 1000
            for i in range(9):
                if board[i] == ' ':
                    board[i] = opponent_symbol
                    score = self.minimax(board, depth + 1, alpha, beta, True, agent_symbol, opponent_symbol)
                    board[i] = ' '
                    best = min(best, score)
                    beta = min(beta, best)
                    if beta <= alpha:
                        break
            return best

    def make_move(self, board):
        opponent_symbol = 'O' if self.symbol == 'X' else 'X'
        available_moves = [i for i in range(9) if board[i] == ' ']
        if not available_moves:
            return None
        if len(available_moves) == 1:
            return available_moves[0]
        
        board_sim = board.copy()
        best_score = -1000
        best_move = None
        
        for move in available_moves:
            board_sim[move] = self.symbol
            score = self.minimax(board_sim, 1, -1000, 1000, False, self.symbol, opponent_symbol)
            board_sim[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
