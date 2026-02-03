"""
Agent Code: A2-TicTacToe
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-03 19:54:05
"""



import random

class TicTacToeAgent:
    """
    A smart Tic Tac Toe agent using minimax algorithm with alpha-beta pruning.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = O_MARK if symbol == X_MARK else X_MARK

    def make_move(self, board):
        """
        Return the index (0-8) of the cell to mark using minimax algorithm.
        """
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]

        if not available_moves:
            return None

        # If it's the first move and center is available, take it
        if len(available_moves) == 9:
            return 4

        # If it's the second move and we're X and center is taken, take a corner
        if len(available_moves) == 8 and board[4] != self.symbol and self.symbol == X_MARK:
            return random.choice([0, 2, 6, 8])

        # Use minimax to find the best move
        best_score = -float('inf')
        best_move = None

        for move in available_moves:
            board[move] = self.symbol
            score = self.minimax(board, 0, False, -float('inf'), float('inf'))
            board[move] = EMPTY

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def minimax(self, board, depth, is_maximizing, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning to evaluate board positions.
        """
        result = self.check_winner(board)
        if result is not None:
            if result == self.symbol:
                return 10 - depth
            elif result == self.opponent_symbol:
                return -10 + depth
            else:
                return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == EMPTY:
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False, alpha, beta)
                    board[i] = EMPTY
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == EMPTY:
                    board[i] = self.opponent_symbol
                    score = self.minimax(board, depth + 1, True, alpha, beta)
                    board[i] = EMPTY
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
            return best_score

    def check_winner(self, board):
        """
        Check if there's a winner or if the game is a draw.
        """
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8), # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8), # Columns
            (0, 4, 8), (2, 4, 6)             # Diagonals
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        if EMPTY not in board:
            return 'DRAW'
        return None
