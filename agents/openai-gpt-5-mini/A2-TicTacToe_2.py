"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    """
    Strong Tic-Tac-Toe agent using minimax with alpha-beta pruning and simple tactical checks.
    Prefers faster wins and delays losses (to improve tie-breaker score).
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opp = O_MARK if symbol == X_MARK else X_MARK
        self._cache = {}

    def make_move(self, board):
        # Return a legal move index (0-8). Fall back to a random legal move on error.
        available = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available:
            return 0  # defensive fallback

        try:
            # 1) Immediate winning move
            for m in available:
                if self._would_win(board, m, self.symbol):
                    return m

            # 2) Block opponent's immediate winning move (if only one)
            opp_threats = [m for m in available if self._would_win(board, m, self.opp)]
            if len(opp_threats) == 1:
                return opp_threats[0]

            # 3) Use minimax (maximize our score, which prefers earlier wins via remaining empties)
            score, move = self._minimax(tuple(board), self.symbol, -float('inf'), float('inf'))
            if move is None:
                return random.choice(available)
            # ensure chosen move is available (safety)
            if board[move] != EMPTY:
                return random.choice(available)
            return move
        except Exception:
            return random.choice(available)

    # ---------- Helper methods ----------
    def _check_winner(self, board):
        # board may be tuple or list
        b = board
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6),
        ]
        for a, c, d in win_conditions:
            if b[a] == b[c] == b[d] != EMPTY:
                return b[a]
        if EMPTY not in b:
            return 'DRAW'
        return None

    def _would_win(self, board, pos, player):
        if board[pos] != EMPTY:
            return False
        # mutate a list copy for the check
        temp = list(board)
        temp[pos] = player
        return self._check_winner(temp) == player

    def _other(self, player):
        return self.opp if player == self.symbol else self.symbol

    def _minimax(self, board_tuple, current_player, alpha, beta):
        """
        Returns (score, best_move) for the given board state and current_player.
        Score uses terminal values:
         - win for self.symbol: +(1000 + empty_cells_remaining)
         - loss for self.symbol: -(1000 + empty_cells_remaining)
         - draw: 0
        This makes the agent prefer earlier wins (more empty cells remaining) and delay losses.
        """
        # caching by (board_tuple, current_player)
        key = (board_tuple, current_player)
        if key in self._cache:
            return self._cache[key]

        board = list(board_tuple)
        winner = self._check_winner(board)
        if winner is not None:
            if winner == 'DRAW':
                res = (0, None)
            elif winner == self.symbol:
                res = (1000 + board.count(EMPTY), None)
            else:
                res = (-(1000 + board.count(EMPTY)), None)
            self._cache[key] = res
            return res

        # generate moves in a heuristic order: center, corners, edges
        preferred = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        moves = [m for m in preferred if board[m] == EMPTY]

        if current_player == self.symbol:
            best_score = -float('inf')
            best_move = None
            for m in moves:
                board[m] = current_player
                child_score, _ = self._minimax(tuple(board), self._other(current_player), alpha, beta)
                board[m] = EMPTY
                # prefer higher score; break ties randomly to add variation
                if child_score > best_score or (child_score == best_score and random.random() < 0.5):
                    best_score = child_score
                    best_move = m
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break
            res = (best_score, best_move)
            self._cache[key] = res
            return res
        else:
            best_score = float('inf')
            best_move = None
            for m in moves:
                board[m] = current_player
                child_score, _ = self._minimax(tuple(board), self._other(current_player), alpha, beta)
                board[m] = EMPTY
                if child_score < best_score or (child_score == best_score and random.random() < 0.5):
                    best_score = child_score
                    best_move = m
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            res = (best_score, best_move)
            self._cache[key] = res
            return res
