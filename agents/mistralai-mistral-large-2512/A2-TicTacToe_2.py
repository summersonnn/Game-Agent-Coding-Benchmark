"""
Agent Code: A2-TicTacToe
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']

        # If it's the first move, take center or a corner
        if len(available_moves) == 9:
            return 4 if board[4] == ' ' else random.choice([0, 2, 6, 8])
        elif len(available_moves) == 8 and board[4] == self.symbol:
            return random.choice([0, 2, 6, 8])

        # Check for immediate winning move or block
        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.symbol
            if self.check_winner(temp_board) == self.symbol:
                return move

        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.opponent_symbol
            if self.check_winner(temp_board) == self.opponent_symbol:
                return move

        # Use minimax for optimal move
        best_score = -float('inf')
        best_move = random.choice(available_moves)

        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.symbol
            score = self.minimax(temp_board, 0, False, -float('inf'), float('inf'))
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def minimax(self, board, depth, is_maximizing, alpha, beta):
        winner = self.check_winner(board)

        if winner == self.symbol:
            return 10 - depth
        elif winner == self.opponent_symbol:
            return depth - 10
        elif winner == 'DRAW':
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent_symbol
                    score = self.minimax(board, depth + 1, True, alpha, beta)
                    board[i] = ' '
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
            return best_score

    def check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6),              # Diagonals
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        if ' ' not in board:
            return 'DRAW'
        return None
