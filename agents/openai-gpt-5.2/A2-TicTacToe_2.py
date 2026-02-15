"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-14 16:45:38
"""

import time

class TicTacToeAgent:
    EMPTY = " "
    BOARD_N = 5
    WIN_SCORE = 1_000_000
    INF = 10**12

    # --- Precompute all 3-in-a-row lines on 5x5 (48 lines) ---
    WIN_LINES = []
    # Rows
    for _r in range(5):
        for _c in range(3):
            _s = _r * 5 + _c
            WIN_LINES.append((_s, _s + 1, _s + 2))
    # Cols
    for _c in range(5):
        for _r in range(3):
            _s = _r * 5 + _c
            WIN_LINES.append((_s, _s + 5, _s + 10))
    # Diagonals (down-right)
    for _r in range(3):
        for _c in range(3):
            _s = _r * 5 + _c
            WIN_LINES.append((_s, _s + 6, _s + 12))
    # Diagonals (down-left)
    for _r in range(3):
        for _c in range(2, 5):
            _s = _r * 5 + _c
            WIN_LINES.append((_s, _s + 4, _s + 8))

    LINES_BY_CELL = [[] for _ in range(25)]
    for _line in WIN_LINES:
        for _idx in _line:
            LINES_BY_CELL[_idx].append(_line)

    # Positional weights: prefer center and near-center
    POS_W = [0] * 25
    _cr, _cc = 2, 2
    for _i in range(25):
        _r, _c = divmod(_i, 5)
        _md = abs(_r - _cr) + abs(_c - _cc)
        # Higher is better
        POS_W[_i] = 20 - 4 * _md

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.opp = "O" if symbol == "X" else "X"

        # Time management
        self._deadline = 0.0
        self._time_up = False

        # Transposition table
        self._tt = {}

        # Zobrist hashing (self-contained PRNG: splitmix64)
        self._mask64 = (1 << 64) - 1
        self._seed = (hash((name, symbol)) & self._mask64) or 0x9E3779B97F4A7C15

        self._z_piece = [[0, 0] for _ in range(25)]  # [cell][0:X,1:O]
        for i in range(25):
            self._z_piece[i][0] = self._rand64()
            self._z_piece[i][1] = self._rand64()
        self._z_side = self._rand64()  # toggled each ply; included when X-to-move

        # Root move ordering memory
        self._root_hint_move = None

    # ---------- Public API ----------
    def make_move(self, board: list[str]) -> int:
        b = list(board)  # do not mutate engine-provided board

        empties = [i for i, v in enumerate(b) if v == self.EMPTY]
        if not empties:
            return 0

        # 1) Immediate win
        m = self._find_winning_move(b, self.symbol)
        if m is not None:
            return m

        # 2) Immediate block
        m = self._find_winning_move(b, self.opp)
        if m is not None:
            return m

        # 3) Search (iterative deepening negamax with alpha-beta + TT)
        self._deadline = time.perf_counter() + 0.93
        self._time_up = False
        self._tt.clear()

        h0 = self._hash_pieces(b)
        # include side-to-move: we use XOR _z_side when X is to move
        if self.symbol == "X":
            h0 ^= self._z_side

        # Choose max depth based on remaining empties (iterative deepening will stop by time)
        e = len(empties)
        if e > 18:
            max_depth = 4
        elif e > 13:
            max_depth = 5
        elif e > 9:
            max_depth = 6
        else:
            max_depth = 7

        best_move = None
        best_score = -self.INF

        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= self._deadline:
                break
            score, move = self._negamax_root(b, h0, depth, self.symbol)
            if self._time_up:
                break
            if move is not None:
                best_move, best_score = move, score
                self._root_hint_move = move  # hint next depth

        if best_move is None or b[best_move] != self.EMPTY:
            # Deterministic fallback: pick the best heuristic move among candidates.
            best_move = self._fallback_move(b)

        return best_move

    # ---------- SplitMix64 PRNG ----------
    def _rand64(self) -> int:
        self._seed = (self._seed + 0x9E3779B97F4A7C15) & self._mask64
        z = self._seed
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & self._mask64
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & self._mask64
        z = (z ^ (z >> 31)) & self._mask64
        return z

    # ---------- Utility ----------
    @staticmethod
    def _other(sym: str) -> str:
        return "O" if sym == "X" else "X"

    def _hash_pieces(self, b: list[str]) -> int:
        h = 0
        zp = self._z_piece
        for i, v in enumerate(b):
            if v == "X":
                h ^= zp[i][0]
            elif v == "O":
                h ^= zp[i][1]
        return h

    def _is_win_after(self, b: list[str], last_move: int, last_player: str) -> bool:
        bb = b
        for a, c, d in self.LINES_BY_CELL[last_move]:
            # (a,c,d) are just names; tuple is 3 indices
            if bb[a] == bb[c] == bb[d] == last_player:
                return True
        return False

    def _find_winning_move(self, b: list[str], sym: str):
        bb = b
        for a, c, d in self.WIN_LINES:
            va, vc, vd = bb[a], bb[c], bb[d]
            if va == sym and vc == sym and vd == self.EMPTY:
                return d
            if va == sym and vd == sym and vc == self.EMPTY:
                return c
            if vc == sym and vd == sym and va == self.EMPTY:
                return a
        return None

    # ---------- Move generation / ordering ----------
    def _candidate_moves(self, b: list[str]) -> list[int]:
        bb = b
        empties = []
        occupied = []
        for i, v in enumerate(bb):
            if v == self.EMPTY:
                empties.append(i)
            else:
                occupied.append(i)

        if not empties:
            return []

        # If very early, allow all moves (but will be ordered).
        if len(occupied) <= 1:
            return empties

        # Otherwise, focus near existing marks (Chebyshev adjacency), plus some strategic additions.
        adj = set()
        for idx in occupied:
            r, c = divmod(idx, 5)
            r0 = r - 1 if r > 0 else 0
            r1 = r + 1 if r < 4 else 4
            c0 = c - 1 if c > 0 else 0
            c1 = c + 1 if c < 4 else 4
            for rr in range(r0, r1 + 1):
                base = rr * 5
                for cc in range(c0, c1 + 1):
                    j = base + cc
                    if bb[j] == self.EMPTY:
                        adj.add(j)

        # Ensure center is considered
        if bb[12] == self.EMPTY:
            adj.add(12)

        cand = list(adj)

        # If too few, add empties from any "unblocked" line that still matters.
        if len(cand) < 8:
            me, opp = self.symbol, self.opp
            extra = set(cand)
            for a, c, d in self.WIN_LINES:
                va, vc, vd = bb[a], bb[c], bb[d]
                has_me = (va == me) or (vc == me) or (vd == me)
                has_opp = (va == opp) or (vc == opp) or (vd == opp)
                if has_me and has_opp:
                    continue
                if va == self.EMPTY:
                    extra.add(a)
                if vc == self.EMPTY:
                    extra.add(c)
                if vd == self.EMPTY:
                    extra.add(d)
            cand = [m for m in extra if bb[m] == self.EMPTY]

        # If still too few (rare), just return all empties.
        if len(cand) < 6:
            return empties

        return cand

    def _move_order_key(self, b: list[str], move: int, player: str) -> int:
        # Larger is better.
        bb = b
        opp = "O" if player == "X" else "X"

        # Threat estimate from local lines
        threat = 0
        for a, c, d in self.LINES_BY_CELL[move]:
            va, vc, vd = bb[a], bb[c], bb[d]

            # counts before placing at 'move' (which is empty)
            n_opp = (va == opp) + (vc == opp) + (vd == opp)
            if n_opp:
                # Still may be a block if opponent has 2-in-line and we occupy the empty.
                n_player = (va == player) + (vc == player) + (vd == player)
                if n_opp == 2 and n_player == 0:
                    threat += 5000  # urgent block square
                continue

            n_player = (va == player) + (vc == player) + (vd == player)
            if n_player == 2:
                threat += 20000  # winning completion
            elif n_player == 1:
                threat += 600  # creates 2-in-a-row threat
            else:
                threat += 40  # participates in a fresh line

        return threat + self.POS_W[move]

    def _ordered_moves(self, b: list[str], player: str, tt_best=None) -> list[int]:
        cand = self._candidate_moves(b)
        if not cand:
            return []

        bb = b
        # Ensure all are empty
        cand = [m for m in cand if bb[m] == self.EMPTY]
        if not cand:
            return []

        # Put tt_best / root hint first if present
        if tt_best is not None and tt_best in cand:
            cand.remove(tt_best)
            first = [tt_best]
        elif self._root_hint_move is not None and self._root_hint_move in cand:
            cand.remove(self._root_hint_move)
            first = [self._root_hint_move]
        else:
            first = []

        # Sort remaining by heuristic key descending
        cand.sort(key=lambda m: self._move_order_key(bb, m, player), reverse=True)
        return first + cand

    def _fallback_move(self, b: list[str]) -> int:
        bb = b
        cand = self._candidate_moves(bb)
        if not cand:
            # pick any empty
            for i, v in enumerate(bb):
                if v == self.EMPTY:
                    return i
            return 0

        best = None
        bestk = -self.INF
        for m in cand:
            if bb[m] != self.EMPTY:
                continue
            k = self._move_order_key(bb, m, self.symbol)
            if k > bestk:
                bestk = k
                best = m
        if best is not None:
            return best

        # last resort: first empty
        for i, v in enumerate(bb):
            if v == self.EMPTY:
                return i
        return 0

    # ---------- Evaluation ----------
    def _eval(self, b: list[str], player: str) -> int:
        # Evaluation from the perspective of 'player' to move (higher is better for player).
        bb = b
        opp = "O" if player == "X" else "X"

        score = 0

        # Line-based features
        for a, c, d in self.WIN_LINES:
            va, vc, vd = bb[a], bb[c], bb[d]
            n_p = (va == player) + (vc == player) + (vd == player)
            n_o = (va == opp) + (vc == opp) + (vd == opp)

            if n_p and n_o:
                continue  # blocked
            if n_p == 3:
                score += 200000
            elif n_o == 3:
                score -= 200000
            elif n_p == 2 and n_o == 0:
                score += 3000
            elif n_o == 2 and n_p == 0:
                score -= 3300
            elif n_p == 1 and n_o == 0:
                score += 90
            elif n_o == 1 and n_p == 0:
                score -= 100

        # Positional bias (mild)
        for i, v in enumerate(bb):
            if v == player:
                score += self.POS_W[i] // 2
            elif v == opp:
                score -= self.POS_W[i] // 2

        return score

    # ---------- Negamax search with alpha-beta and TT ----------
    def _negamax_root(self, b: list[str], h: int, depth: int, player: str):
        alpha = -self.INF
        beta = self.INF
        best_score = -self.INF
        best_move = None

        # Probe TT for best move hint
        tt_entry = self._tt.get(h)
        tt_best = tt_entry[4] if tt_entry is not None else None

        moves = self._ordered_moves(b, player, tt_best=tt_best)
        if not moves:
            return 0, None

        opp = "O" if player == "X" else "X"
        for m in moves:
            if time.perf_counter() >= self._deadline:
                self._time_up = True
                break

            b[m] = player
            h2 = h ^ self._z_piece[m][0 if player == "X" else 1] ^ self._z_side
            score = -self._negamax(b, h2, depth - 1, -beta, -alpha, opp, ply=1, last_move=m, last_player=player)
            b[m] = self.EMPTY

            if self._time_up:
                break

            if score > best_score:
                best_score = score
                best_move = m
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best_score, best_move

    def _negamax(self, b: list[str], h: int, depth: int, alpha: int, beta: int,
                 player: str, ply: int, last_move: int, last_player: str) -> int:
        if time.perf_counter() >= self._deadline:
            self._time_up = True
            return self._eval(b, player)

        # If previous player just won, current player loses.
        if last_move is not None and self._is_win_after(b, last_move, last_player):
            return -self.WIN_SCORE + ply

        # Draw check
        # (also a cutoff if no legal moves)
        has_empty = False
        for v in b:
            if v == self.EMPTY:
                has_empty = True
                break
        if not has_empty:
            return 0

        if depth <= 0:
            return self._eval(b, player)

        # Transposition table lookup
        entry = self._tt.get(h)
        if entry is not None:
            e_depth, e_score, e_flag, e_alpha, e_best = entry
            if e_depth >= depth:
                if e_flag == 0:  # EXACT
                    return e_score
                if e_flag == 1:  # LOWERBOUND
                    if e_score > alpha:
                        alpha = e_score
                else:  # UPPERBOUND
                    if e_score < beta:
                        beta = e_score
                if alpha >= beta:
                    return e_score

        opp = "O" if player == "X" else "X"

        tt_best = entry[4] if entry is not None else None
        moves = self._ordered_moves(b, player, tt_best=tt_best)
        if not moves:
            return 0

        orig_alpha = alpha
        best_score = -self.INF
        best_move = None

        for m in moves:
            if time.perf_counter() >= self._deadline:
                self._time_up = True
                break

            b[m] = player
            h2 = h ^ self._z_piece[m][0 if player == "X" else 1] ^ self._z_side
            score = -self._negamax(b, h2, depth - 1, -beta, -alpha, opp, ply + 1, last_move=m, last_player=player)
            b[m] = self.EMPTY

            if self._time_up:
                break

            if score > best_score:
                best_score = score
                best_move = m
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        # Store TT
        if not self._time_up:
            if best_score <= orig_alpha:
                flag = 2  # UPPERBOUND
            elif best_score >= beta:
                flag = 1  # LOWERBOUND
            else:
                flag = 0  # EXACT

            # Entry: (depth, score, flag, alpha_at_store, best_move)
            # (alpha_at_store is not used except for debugging; kept compact)
            self._tt[h] = (depth, best_score, flag, orig_alpha, best_move)

        return best_score
