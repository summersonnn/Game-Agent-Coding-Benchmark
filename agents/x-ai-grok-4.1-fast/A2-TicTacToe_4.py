"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4.1-fast
Run: 4
Generated: 2026-02-04 17:03:29
"""



# No additional imports needed

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opp_symbol = O_MARK if symbol == X_MARK else X_MARK

    def is_winner(self, board, symbol):
        wins = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        return any(board[i] == symbol for i in win for win in wins)

    def get_available_moves(self, board):
        preferred_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        return [i for i in preferred_order if board[i] == EMPTY]

    def minimax(self, board, is_maximizing, alpha=-float('inf'), beta=float('inf')):
        if self.is_winner(board, self.symbol):
            return 1
        if self.is_winner(board, self.opp_symbol):
            return -1
        if EMPTY not in board:
            return 0

        if is_maximizing:
            max_eval = -float('inf')
            for i in self.get_available_moves(board):
                board[i] = self.symbol
                eval_score = self.minimax(board, False, alpha, beta)
                board[i] = EMPTY
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i in self.get_available_moves(board):
                board[i] = self.opp_symbol
                eval_score = self.minimax(board, True, alpha, beta)
                board[i] = EMPTY
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, board):
        available = self.get_available_moves(board)
        if not available:
            return None

        # Check for immediate win
        for move in available:
            board[move] = self.symbol
            if self.is_winner(board, self.symbol):
                board[move] = EMPTY
                return move
            board[move] = EMPTY

        # Check for immediate block
        for move in available:
            board[move] = self.opp_symbol
            if self.is_winner(board, self.opp_symbol):
                board[move] = EMPTY
                return move
            board[move] = EMPTY

        # Minimax for best move
        best_score = -float('inf')
        best_move = None
        for move in available:
            board[move] = self.symbol
            score = self.minimax(board, False)
            board[move] = EMPTY
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
