"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-13 14:53:21
"""

import time

class TicTacToeAgent:
    __slots__ = ("name", "symbol", "opp", "tt")

    # --- Class-wide, shared precomputation (initialized lazily) ---
    _READY = False
    _EMPTY = " "
    _LINES = None              # list[tuple[int,int,int]]
    _CELL_TO_LINES = None      # list[list[int]]
    _CELL_IMPORTANCE = None    # list[int]
    _POS_WEIGHT = None         # list[int]
    _ZOBRIST = None            # list[tuple[int,int]]  (per cell: (X, O))

    # Transposition-table flags
    _EXACT = 0
    _LOWER = 1
    _UPPER = -1

    _WIN_BASE = 100_000
    _INF = 10**18

    def __init__(self, name: str, symbol: str):
        if not TicTacToeAgent._READY:
            TicTacToeAgent._init_tables()

        self.name = name
        self.symbol = (symbol or "X").upper()
        self.symbol = "X" if self.symbol != "O" else "O"
        self.opp = "O" if self.symbol == "X" else "X"

        # Transposition table: key=(hash, player_to_move) -> (depth, value, flag, best_move)
        self.tt = {}

    @classmethod
    def _init_tables(cls):
        # Winning lines (3-in-a-row on a 5x5)
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                s = r * 5 + c
                lines.append((s, s + 1, s + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                lines.append((s, s + 5, s + 10))
        # Diagonals down-right
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                lines.append((s, s + 6, s + 12))
        # Diagonals down-left
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                lines.append((s, s + 4, s + 8))

        cell_to_lines = [[] for _ in range(25)]
        for li, (a, b, c) in enumerate(lines):
            cell_to_lines[a].append(li)
            cell_to_lines[b].append(li)
            cell_to_lines[c].append(li)

        cell_importance = [len(cell_to_lines[i]) for i in range(25)]

        # Mild positional preference (center > edges > corners)
        pos_weight = []
        for i in range(25):
            r, c = divmod(i, 5)
            manh = abs(r - 2) + abs(c - 2)
            pos_weight.append(max(0, 4 - manh))

        # Zobrist table: per cell, random 64-bit for X and O
        zob = []
        for _ in range(25):
            zob.append((random.getrandbits(64), random.getrandbits(64)))

        cls._LINES = lines
        cls._CELL_TO_LINES = cell_to_lines
        cls._CELL_IMPORTANCE = cell_importance
        cls._POS_WEIGHT = pos_weight
        cls._ZOBRIST = zob
        cls._READY = True

    # ---------------- Core API ----------------
    def make_move(self, board: list[str]) -> int:
        b = list(board)  # safety copy
        empty = self._EMPTY

        legal = [i for i, v in enumerate(b) if v == empty]
        if not legal:
            return 0  # shouldn't happen; engine will randomize if invalid

        # If game is already ended (shouldn't happen), just return a legal move.
        if self._check_winner_full(b) is not None:
            return legal[0]

        me, opp = self.symbol, self.opp

        # 1) Immediate win
        my_wins = self._winning_moves(b, me)
        if my_wins:
            return self._pick_best_static(b, my_wins, me, opp)

        # 2) Immediate block
        opp_wins = self._winning_moves(b, opp)
        if opp_wins:
            return self._pick_best_static(b, opp_wins, me, opp)

        # 3) Quick fork creation (2+ threats next turn)
        forks = [m for m in legal if self._fork_potential(b, m, me, opp) >= 2]
        if forks:
            return self._pick_best_static(b, forks, me, opp)

        # 4) Block opponent forks if present
        opp_forks = [m for m in legal if self._fork_potential(b, m, opp, me) >= 2]
        if opp_forks:
            return self._pick_best_static(b, opp_forks, me, opp)

        # 5) Search (iterative deepening alpha-beta with TT)
        if len(self.tt) > 250_000:
            self.tt.clear()

        empties = len(legal)
        max_depth = self._select_max_depth(empties)
        # Keep a little margin under 1s timeout.
        end_time = time.perf_counter() + 0.92

        h = self._hash_board(b)
        best_move = None

        # Iterative deepening: always keep the last fully-computed best move.
        for depth in range(1, max_depth + 1):
            try:
                val, move = self._negamax(
                    b, h, me, opp, depth, -self._INF, self._INF, empties, end_time, extended=False
                )
            except TimeoutError:
                break
            if move is not None:
                best_move = move
            # If we found a forced win/loss, no need to go deeper.
            if abs(val) >= self._WIN_BASE - 1000:
                break

        if best_move is None or b[best_move] != empty:
            # Fallback: choose most "central/important" legal move.
            best_move = max(legal, key=lambda m: (self._CELL_IMPORTANCE[m], self._POS_WEIGHT[m]))

        return best_move

    # ---------------- Search ----------------
    def _negamax(
        self,
        b: list[str],
        h: int,
        player: str,
        other: str,
        depth: int,
        alpha: int,
        beta: int,
        empties: int,
        end_time: float,
        extended: bool,
    ):
        if time.perf_counter() >= end_time:
            raise TimeoutError

        key = (h, player)
        alpha0 = alpha

        entry = self.tt.get(key)
        if entry is not None:
            e_depth, e_val, e_flag, e_best = entry
            if e_depth >= depth:
                if e_flag == self._EXACT:
                    return e_val, e_best
                if e_flag == self._LOWER:
                    alpha = max(alpha, e_val)
                elif e_flag == self._UPPER:
                    beta = min(beta, e_val)
                if alpha >= beta:
                    return e_val, e_best

        # Quiescence-like single extension if there are immediate tactics around depth 0.
        if depth == 0:
            if (not extended) and (self._has_immediate_win(b, player) or self._has_immediate_win(b, other)):
                depth = 1
                extended = True
            else:
                return self._evaluate(b, player, other), None

        moves = [i for i, v in enumerate(b) if v == self._EMPTY]
        if not moves:
            return 0, None

        # Move ordering (helps alpha-beta)
        tt_best = entry[3] if entry is not None else None
        ordered = self._order_moves(b, moves, player, other, tt_best)

        best_val = -self._INF
        best_move = None

        z_idx = 0 if player == "X" else 1

        for m in ordered:
            if time.perf_counter() >= end_time:
                raise TimeoutError

            b[m] = player
            h2 = h ^ self._ZOBRIST[m][z_idx]
            new_empties = empties - 1

            if self._is_win_from_move(b, m, player):
                val = self._WIN_BASE + new_empties
            elif new_empties == 0:
                val = 0
            else:
                child_val, _ = self._negamax(
                    b, h2, other, player, depth - 1, -beta, -alpha, new_empties, end_time, extended=extended
                )
                val = -child_val

            b[m] = self._EMPTY

            if val > best_val:
                best_val, best_move = val, m

            alpha = max(alpha, val)
            if alpha >= beta:
                break

        # Store TT entry
        if best_val <= alpha0:
            flag = self._UPPER
        elif best_val >= beta:
            flag = self._LOWER
        else:
            flag = self._EXACT
        self.tt[key] = (depth, best_val, flag, best_move)

        return best_val, best_move

    def _select_max_depth(self, empties: int) -> int:
        # Conservative early (branching huge), deeper late.
        if empties >= 20:
            return 3
        if empties >= 16:
            return 4
        if empties >= 12:
            return 5
        if empties >= 9:
            return 7
        return min(empties, 12)

    # ---------------- Tactics / Heuristics ----------------
    def _pick_best_static(self, b: list[str], candidates, me: str, opp: str) -> int:
        # Pick the candidate that looks best after the move (fast, no search).
        best = None
        best_score = -self._INF
        for m in candidates:
            if b[m] != self._EMPTY:
                continue
            b[m] = me
            score = self._evaluate(b, me, opp)
            # Prefer moves that also reduce opponent immediate wins / create threats.
            score += 250 * len(self._winning_moves(b, me))
            score -= 300 * len(self._winning_moves(b, opp))
            b[m] = self._EMPTY
            # Tie-break: central/important
            score = (score, self._CELL_IMPORTANCE[m], self._POS_WEIGHT[m])
            if best is None or score > best_score:
                best = m
                best_score = score
        return best if best is not None else next(iter(candidates))

    def _evaluate(self, b: list[str], player: str, other: str) -> int:
        # Heuristic score from "player" perspective.
        score = 0

        # Positional: center + intersection cells
        for i, v in enumerate(b):
            if v == player:
                score += 3 * self._CELL_IMPORTANCE[i] + 2 * self._POS_WEIGHT[i]
            elif v == other:
                score -= 3 * self._CELL_IMPORTANCE[i] + 2 * self._POS_WEIGHT[i]

        # Line potential
        p2 = 0
        o2 = 0
        for a, c, d in self._LINES:
            va, vc, vd = b[a], b[c], b[d]
            p = (va == player) + (vc == player) + (vd == player)
            o = (va == other) + (vc == other) + (vd == other)
            if p and o:
                continue  # blocked
            if p:
                if p == 2:
                    score += 450
                    p2 += 1
                elif p == 1:
                    score += 18
            elif o:
                if o == 2:
                    score -= 520
                    o2 += 1
                elif o == 1:
                    score -= 20

        # Extra emphasis on multiple simultaneous threats ("fork pressure")
        score += 140 * (p2 - o2)

        return score

    def _order_moves(self, b: list[str], moves: list[int], player: str, other: str, tt_best: int | None):
        # Highest first.
        def mscore(m: int) -> int:
            s = 10 * self._CELL_IMPORTANCE[m] + 6 * self._POS_WEIGHT[m]

            # Prefer TT best move first if present.
            if tt_best is not None and m == tt_best:
                s += 50_000

            # Immediate win / block cues (fast local checks)
            if self._is_win_if_play(b, m, player):
                s += 100_000
            if self._is_win_if_play(b, m, other):
                s += 80_000

            # Fork potential
            s += 4_000 * self._fork_potential(b, m, player, other)

            return s

        return sorted(moves, key=mscore, reverse=True)

    def _fork_potential(self, b: list[str], move: int, player: str, other: str) -> int:
        # Count how many lines would become "two-in-a-row with one empty" after playing at move.
        if b[move] != self._EMPTY:
            return 0
        cnt = 0
        for li in self._CELL_TO_LINES[move]:
            a, c, d = self._LINES[li]
            if move == a:
                p, q = c, d
            elif move == c:
                p, q = a, d
            else:
                p, q = a, c

            vp, vq = b[p], b[q]
            if vp == other or vq == other:
                continue
            # After playing move, line has player at move; we want exactly one more player mark among p/q.
            if (vp == player and vq == self._EMPTY) or (vq == player and vp == self._EMPTY):
                cnt += 1
        return cnt

    def _winning_moves(self, b: list[str], player: str):
        # Return set of indices that win immediately for player.
        wins = set()
        e = self._EMPTY
        for a, c, d in self._LINES:
            va, vc, vd = b[a], b[c], b[d]
            # Exactly two player's marks and one empty
            p = (va == player) + (vc == player) + (vd == player)
            if p != 2:
                continue
            if va == e and vc == player and vd == player:
                wins.add(a)
            elif vc == e and va == player and vd == player:
                wins.add(c)
            elif vd == e and va == player and vc == player:
                wins.add(d)
        return wins

    def _has_immediate_win(self, b: list[str], player: str) -> bool:
        e = self._EMPTY
        for a, c, d in self._LINES:
            va, vc, vd = b[a], b[c], b[d]
            p = (va == player) + (vc == player) + (vd == player)
            if p == 2 and (va == e or vc == e or vd == e):
                return True
        return False

    # ---------------- Win checks / hashing ----------------
    def _is_win_if_play(self, b: list[str], move: int, player: str) -> bool:
        # Check if putting player at move completes a 3-in-row.
        if b[move] != self._EMPTY:
            return False
        for li in self._CELL_TO_LINES[move]:
            a, c, d = self._LINES[li]
            if move == a:
                if b[c] == player and b[d] == player:
                    return True
            elif move == c:
                if b[a] == player and b[d] == player:
                    return True
            else:
                if b[a] == player and b[c] == player:
                    return True
        return False

    def _is_win_from_move(self, b: list[str], move: int, player: str) -> bool:
        # Assumes b[move] == player; checks only affected lines.
        for li in self._CELL_TO_LINES[move]:
            a, c, d = self._LINES[li]
            if b[a] == b[c] == b[d] == player:
                return True
        return False

    def _check_winner_full(self, b: list[str]):
        e = self._EMPTY
        for a, c, d in self._LINES:
            v = b[a]
            if v != e and v == b[c] == b[d]:
                return v
        if e not in b:
            return "DRAW"
        return None

    def _hash_board(self, b: list[str]) -> int:
        h = 0
        for i, v in enumerate(b):
            if v == "X":
                h ^= self._ZOBRIST[i][0]
            elif v == "O":
                h ^= self._ZOBRIST[i][1]
        return h
