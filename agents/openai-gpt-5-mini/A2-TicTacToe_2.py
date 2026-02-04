"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-04 16:48:42
"""



class TicTacToeAgent:
    """
    Strong Tic-Tac-Toe agent using minimax (with simple tactical shortcuts).
    Only the class definition is output as requested.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'

    def make_move(self, board):
        """
        Return index (0-8) for the chosen move.
        board: list of 9 strings (X, O, or EMPTY).
        """
        # Helper constants assumed to exist in the module
        try:
            EMPTY  # noqa: F821
            X_MARK  # noqa: F821
            O_MARK  # noqa: F821
        except NameError:
            # Fallback in case constants aren't available
            EMPTY = ' '
            X_MARK = 'X'
            O_MARK = 'O'

        # Helper functions
        def other(player):
            return O_MARK if player == X_MARK else X_MARK

        def check_winner(b):
            wins = [
                (0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6)
            ]
            for a, c, d in wins:
                if b[a] == b[c] == b[d] != EMPTY:
                    return b[a]
            if EMPTY not in b:
                return 'DRAW'
            return None

        available = [i for i, s in enumerate(board) if s == EMPTY]
        if not available:
            return None

        me = self.symbol
        opp = other(me)

        # Immediate winning move
        for mv in available:
            board[mv] = me
            if check_winner(board) == me:
                board[mv] = EMPTY
                return mv
            board[mv] = EMPTY

        # Block opponent immediate win
        for mv in available:
            board[mv] = opp
            if check_winner(board) == opp:
                board[mv] = EMPTY
                return mv
            board[mv] = EMPTY

        # Prefer center if available (good heuristic)
        if 4 in available:
            return 4

        # Minimax algorithm with depth-sensitive scoring (favors faster wins)
        def minimax(b, current_player, depth):
            result = check_winner(b)
            if result is not None:
                if result == 'DRAW':
                    return 0
                return (10 - depth) if result == me else (depth - 10)

            moves = [i for i, s in enumerate(b) if s == EMPTY]
            if current_player == me:
                best_val = -9999
                for m in moves:
                    b[m] = current_player
                    val = minimax(b, other(current_player), depth + 1)
                    b[m] = EMPTY
                    if val > best_val:
                        best_val = val
                return best_val
            else:
                best_val = 9999
                for m in moves:
                    b[m] = current_player
                    val = minimax(b, other(current_player), depth + 1)
                    b[m] = EMPTY
                    if val < best_val:
                        best_val = val
                return best_val

        # Choose best move(s) according to minimax
        best_score = -9999
        best_moves = []
        for mv in available:
            board[mv] = me
            score = minimax(board, other(me), 1)
            board[mv] = EMPTY
            if score > best_score:
                best_score = score
                best_moves = [mv]
            elif score == best_score:
                best_moves.append(mv)

        # Fallback: choose randomly among best moves
        return random.choice(best_moves) if best_moves else random.choice(available)
