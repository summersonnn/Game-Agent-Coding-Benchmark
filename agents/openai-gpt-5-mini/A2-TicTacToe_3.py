"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5-mini
Run: 5
Generated: 2026-02-04 17:55:46
"""



class TicTacToeAgent:
    """
    Strong Tic-Tac-Toe agent using minimax with alpha-beta style pruning and memoization.
    Returns optimal moves (from the agent's perspective) and handles immediate wins/blocks quickly.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opp = O_MARK if symbol == X_MARK else X_MARK
        self._cache = {}

    def _check_winner(self, board):
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

    def make_move(self, board):
        """
        Return the index (0-8) of the cell to mark.
        """
        available = [i for i, v in enumerate(board) if v == EMPTY]
        if not available:
            return None

        # Quick immediate-win
        for m in available:
            temp = list(board)
            temp[m] = self.symbol
            if self._check_winner(temp) == self.symbol:
                return m

        # Quick block of opponent immediate-win
        for m in available:
            temp = list(board)
            temp[m] = self.opp
            if self._check_winner(temp) == self.opp:
                return m

        # Minimax with memoization
        self._cache.clear()

        def minimax(board_tuple, current):
            key = (board_tuple, current)
            if key in self._cache:
                return self._cache[key]

            winner = self._check_winner(list(board_tuple))
            if winner:
                if winner == 'DRAW':
                    res = (0, None)
                elif winner == self.symbol:
                    res = (1, None)
                else:
                    res = (-1, None)
                self._cache[key] = res
                return res

            # Move ordering heuristic: center, corners, sides
            order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
            moves = [m for m in order if board_tuple[m] == EMPTY]

            if current == self.symbol:
                best_score = -2
                best_move = None
                for m in moves:
                    new_board = list(board_tuple)
                    new_board[m] = current
                    next_current = X_MARK if current == O_MARK else O_MARK
                    score, _ = minimax(tuple(new_board), next_current)
                    if score > best_score:
                        best_score = score
                        best_move = m
                        if best_score == 1:
                            break
                res = (best_score, best_move)
                self._cache[key] = res
                return res
            else:
                best_score = 2
                best_move = None
                for m in moves:
                    new_board = list(board_tuple)
                    new_board[m] = current
                    next_current = X_MARK if current == O_MARK else O_MARK
                    score, _ = minimax(tuple(new_board), next_current)
                    if score < best_score:
                        best_score = score
                        best_move = m
                        if best_score == -1:
                            break
                res = (best_score, best_move)
                self._cache[key] = res
                return res

        # Determine whose turn it is on this board; if inconsistent, assume agent's turn
        x_count = board.count(X_MARK)
        o_count = board.count(O_MARK)
        current_turn = X_MARK if x_count <= o_count else O_MARK
        if current_turn != self.symbol:
            current_turn = self.symbol

        _, move = minimax(tuple(board), current_turn)
        if move is None:
            # Fallback: prefer center, then corners, then any available
            if 4 in available:
                return 4
            for c in (0, 2, 6, 8):
                if c in available:
                    return c
            return random.choice(available)
        return move
