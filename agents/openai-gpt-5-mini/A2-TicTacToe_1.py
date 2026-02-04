"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-04 16:48:42
"""



class TicTacToeAgent:
    """
    Unbeatable Tic-Tac-Toe agent using minimax with alpha-beta pruning.
    Returns optimal moves and prefers center/corners when equal.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent = O_MARK if symbol == X_MARK else X_MARK
        # small cache to avoid recomputing identical states at same depth
        self._cache = {}

    def make_move(self, board):
        """
        Return the index (0-8) of the cell to mark.
        Does not mutate the incoming board.
        """
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return None
        # If only one move, take it
        if len(available_moves) == 1:
            return available_moves[0]
        # If board is empty (we are first), take center if possible
        if len(available_moves) == 9:
            return 4 if 4 in available_moves else random.choice(available_moves)

        # Work on a copy so we don't mutate the passed board
        local_board = board[:]

        # Immediate winning move
        for m in available_moves:
            local_board[m] = self.symbol
            if self._check_winner(local_board) == self.symbol:
                return m
            local_board[m] = EMPTY

        # Immediate block of opponent's win
        for m in available_moves:
            local_board[m] = self.opponent
            if self._check_winner(local_board) == self.opponent:
                return m
            local_board[m] = EMPTY

        # Use minimax to choose the best move
        best_score = -float('inf')
        best_moves = []
        preferred_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        moves = [m for m in preferred_order if m in available_moves]

        # Clear cache per move to avoid unbounded growth across many games
        # (optional) keep cache to speed recursion within this move
        self._cache.clear()

        for move in moves:
            local_board[move] = self.symbol
            score = self._minimax(local_board, is_maximizing=False, depth=1,
                                  alpha=-float('inf'), beta=float('inf'))
            local_board[move] = EMPTY
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        if not best_moves:
            return random.choice(available_moves)

        # pick best move according to preferred ordering to be deterministic
        for p in preferred_order:
            if p in best_moves:
                return p
        return best_moves[0]

    def _minimax(self, board, is_maximizing, depth, alpha, beta):
        """
        Minimax recursion with alpha-beta pruning.
        Scoring: win = 10 - depth, loss = depth - 10, draw = 0
        Cache key includes depth because returned score depends on depth.
        """
        key = (tuple(board), is_maximizing, depth)
        if key in self._cache:
            return self._cache[key]

        winner = self._check_winner(board)
        if winner is not None:
            if winner == 'DRAW':
                val = 0
            elif winner == self.symbol:
                val = 10 - depth
            else:
                val = depth - 10
            self._cache[key] = val
            return val

        available_moves = [i for i, s in enumerate(board) if s == EMPTY]
        preferred_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        moves = [m for m in preferred_order if m in available_moves]

        if is_maximizing:
            max_eval = -float('inf')
            for m in moves:
                board[m] = self.symbol
                eval_score = self._minimax(board, False, depth + 1, alpha, beta)
                board[m] = EMPTY
                if eval_score > max_eval:
                    max_eval = eval_score
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            self._cache[key] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for m in moves:
                board[m] = self.opponent
                eval_score = self._minimax(board, True, depth + 1, alpha, beta)
                board[m] = EMPTY
                if eval_score < min_eval:
                    min_eval = eval_score
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            self._cache[key] = min_eval
            return min_eval

    def _check_winner(self, board):
        """
        Returns 'X' or 'O' if there is a winner, 'DRAW' if board is full with no winner,
        or None if the game is still ongoing.
        """
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != EMPTY:
                return board[a]
        if EMPTY not in board:
            return 'DRAW'
        return None
