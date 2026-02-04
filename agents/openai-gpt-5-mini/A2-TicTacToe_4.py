"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5-mini
Run: 4
Generated: 2026-02-04 16:48:42
"""



class TicTacToeAgent:
    """
    Strong Tic-Tac-Toe agent using Minimax with alpha-beta pruning.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent = X_MARK if symbol == O_MARK else O_MARK

    def make_move(self, board):
        """
        Return the index (0-8) of the cell to mark.
        """
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return None

        # If board is empty, take center (strong opening)
        if len(available_moves) == 9:
            return 4

        # Immediate win
        for m in available_moves:
            board[m] = self.symbol
            if self._check_winner(board) == self.symbol:
                board[m] = EMPTY
                return m
            board[m] = EMPTY

        # Immediate block
        for m in available_moves:
            board[m] = self.opponent
            if self._check_winner(board) == self.opponent:
                board[m] = EMPTY
                return m
            board[m] = EMPTY

        # Use minimax to pick best move
        _, move = self._minimax(board, True, -float('inf'), float('inf'))
        if move is None:
            return random.choice(available_moves)
        return move

    def _check_winner(self, board):
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

    def _minimax(self, board, is_maximizing, alpha, beta):
        winner = self._check_winner(board)
        if winner is not None:
            if winner == 'DRAW':
                return 0, None
            return (1, None) if winner == self.symbol else (-1, None)

        best_move = None
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == EMPTY:
                    board[i] = self.symbol
                    eval_score, _ = self._minimax(board, False, alpha, beta)
                    board[i] = EMPTY
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = i
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == EMPTY:
                    board[i] = self.opponent
                    eval_score, _ = self._minimax(board, True, alpha, beta)
                    board[i] = EMPTY
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = i
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            return min_eval, best_move
