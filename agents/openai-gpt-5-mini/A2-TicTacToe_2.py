"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-13 14:53:21
"""



class TicTacToeAgent:
    """
    Heuristic Tic-Tac-Toe agent for 5x5 (connect-3).
    Strategy highlights:
      - Immediate win
      - Immediate block
      - Create forks (moves creating >=2 threats)
      - Block opponent forks (prefer playing fork cell or reduce opponent forks)
      - Center preference
      - Heuristic scoring: maximize potential lines for self, minimize opponent immediate responses
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opp = 'O' if symbol == 'X' else 'X'

        # Precompute all winning 3-in-a-row lines on 5x5
        lines = []
        # Rows (5 rows, 3 starting columns)
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))
        # Columns (5 cols, 3 starting rows)
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))
        # Diagonals down-right
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))
        # Diagonals down-left
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))

        self.win_lines = lines
        # Map cell -> lines that include that cell for fast lookup
        self.cell_to_lines = {i: [] for i in range(25)}
        for line in self.win_lines:
            for pos in line:
                self.cell_to_lines[pos].append(line)

    def make_move(self, board):
        empties = [i for i, s in enumerate(board) if s == ' ']
        if not empties:
            return None

        opp = self.opp
        me = self.symbol

        # Helper: check if placing `sym` at pos would immediately win
        def is_winning_move(bd, pos, sym):
            for line in self.cell_to_lines[pos]:
                # find the two other positions
                a, b, c = line
                if pos == a:
                    other1, other2 = b, c
                elif pos == b:
                    other1, other2 = a, c
                else:
                    other1, other2 = a, b
                if bd[other1] == sym and bd[other2] == sym:
                    return True
            return False

        # Helper: number of "threats" (lines with exactly 2 of `sym` and 1 empty) after playing at pos
        def count_threats_after_move(bd, pos, sym):
            bd2 = bd[:] 
            bd2[pos] = sym
            threats = 0
            for line in self.cell_to_lines[pos]:
                a, b, c = line
                cnt_sym = (1 if bd2[a] == sym else 0) + (1 if bd2[b] == sym else 0) + (1 if bd2[c] == sym else 0)
                cnt_empty = (1 if bd2[a] == ' ' else 0) + (1 if bd2[b] == ' ' else 0) + (1 if bd2[c] == ' ' else 0)
                if cnt_sym == 2 and cnt_empty == 1:
                    threats += 1
            return threats

        # Helper: whether opponent has any immediate winning move after we play at pos
        def opponent_can_win_after(bd, pos):
            bd2 = bd[:]
            bd2[pos] = me
            for p in range(25):
                if bd2[p] == ' ':
                    if is_winning_move(bd2, p, opp):
                        return True
            return False

        # 1) Immediate win
        for m in empties:
            if is_winning_move(board, m, me):
                return m

        # 2) Immediate block
        opp_immediate_wins = [m for m in empties if is_winning_move(board, m, opp)]
        if opp_immediate_wins:
            # If there is a single immediate win, block it.
            # If there are multiple, prefer a blocking move that blocks multiple (intersection) if any.
            if len(opp_immediate_wins) == 1:
                return opp_immediate_wins[0]
            # try to find a move that blocks all (i.e., a cell present in all winning move positions)
            # Since opp_immediate_wins are empty positions themselves, intersection might be empty;
            # fall back to block the first or a move that reduces opponent forks.
            # Try to choose a blocking cell that avoids giving opponent another immediate win
            for blk in opp_immediate_wins:
                if not opponent_can_win_after(board, blk):
                    return blk
            return opp_immediate_wins[0]

        # 3) Create fork (move that creates >=2 threats)
        my_forks = [m for m in empties if count_threats_after_move(board, m, me) >= 2]
        if my_forks:
            # prefer a fork that does not allow opponent an immediate win afterward
            safe_forks = [m for m in my_forks if not opponent_can_win_after(board, m)]
            if safe_forks:
                return random.choice(safe_forks)
            return random.choice(my_forks)

        # 4) Block opponent forks
        opp_forks = [m for m in empties if count_threats_after_move(board, m, opp) >= 2]
        if opp_forks:
            # If we can play directly on the fork cell, do so (preferring safe ones).
            for f in opp_forks:
                if f in empties and not opponent_can_win_after(board, f):
                    return f
            for f in opp_forks:
                if f in empties:
                    return f
            # Otherwise, pick move that minimizes opponent forks after our move
            best_m = None
            best_remain = 999
            for m in empties:
                bd2 = board[:]
                bd2[m] = me
                remain = 0
                for p in range(25):
                    if bd2[p] == ' ' and count_threats_after_move(bd2, p, opp) >= 2:
                        remain += 1
                if remain < best_remain:
                    best_remain = remain
                    best_m = m
            if best_m is not None:
                return best_m

        # 5) Center preference
        center = 12
        if center in empties:
            return center

        # 6) Heuristic scoring for remaining moves
        def heuristic_score(bd, pos):
            bd2 = bd[:]
            bd2[pos] = me
            # If this move wins, extremely high score
            for line in self.cell_to_lines[pos]:
                a, b, c = line
                if bd2[a] == bd2[b] == bd2[c] == me:
                    return 100000
            # Count immediate threats we create
            threats = count_threats_after_move(bd, pos, me)
            # Count opponent immediate wins after this move
            opp_immediate_after = 0
            for p in range(25):
                if bd2[p] == ' ' and is_winning_move(bd2, p, opp):
                    opp_immediate_after += 1
            # Sum potential of lines through this cell (no opponent present)
            line_potential = 0
            for line in self.cell_to_lines[pos]:
                a, b, c = line
                syms = [bd2[a], bd2[b], bd2[c]]
                if opp not in syms:
                    my_count = syms.count(me)
                    if my_count == 2:
                        line_potential += 40
                    elif my_count == 1:
                        line_potential += 7
                    else:
                        line_potential += 2
            # Slight preference for corners and near-center (encourage quick wins)
            corner_bonus = 0
            if pos in {0, 4, 20, 24}:
                corner_bonus = 3
            # penalty if move gives opponent an immediate win
            score = 200 * threats + line_potential + corner_bonus - 500 * min(1, opp_immediate_after)
            # slight tiebreaker: prefer lower indices unpredictably
            return score

        best_score = None
        best_moves = []
        for m in empties:
            sc = heuristic_score(board, m)
            if best_score is None or sc > best_score:
                best_score = sc
                best_moves = [m]
            elif sc == best_score:
                best_moves.append(m)

        if best_moves:
            return random.choice(best_moves)

        # Fallback: random empty cell
        return random.choice(empties)
