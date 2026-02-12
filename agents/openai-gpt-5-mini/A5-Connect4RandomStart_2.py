"""
Agent Code: A5-Connect4RandomStart
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-12 14:50:42
"""



import random

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        name: str - agent name (for logging if desired)
        symbol: 'R' or 'Y' - the agent's disc
        """
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        Returns an int column index (0-6).
        """
        ROWS = 6
        COLS = 7
        EMPTY = ' '

        def get_valid_cols(b):
            return [c for c in range(COLS) if b[0][c] == EMPTY]

        def simulate_drop(b, col, disc):
            nb = [row[:] for row in b]
            for r in range(ROWS - 1, -1, -1):
                if nb[r][col] == EMPTY:
                    nb[r][col] = disc
                    return nb, r
            return None, None

        def check_winner(b):
            # Horizontal
            for r in range(ROWS):
                for c in range(COLS - 3):
                    if b[r][c] != EMPTY and b[r][c] == b[r][c+1] == b[r][c+2] == b[r][c+3]:
                        return b[r][c]
            # Vertical
            for r in range(ROWS - 3):
                for c in range(COLS):
                    if b[r][c] != EMPTY and b[r][c] == b[r+1][c] == b[r+2][c] == b[r+3][c]:
                        return b[r][c]
            # Diagonal /
            for r in range(3, ROWS):
                for c in range(COLS - 3):
                    if b[r][c] != EMPTY and b[r][c] == b[r-1][c+1] == b[r-2][c+2] == b[r-3][c+3]:
                        return b[r][c]
            # Diagonal \
            for r in range(ROWS - 3):
                for c in range(COLS - 3):
                    if b[r][c] != EMPTY and b[r][c] == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3]:
                        return b[r][c]
            return None

        try:
            me = self.symbol
            opp = 'R' if me == 'Y' else 'Y'
            valid = get_valid_cols(board)
            if not valid:
                # No valid moves; return a safe default
                return 0

            # 1) Immediate winning move
            winning = []
            for c in valid:
                nb, _ = simulate_drop(board, c, me)
                if nb and check_winner(nb) == me:
                    winning.append(c)
            if winning:
                return random.choice(winning)

            # 2) Block opponent immediate win(s)
            opp_wins = []
            for c in valid:
                nb, _ = simulate_drop(board, c, opp)
                if nb and check_winner(nb) == opp:
                    opp_wins.append(c)
            if len(opp_wins) == 1:
                return opp_wins[0]
            if len(opp_wins) > 1:
                # Multiple immediate threats — cannot always block all;
                # try to block one (randomly) to delay loss, or pick any valid.
                return random.choice(opp_wins)

            # 3) Create a fork (move that gives >=2 immediate wins next turn)
            forks = []
            for c in valid:
                nb, _ = simulate_drop(board, c, me)
                if not nb:
                    continue
                nb_valid = get_valid_cols(nb)
                wins_after = 0
                for c2 in nb_valid:
                    nb2, _ = simulate_drop(nb, c2, me)
                    if nb2 and check_winner(nb2) == me:
                        wins_after += 1
                if wins_after >= 2:
                    forks.append(c)
            if forks:
                return random.choice(forks)

            # 4) Prefer center columns while avoiding moves that let opponent win immediately
            preference = [3, 2, 4, 1, 5, 0, 6]
            safe_choices = []
            for c in preference:
                if c not in valid:
                    continue
                nb, _ = simulate_drop(board, c, me)
                if not nb:
                    continue
                # Does opponent have an immediate winning reply after this move?
                opp_can_win = False
                nb_valid = get_valid_cols(nb)
                for c2 in nb_valid:
                    nb2, _ = simulate_drop(nb, c2, opp)
                    if nb2 and check_winner(nb2) == opp:
                        opp_can_win = True
                        break
                if not opp_can_win:
                    safe_choices.append(c)
            if safe_choices:
                return random.choice(safe_choices)

            # 5) Fallback: pick a valid column (prefer center by order)
            for c in preference:
                if c in valid:
                    return c
            return random.choice(valid)

        except Exception:
            # On unexpected error, return a random valid move (engine will handle crashes/timeouts)
            valid = [c for c in range(7) if board[0][c] == EMPTY]
            return random.choice(valid) if valid else 0
