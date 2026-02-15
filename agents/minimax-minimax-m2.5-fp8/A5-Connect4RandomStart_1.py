"""
Agent Code: A5-Connect4RandomStart
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-14 19:46:39
"""



import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        me = self.symbol
        opp = 'Y' if me == 'R' else 'R'

        # ---------- helper functions ----------
        def check_winner(b):
            # horizontal
            for r in range(6):
                for c in range(4):
                    if b[r][c] != ' ' and b[r][c] == b[r][c+1] == b[r][c+2] == b[r][c+3]:
                        return b[r][c]
            # vertical
            for r in range(3):
                for c in range(7):
                    if b[r][c] != ' ' and b[r][c] == b[r+1][c] == b[r+2][c] == b[r+3][c]:
                        return b[r][c]
            # diagonal down‑right
            for r in range(3):
                for c in range(4):
                    if b[r][c] != ' ' and b[r][c] == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3]:
                        return b[r][c]
            # diagonal down‑left
            for r in range(3):
                for c in range(3, 7):
                    if b[r][c] != ' ' and b[r][c] == b[r+1][c-1] == b[r+2][c-2] == b[r+3][c-3]:
                        return b[r][c]
            return None

        def valid_moves(b):
            return [c for c in range(7) if b[0][c] == ' ']

        def drop_piece(b, col, piece):
            new_board = [row[:] for row in b]
            for r in range(5, -1, -1):
                if new_board[r][col] == ' ':
                    new_board[r][col] = piece
                    return new_board
            return None  # column full (should not happen for valid moves)

        def evaluate(b):
            """Static evaluation from the perspective of `me`."""
            w = check_winner(b)
            if w == me:
                return 1_000_000
            if w == opp:
                return -1_000_000

            score = 0
            # column centre bias
            col_weights = [2, 3, 4, 6, 4, 3, 2]
            for r in range(6):
                for c in range(7):
                    if b[r][c] == me:
                        score += col_weights[c]
                    elif b[r][c] == opp:
                        score -= col_weights[c]

            # helper for a window of 4 cells
            def window_score(window):
                cnt_me = window.count(me)
                cnt_opp = window.count(opp)
                empty = window.count(' ')
                if cnt_me == 4:
                    return 100_000
                if cnt_me == 3 and empty == 1:
                    return 100
                if cnt_me == 2 and empty == 2:
                    return 10
                if cnt_me == 1 and empty == 3:
                    return 1
                if cnt_opp == 4:
                    return -100_000
                if cnt_opp == 3 and empty == 1:
                    return -100
                if cnt_opp == 2 and empty == 2:
                    return -10
                if cnt_opp == 1 and empty == 3:
                    return -1
                return 0

            # horizontal windows
            for r in range(6):
                for c in range(4):
                    window = [b[r][c+i] for i in range(4)]
                    score += window_score(window)
            # vertical windows
            for r in range(3):
                for c in range(7):
                    window = [b[r+i][c] for i in range(4)]
                    score += window_score(window)
            # diagonal down‑right
            for r in range(3):
                for c in range(4):
                    window = [b[r+i][c+i] for i in range(4)]
                    score += window_score(window)
            # diagonal down‑left
            for r in range(3):
                for c in range(3, 7):
                    window = [b[r+i][c-i] for i in range(4)]
                    score += window_score(window)

            return score

        def order_moves(b, player):
            """Return columns ordered by static evaluation for the given player."""
            moves = []
            for col in valid_moves(b):
                nb = drop_piece(b, col, player)
                if nb is None:
                    continue
                # evaluate from the perspective of the original agent
                sc = evaluate(nb)
                moves.append((sc, col))
            if player == me:
                moves.sort(reverse=True, key=lambda x: x[0])   # best for us first
            else:
                moves.sort(key=lambda x: x[0])                  # worst for us first (for pruning)
            return [col for _, col in moves]

        # ---------- minimax with alpha‑beta ----------
        def minimax(b, depth, alpha, beta, maximizing):
            winner = check_winner(b)
            if winner == me:
                return 1_000_000
            if winner == opp:
                return -1_000_000
            if not valid_moves(b) or depth == 0:
                return evaluate(b)

            if maximizing:
                max_eval = -float('inf')
                for col in order_moves(b, me):
                    nb = drop_piece(b, col, me)
                    ev = minimax(nb, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, ev)
                    alpha = max(alpha, ev)
                    if beta <= alpha:
                        break
                return max_eval
            else:
                min_eval = float('inf')
                for col in order_moves(b, opp):
                    nb = drop_piece(b, col, opp)
                    ev = minimax(nb, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, ev)
                    beta = min(beta, ev)
                    if beta <= alpha:
                        break
                return min_eval

        # ---------- choose a move ----------
        possible = valid_moves(board)
        if not possible:
            # board full – fallback (should not happen)
            return random.randint(0, 6)

        # immediate winning move?
        for col in possible:
            if check_winner(drop_piece(board, col, me)) == me:
                return col

        # evaluate each move with depth‑4 search (opponent’s turn first)
        best_score = -float('inf')
        best_moves = []
        for col in possible:
            next_board = drop_piece(board, col, me)
            val = minimax(next_board, depth=4, alpha=-float('inf'), beta=float('inf'), maximizing=False)
            if val > best_score:
                best_score = val
                best_moves = [col]
            elif val == best_score:
                best_moves.append(col)

        return random.choice(best_moves)
