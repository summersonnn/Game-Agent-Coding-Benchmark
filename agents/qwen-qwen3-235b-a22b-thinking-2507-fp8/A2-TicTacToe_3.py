"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 3
Generated: 2026-02-04 16:49:47
"""



import random

class TicTacToeAgent:
    """
    Your agent implementation goes here.
    Implement smart logic to beat your opponent.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def get_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        if ' ' not in board:
            return 'DRAW'
        return None

    def minimax(self, board, depth, is_maximizing, alpha, beta):
        winner = self.get_winner(board)
        if winner == self.symbol:
            return 10 - depth
        elif winner == 'DRAW':
            return 0
        elif winner is not None:
            return depth - 10

        if is_maximizing:
            best_score = -1000
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    best_score = max(best_score, score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
            return best_score
        else:
            best_score = 1000
            opponent_symbol = 'X' if self.symbol == 'O' else 'O'
            for i in range(9):
                if board[i] == ' ':
                    board[i] = opponent_symbol
                    score = self.minimax(board, depth + 1, True, alpha, beta)
                    board[i] = ' '
                    best_score = min(best_score, score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
            return best_score

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return None

        board_copy = board[:]
        
        for move in available_moves:
            board_copy[move] = self.symbol
            if self.get_winner(board_copy) == self.symbol:
                board_copy[move] = ' '
                return move
            board_copy[move] = ' '

        best_score = -1000
        best_moves = []
        for move in available_moves:
            board_copy[move] = self.symbol
            score = self.minimax(board_copy, 0, False, -1000, 1000)
            board_copy[move] = ' '
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
                
        return random.choice(best_moves)
