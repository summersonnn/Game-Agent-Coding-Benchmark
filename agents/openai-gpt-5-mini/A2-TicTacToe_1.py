"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-11 20:47:17
"""

from functools import lru_cache

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'

    def make_move(self, board):
        try:
            # Basic validation
            if not isinstance(board, (list, tuple)) or len(board) != 9:
                available = [i for i, s in enumerate(board) if s == ' '] if isinstance(board, (list, tuple)) else []
                return random.choice(available) if available else None

            board_t = tuple(board)
            my = self.symbol
            opp = O_MARK if my == X_MARK else X_MARK  # use constants from game module
            # determine whose turn it is (X moves when counts equal)
            x_count = board_t.count(X_MARK)
            o_count = board_t.count(O_MARK)
            current_turn = X_MARK if x_count == o_count else O_MARK

            win_cons = (
                (0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6),
            )

            def check_winner(bt):
                for a, b, c in win_cons:
                    v = bt[a]
                    if v != ' ' and v == bt[b] == bt[c]:
                        return v
                if ' ' not in bt:
                    return 'DRAW'
                return None

            available_moves = [i for i, s in enumerate(board_t) if s == ' ']
            if not available_moves:
                return None

            # Quick immediate win (take it)
            for m in available_moves:
                nb = list(board_t)
                nb[m] = my
                if check_winner(tuple(nb)) == my:
                    return m

            # Detect opponent immediate winning squares
            opp_wins = set()
            for m in available_moves:
                nb = list(board_t)
                nb[m] = opp
                if check_winner(tuple(nb)) == opp:
                    opp_wins.add(m)
            # If opponent has exactly one immediate winning move, block it
            if len(opp_wins) == 1:
                block = next(iter(opp_wins))
                # prefer center/corner when blocking (if multiple equivalent choices exist)
                if block in available_moves:
                    return block

            # Minimax with caching. Utility: (outcome, tie_metric)
            # outcome: 1 = win for self, 0 = draw, -1 = loss for self
            # tie_metric: for wins/losses use max(empty_cells, 3) (matches competition tie-breaker); for draws 0
            @lru_cache(maxsize=None)
            def minimax(bt, turn):
                # Terminal check
                for a, b, c in win_cons:
                    v = bt[a]
                    if v != ' ' and v == bt[b] == bt[c]:
                        if v == my:
                            return (1, max(bt.count(' '), 3))
                        else:
                            return (-1, max(bt.count(' '), 3))
                if ' ' not in bt:
                    return (0, 0)

                maximizing = (turn == my)
                next_turn = O_MARK if turn == X_MARK else X_MARK

                best = None
                # iterate possible moves
                for i, spot in enumerate(bt):
                    if spot == ' ':
                        nb = list(bt)
                        nb[i] = turn
                        child = minimax(tuple(nb), next_turn)
                        if best is None:
                            best = child
                        else:
                            a_score, a_tb = child
                            b_score, b_tb = best
                            if a_score != b_score:
                                choose_a = (a_score > b_score) if maximizing else (a_score < b_score)
                            else:
                                # tie-break on tie_metric, orientation depends on maximizing/minimizing
                                if a_score == 1:
                                    choose_a = (a_tb > b_tb) if maximizing else (a_tb < b_tb)
                                elif a_score == -1:
                                    choose_a = (a_tb < b_tb) if maximizing else (a_tb > b_tb)
                                else:  # draw
                                    choose_a = (a_tb > b_tb) if maximizing else (a_tb < b_tb)
                            if choose_a:
                                best = child
                return best

            # Evaluate each candidate move (place my symbol and then let opponent move)
            results = []
            for m in available_moves:
                nb = list(board_t)
                nb[m] = my
                win = check_winner(tuple(nb))
                if win == my:
                    tie = max(nb.count(' '), 3)
                    results.append((m, (1, tie)))
                else:
                    # opponent moves next
                    res = minimax(tuple(nb), opp)
                    results.append((m, res))

            # Choose best move according to minimax results (we are the maximizer at this decision)
            best_move = None
            best_val = None
            for m, val in results:
                if best_val is None:
                    best_move, best_val = m, val
                    continue
                a_score, a_tb = val
                b_score, b_tb = best_val
                if a_score != b_score:
                    choose = a_score > b_score
                else:
                    if a_score == 1:
                        choose = a_tb > b_tb
                    elif a_score == -1:
                        choose = a_tb < b_tb
                    else:
                        choose = a_tb > b_tb
                if choose:
                    best_move, best_val = m, val

            # Tie-break among equal best moves: prefer center, then corners, then edges
            candidates = [m for m, v in results if v == best_val]
            if len(candidates) > 1:
                if 4 in candidates:
                    return 4
                for c in (0, 2, 6, 8):
                    if c in candidates:
                        return c
                return candidates[0]

            return best_move

        except Exception:
            # On any unexpected error, return a random valid move
            pass

        moves = [i for i, s in enumerate(board) if s == ' ']
        return random.choice(moves) if moves else None
