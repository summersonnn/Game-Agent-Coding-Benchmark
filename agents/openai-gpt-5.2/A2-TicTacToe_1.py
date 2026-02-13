"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-13 14:53:21
"""

import time

import time

class TicTacToeAgent:
    EMPTY = ' '
    SIZE = 5

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opp = 'O' if symbol == 'X' else 'X'

        # Precompute all 3-in-a-row winning triplets on a 5x5 grid
        self.triplets = []
        # Rows
        for r in range(5):
            for c in range(3):
                s = r * 5 + c
                self.triplets.append((s, s + 1, s + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                self.triplets.append((s, s + 5, s + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                self.triplets.append((s, s + 6, s + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                self.triplets.append((s, s + 4, s + 8))

        # Cell -> triplets containing that cell (for fast fork/threat computations)
        self.cell_triplets = [[] for _ in range(25)]
        for t in self.triplets:
            for idx in t:
                self.cell_triplets[idx].append(t)

        # Positional weights: how many triplets include each cell (center tends to be best)
        self.cell_weight = [0] * 25
        for a, b, c in self.triplets:
            self.cell_weight[a] += 1
            self.cell_weight[b] += 1
            self.cell_weight[c] += 1

        # Neighbor lists (8-connected) for quick local heuristics
        self.neighbors = [[] for _ in range(25)]
        for i in range(25):
            r, c = divmod(i, 5)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < 5 and 0 <= cc < 5:
                        self.neighbors[i].append(rr * 5 + cc)

        # Search bookkeeping
        self._deadline = 0.0
        self._timed_out = False
        self._tt = {}  # (board_str, to_move, depth) -> value

    def make_move(self, board: list[str]) -> int:
        empties = [i for i, v in enumerate(board) if v == self.EMPTY]
        if not empties:
            return None

        # 1) Win now
        wins = self._winning_moves(board, self.symbol)
        if wins:
            return self._pick_best(board, wins, self.symbol)

        # 2) Block opponent win
        blocks = self._winning_moves(board, self.opp)
        if blocks:
            return self._pick_best(board, blocks, self.symbol, prefer_threats=True)

        # 3) Create a fork (two+ immediate winning threats)
        forks = self._fork_moves(board, self.symbol)
        if forks:
            return self._pick_best(board, forks, self.symbol, prefer_threats=True)

        # 4) Block opponent fork (if possible, occupy their fork squares)
        opp_forks = self._fork_moves(board, self.opp)
        if opp_forks:
            candidates = [m for m in opp_forks if board[m] == self.EMPTY]
            if candidates:
                return self._pick_best(board, candidates, self.symbol, prefer_threats=True)

        # 5) Depth-limited alpha-beta search with move filtering + iterative deepening
        return self._search(board, empties)

    # ---------------- Core tactics helpers ----------------

    def _winning_moves(self, board: list[str], sym: str) -> list[int]:
        """Return all empty cells that immediately complete a 3-in-row for sym."""
        res = set()
        E = self.EMPTY
        for a, b, c in self.triplets:
            va, vb, vc = board[a], board[b], board[c]
            if va == E:
                if vb == sym and vc == sym:
                    res.add(a)
            elif vb == E:
                if va == sym and vc == sym:
                    res.add(b)
            elif vc == E:
                if va == sym and vb == sym:
                    res.add(c)
        return list(res)

    def _threat_count_after_move(self, board: list[str], move: int, sym: str) -> int:
        """Number of (sym,sym,empty) lines created by playing sym at move."""
        if board[move] != self.EMPTY:
            return 0
        opp = 'O' if sym == 'X' else 'X'
        cnt = 0
        E = self.EMPTY
        for a, b, c in self.cell_triplets[move]:
            x = board[a]
            y = board[b]
            z = board[c]
            # pretend move is applied
            if a == move:
                x = sym
            elif b == move:
                y = sym
            else:
                z = sym

            # only count "clean" threats (no opponent mark)
            if x == opp or y == opp or z == opp:
                continue
            s = (1 if x == sym else 0) + (1 if y == sym else 0) + (1 if z == sym else 0)
            e = (1 if x == E else 0) + (1 if y == E else 0) + (1 if z == E else 0)
            if s == 2 and e == 1:
                cnt += 1
        return cnt

    def _fork_moves(self, board: list[str], sym: str) -> list[int]:
        forks = []
        for i, v in enumerate(board):
            if v == self.EMPTY and self._threat_count_after_move(board, i, sym) >= 2:
                forks.append(i)
        return forks

    def _pick_best(self, board: list[str], moves: list[int], sym: str, prefer_threats: bool = False) -> int:
        """Tie-breaker for tactical move sets."""
        best = None
        best_score = -10**18
        for m in moves:
            if board[m] != self.EMPTY:
                continue
            score = self.cell_weight[m] * 10
            # small local preference: being adjacent to own marks and away from opponent
            for nb in self.neighbors[m]:
                if board[nb] == sym:
                    score += 2
                elif board[nb] != self.EMPTY:
                    score -= 1
            if prefer_threats:
                score += 50 * self._threat_count_after_move(board, m, sym)
            # deterministic-ish tiebreaker
            score = score * 100 - m
            if score > best_score:
                best_score = score
                best = m
        if best is not None:
            return best
        # Fallback
        empties = [i for i, v in enumerate(board) if v == self.EMPTY]
        return random.choice(empties)

    # ---------------- Search ----------------

    def _infer_to_move(self, board: list[str]) -> str:
        x = sum(1 for v in board if v == 'X')
        o = sum(1 for v in board if v == 'O')
        return 'X' if x == o else 'O'

    def _search(self, board: list[str], empties: list[int]) -> int:
        to_move = self._infer_to_move(board)

        # If something is off, still return a valid move
        if to_move not in ('X', 'O'):
            return random.choice(empties)

        n_empty = len(empties)
        if n_empty <= 1:
            return empties[0]

        # Iterative deepening limits: keep it reliable under 1s
        if n_empty <= 8:
            max_depth = 7
        elif n_empty <= 12:
            max_depth = 6
        elif n_empty <= 16:
            max_depth = 5
        else:
            max_depth = 4

        self._deadline = time.perf_counter() + 0.92
        self._timed_out = False
        self._tt.clear()

        # Baseline move: best positional
        best_move = self._pick_best(board, empties, self.symbol)
        best_val = -10**18

        # Only search as the side to move (engine should call us on our turn)
        # If it's somehow not our symbol, we still do a correct minimax for the actual mover.
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > self._deadline:
                break
            val, move = self._root_minimax(board, to_move, depth)
            if self._timed_out:
                break
            if move is not None:
                # choose according to which side is to_move
                if to_move == self.symbol:
                    if val > best_val:
                        best_val, best_move = val, move
                else:
                    # if we're (unexpectedly) searching for opponent to move, keep the minimizing best
                    if val < best_val:
                        best_val, best_move = val, move

        return best_move if (best_move is not None and board[best_move] == self.EMPTY) else random.choice(empties)

    def _root_minimax(self, board: list[str], to_move: str, depth: int) -> tuple[int, int | None]:
        moves = self._ordered_moves(board, to_move)
        if not moves:
            return self._heuristic(board), None

        alpha, beta = -10**18, 10**18
        best_move = None

        if to_move == self.symbol:
            best_val = -10**18
            for m in moves:
                if time.perf_counter() > self._deadline:
                    self._timed_out = True
                    break
                board[m] = to_move
                val = self._minimax(board, self._other(to_move), depth - 1, alpha, beta)
                board[m] = self.EMPTY
                if val > best_val:
                    best_val, best_move = val, m
                alpha = max(alpha, best_val)
                if alpha >= beta:
                    break
            return best_val, best_move
        else:
            best_val = 10**18
            for m in moves:
                if time.perf_counter() > self._deadline:
                    self._timed_out = True
                    break
                board[m] = to_move
                val = self._minimax(board, self._other(to_move), depth - 1, alpha, beta)
                board[m] = self.EMPTY
                if val < best_val:
                    best_val, best_move = val, m
                beta = min(beta, best_val)
                if alpha >= beta:
                    break
            return best_val, best_move

    def _minimax(self, board: list[str], to_move: str, depth: int, alpha: int, beta: int) -> int:
        if time.perf_counter() > self._deadline:
            self._timed_out = True
            return self._heuristic(board)

        winner = self._check_winner(board)
        if winner is not None:
            return self._terminal_score(board, winner)

        if depth <= 0:
            return self._heuristic(board)

        key = None
        if depth >= 2:  # avoid too much key-building overhead at shallow nodes
            key = (''.join(board), to_move, depth)
            cached = self._tt.get(key)
            if cached is not None:
                return cached

        moves = self._ordered_moves(board, to_move)
        if not moves:
            val = self._heuristic(board)
            if key is not None:
                self._tt[key] = val
            return val

        if to_move == self.symbol:
            best = -10**18
            for m in moves:
                board[m] = to_move
                val = self._minimax(board, self._other(to_move), depth - 1, alpha, beta)
                board[m] = self.EMPTY
                if val > best:
                    best = val
                alpha = max(alpha, best)
                if alpha >= beta or self._timed_out:
                    break
        else:
            best = 10**18
            for m in moves:
                board[m] = to_move
                val = self._minimax(board, self._other(to_move), depth - 1, alpha, beta)
                board[m] = self.EMPTY
                if val < best:
                    best = val
                beta = min(beta, best)
                if alpha >= beta or self._timed_out:
                    break

        if key is not None:
            self._tt[key] = best
        return best

    def _ordered_moves(self, board: list[str], to_move: str) -> list[int]:
        E = self.EMPTY
        empties = [i for i, v in enumerate(board) if v == E]
        if not empties:
            return []

        opp = self._other(to_move)

        # If current player can win now, only consider winning moves.
        wins = self._winning_moves(board, to_move)
        if wins:
            return wins

        # If opponent can win next, blocking is mandatory (unless you can win now, handled above).
        opp_wins = self._winning_moves(board, opp)
        if opp_wins:
            # blocks are exactly those squares
            blocks = [m for m in opp_wins if board[m] == E]
            if blocks:
                return blocks

        # Otherwise, filter to "relevant" moves near existing action
        # Collect empties that belong to any triplet containing a mark.
        relevant = set()
        any_mark = False
        for a, b, c in self.triplets:
            if board[a] != E or board[b] != E or board[c] != E:
                any_mark = True
                if board[a] == E:
                    relevant.add(a)
                if board[b] == E:
                    relevant.add(b)
                if board[c] == E:
                    relevant.add(c)

        candidates = list(relevant) if any_mark and relevant else empties

        n_empty = len(empties)
        max_cand = 14 if n_empty <= 12 else 12 if n_empty <= 16 else 10
        if len(candidates) > max_cand:
            # Score candidates by positional weight + local adjacency + threat creation for mover
            scored = []
            for m in candidates:
                if board[m] != E:
                    continue
                s = self.cell_weight[m] * 10
                for nb in self.neighbors[m]:
                    if board[nb] == to_move:
                        s += 2
                    elif board[nb] == opp:
                        s += 1  # still "relevant"
                s += 40 * self._threat_count_after_move(board, m, to_move)
                scored.append((s, -m, m))
            scored.sort(reverse=True)
            candidates = [m for _, __, m in scored[:max_cand]]

        # Order by approximate leaf heuristic after move; good for alpha-beta pruning.
        # For minimizing nodes, we sort ascending; for maximizing nodes, descending.
        scored2 = []
        for m in candidates:
            if board[m] != E:
                continue
            board[m] = to_move
            h = self._heuristic(board)
            board[m] = E
            scored2.append((h, -self.cell_weight[m], m))
        scored2.sort(reverse=(to_move == self.symbol))
        return [m for _, __, m in scored2]

    # ---------------- Evaluation ----------------

    def _other(self, sym: str) -> str:
        return 'O' if sym == 'X' else 'X'

    def _check_winner(self, board: list[str]) -> str | None:
        E = self.EMPTY
        for a, b, c in self.triplets:
            va = board[a]
            if va != E and va == board[b] == board[c]:
                return va
        if E not in board:
            return 'DRAW'
        return None

    def _terminal_score(self, board: list[str], winner: str) -> int:
        if winner == 'DRAW':
            return 0
        empties = sum(1 for v in board if v == self.EMPTY)
        base = 100000 + empties  # prefer winning sooner (more empties left); prefer losing later
        if winner == self.symbol:
            return base
        return -base

    def _heuristic(self, board: list[str]) -> int:
        # Static evaluation from self.symbol perspective
        me, opp, E = self.symbol, self.opp, self.EMPTY

        score = 0

        # Line patterns
        for a, b, c in self.triplets:
            va, vb, vc = board[a], board[b], board[c]
            # Skip "blocked" lines
            has_me = (va == me) or (vb == me) or (vc == me)
            has_opp = (va == opp) or (vb == opp) or (vc == opp)
            if has_me and has_opp:
                continue

            me_cnt = (1 if va == me else 0) + (1 if vb == me else 0) + (1 if vc == me else 0)
            opp_cnt = (1 if va == opp else 0) + (1 if vb == opp else 0) + (1 if vc == opp else 0)
            empty_cnt = 3 - me_cnt - opp_cnt

            if me_cnt == 2 and empty_cnt == 1:
                score += 90
            elif opp_cnt == 2 and empty_cnt == 1:
                score -= 110
            elif me_cnt == 1 and empty_cnt == 2:
                score += 6
            elif opp_cnt == 1 and empty_cnt == 2:
                score -= 7

        # Positional: prefer occupying influential cells
        for i, v in enumerate(board):
            if v == me:
                score += 2 * self.cell_weight[i]
            elif v == opp:
                score -= 2 * self.cell_weight[i]

        return score
