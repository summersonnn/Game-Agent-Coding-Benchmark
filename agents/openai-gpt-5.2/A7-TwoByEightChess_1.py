"""
Agent Code: A7-TwoByEightChess
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-14 13:30:59
"""

import time
from typing import List, Tuple, Dict, Optional

import time
import random
from typing import List, Tuple, Dict, Optional


class TwoByEightChessAgent:
    COLS = "abcdefgh"
    WHITE = "W"
    BLACK = "B"

    # Evaluation / search constants
    MATE = 100000
    INF = 10**9

    PIECE_VALUE = {
        "P": 120,
        "N": 320,
        "R": 520,
        "K": 0,
    }

    def __init__(self, name, color):
        self.name = name
        self.color = color  # 'W' or 'B'
        self._rng = random.Random((hash(name) << 1) ^ hash(color))
        self._tt = {}  # transposition table
        self._deadline = 0.0

    # ----------------------------
    # Public API
    # ----------------------------
    def make_move(self, board, move_history):
        # Defensive: if something odd happens, return a valid move if possible.
        turn = self.WHITE if (len(move_history) % 2 == 0) else self.BLACK
        my_color = self.color

        b = self._encode_board(board)

        # If we were called out of turn (shouldn't happen), still pick for self.color.
        # (Choosing for actual turn would be "helping" the opponent.)
        color_to_play = my_color

        rep_counts = self._reconstruct_repetition_counts(move_history)
        # Ensure current position is counted (engine does record initial; we do too in reconstruction,
        # but if history reconstruction diverged, still safe to count current).
        rep_counts[(b, color_to_play)] = rep_counts.get((b, color_to_play), 0) + 0

        legal = self._legal_moves(b, color_to_play)
        if not legal:
            # No legal moves (checkmate/stalemate). Engine will handle; return something.
            return "Ka1a1"

        # Quick tactical: immediate mate / king capture if available
        best_move = legal[0]
        for mv in legal:
            nb = self._apply_move(b, mv, color_to_play)
            opp = self._other(color_to_play)
            if self._is_terminal_win_for_side_to_move(nb, opp):
                best_move = mv
                return self._format_move(b, mv)

        # Iterative deepening alpha-beta within time
        self._deadline = time.perf_counter() + 0.95  # stay below 1s
        self._tt.clear()

        # Move ordering seed (helps ID)
        legal_sorted = self._order_moves(b, color_to_play, legal)

        best_score = -self.INF
        best_move = legal_sorted[0]

        # Depth cap: small game, but keep bounded for worst cases
        max_depth = 14

        try:
            for depth in range(1, max_depth + 1):
                score, mv = self._search_root(b, color_to_play, depth, rep_counts, legal_sorted)
                if mv is not None:
                    best_score, best_move = score, mv
                # If we found a forced mate line, stop early.
                if best_score >= self.MATE - 200:
                    break
        except TimeoutError:
            pass

        return self._format_move(b, best_move)

    # ----------------------------
    # Core search
    # ----------------------------
    def _search_root(
        self,
        board_t: Tuple[str, ...],
        color: str,
        depth: int,
        rep_counts: Dict[Tuple[Tuple[str, ...], str], int],
        root_moves: List[Tuple[int, int, bool]],
    ) -> Tuple[int, Optional[Tuple[int, int, bool]]]:
        self._check_time()

        alpha = -self.INF
        beta = self.INF
        best_mv = None
        best = -self.INF

        # Slight re-order every depth: best-so-far first via TT
        ordered = self._order_moves(board_t, color, root_moves)

        for mv in ordered:
            self._check_time()
            nb = self._apply_move(board_t, mv, color)
            opp = self._other(color)
            key = (nb, opp)
            rep_counts[key] = rep_counts.get(key, 0) + 1

            score = -self._negamax(nb, opp, depth - 1, -beta, -alpha, 1, rep_counts)

            rep_counts[key] -= 1
            if rep_counts[key] <= 0:
                rep_counts.pop(key, None)

            if score > best:
                best = score
                best_mv = mv
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best, best_mv

    def _negamax(
        self,
        board_t: Tuple[str, ...],
        color: str,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
        rep_counts: Dict[Tuple[Tuple[str, ...], str], int],
    ) -> int:
        self._check_time()

        # Draw by repetition (engine: 3-fold for current position+turn)
        if rep_counts.get((board_t, color), 0) >= 3:
            return 0

        # Draw by insufficient material (only kings)
        if self._insufficient_material(board_t):
            return 0

        # Terminal by no legal moves (checkmate/stalemate)
        legal = self._legal_moves(board_t, color)
        if not legal:
            if self._in_check(board_t, color):
                return -(self.MATE - ply)  # losing sooner is worse
            return 0  # stalemate

        if depth <= 0:
            return self._evaluate_pov(board_t, color)

        # Transposition
        tt_key = (board_t, color)
        tt_entry = self._tt.get(tt_key)
        if tt_entry is not None:
            tt_depth, tt_val, tt_flag, tt_best = tt_entry
            if tt_depth >= depth:
                if tt_flag == "EXACT":
                    return tt_val
                if tt_flag == "LOWER":
                    alpha = max(alpha, tt_val)
                elif tt_flag == "UPPER":
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val

        orig_alpha = alpha
        best_val = -self.INF
        best_move = None

        ordered = self._order_moves(board_t, color, legal, tt_best=tt_entry[3] if tt_entry else None)

        for mv in ordered:
            self._check_time()
            nb = self._apply_move(board_t, mv, color)
            opp = self._other(color)

            key = (nb, opp)
            rep_counts[key] = rep_counts.get(key, 0) + 1
            val = -self._negamax(nb, opp, depth - 1, -beta, -alpha, ply + 1, rep_counts)
            rep_counts[key] -= 1
            if rep_counts[key] <= 0:
                rep_counts.pop(key, None)

            if val > best_val:
                best_val = val
                best_move = mv
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        # Store TT
        flag = "EXACT"
        if best_val <= orig_alpha:
            flag = "UPPER"
        elif best_val >= beta:
            flag = "LOWER"
        self._tt[tt_key] = (depth, best_val, flag, best_move)

        return best_val

    # ----------------------------
    # Move generation and rules
    # ----------------------------
    def _legal_moves(self, board_t: Tuple[str, ...], color: str) -> List[Tuple[int, int, bool]]:
        moves = []
        for i, p in enumerate(board_t):
            if p == ".":
                continue
            if not self._is_own_piece(p, color):
                continue
            moves.extend(self._legal_moves_for_piece(board_t, color, i))
        return moves

    def _legal_moves_for_piece(self, board_t: Tuple[str, ...], color: str, from_i: int) -> List[Tuple[int, int, bool]]:
        p = board_t[from_i]
        pt = p.upper()
        pseudo = self._pseudo_moves_for_piece(board_t, color, from_i, ignore_check=True)

        legal = []
        for to_i, is_cap in pseudo:
            nb = self._apply_move(board_t, (from_i, to_i, is_cap), color)
            if not self._in_check(nb, color):
                legal.append((from_i, to_i, is_cap))
        return legal

    def _pseudo_moves_for_piece(
        self,
        board_t: Tuple[str, ...],
        color: str,
        from_i: int,
        ignore_check: bool = True,  # kept for parity with engine; unused here
    ) -> List[Tuple[int, bool]]:
        p = board_t[from_i]
        if p == ".":
            return []
        if not self._is_own_piece(p, color):
            return []

        r, c = divmod(from_i, 8)
        pt = p.upper()
        out = []

        def add(nr, nc):
            if 0 <= nr < 2 and 0 <= nc < 8:
                to_i = nr * 8 + nc
                target = board_t[to_i]
                if target == ".":
                    out.append((to_i, False))
                elif self._is_enemy_piece(target, color):
                    out.append((to_i, True))

        if pt == "K":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    add(r + dr, c + dc)

        elif pt == "N":
            deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                      (-2, -1), (-2, 1), (2, -1), (2, 1),
                      (0, -2), (0, 2)]  # linear jump
            for dr, dc in deltas:
                add(r + dr, c + dc)

        elif pt == "R":
            # Vertical (only 1 step possible on 2-row board, but keep sliding semantics)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    to_i = nr * 8 + nc
                    target = board_t[to_i]
                    if target == ".":
                        out.append((to_i, False))
                    elif self._is_enemy_piece(target, color):
                        out.append((to_i, True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif pt == "P":
            direction = 1 if color == self.WHITE else -1
            # forward
            nc = c + direction
            if 0 <= nc < 8:
                to_i = r * 8 + nc
                if board_t[to_i] == ".":
                    out.append((to_i, False))
            # diagonal captures
            for dr in (-1, 1):
                nr, nc = r + dr, c + direction
                if 0 <= nr < 2 and 0 <= nc < 8:
                    to_i = nr * 8 + nc
                    target = board_t[to_i]
                    if self._is_enemy_piece(target, color):
                        out.append((to_i, True))

        return out

    def _apply_move(self, board_t: Tuple[str, ...], mv: Tuple[int, int, bool], color: str) -> Tuple[str, ...]:
        fr, to, _ = mv
        b = list(board_t)
        piece = b[fr]
        b[fr] = "."
        # move
        b[to] = piece
        # promotion
        if piece.upper() == "P":
            _, tc = divmod(to, 8)
            if (color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0):
                b[to] = "R" if color == self.WHITE else "r"
        return tuple(b)

    def _in_check(self, board_t: Tuple[str, ...], color: str) -> bool:
        king = "K" if color == self.WHITE else "k"
        try:
            k_i = board_t.index(king)
        except ValueError:
            # Engine treats missing king as "in check" (effectively lost)
            return True

        enemy = self._other(color)
        # Engine check detection uses enemy pseudo-moves that ignore self-check.
        for i, p in enumerate(board_t):
            if p == "." or not self._is_own_piece(p, enemy):
                continue
            for to_i, _ in self._pseudo_moves_for_piece(board_t, enemy, i, ignore_check=True):
                if to_i == k_i:
                    return True
        return False

    def _is_terminal_win_for_side_to_move(self, board_t: Tuple[str, ...], side_to_move: str) -> bool:
        # If side_to_move has no legal moves and is in check => opponent just won.
        legal = self._legal_moves(board_t, side_to_move)
        if legal:
            return False
        return self._in_check(board_t, side_to_move)

    def _insufficient_material(self, board_t: Tuple[str, ...]) -> bool:
        for p in board_t:
            if p != "." and p.upper() != "K":
                return False
        return True

    # ----------------------------
    # Evaluation / ordering
    # ----------------------------
    def _evaluate_pov(self, board_t: Tuple[str, ...], pov_color: str) -> int:
        # Base eval from White's perspective, then flip for POV (negamax style).
        base = 0
        for i, p in enumerate(board_t):
            if p == ".":
                continue
            sign = 1 if p.isupper() else -1
            pt = p.upper()
            base += sign * self.PIECE_VALUE.get(pt, 0)
            # pawn progress (towards promotion)
            if pt == "P":
                _, c = divmod(i, 8)
                base += sign * (c * 8 if sign > 0 else (7 - c) * 8)

        # Mobility (very small weight)
        wm = len(self._legal_moves(board_t, self.WHITE))
        bm = len(self._legal_moves(board_t, self.BLACK))
        base += 4 * (wm - bm)

        # Check pressure
        if self._in_check(board_t, self.BLACK):
            base += 25
        if self._in_check(board_t, self.WHITE):
            base -= 25

        return base if pov_color == self.WHITE else -base

    def _order_moves(
        self,
        board_t: Tuple[str, ...],
        color: str,
        moves: List[Tuple[int, int, bool]],
        tt_best: Optional[Tuple[int, int, bool]] = None,
    ) -> List[Tuple[int, int, bool]]:
        # Simple and effective ordering: TT best first, then promotions, captures (MVV/LVA), checks.
        def mscore(mv):
            fr, to, is_cap = mv
            piece = board_t[fr]
            pt = piece.upper()
            target = board_t[to]
            sc = 0

            # TT move bonus
            if tt_best is not None and mv == tt_best:
                sc += 10_000

            # Promotion bonus
            if pt == "P":
                _, tc = divmod(to, 8)
                if (color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0):
                    sc += 4000

            # Captures: MVV-LVA
            if is_cap and target != ".":
                sc += 2000 + 10 * self.PIECE_VALUE.get(target.upper(), 0) - self.PIECE_VALUE.get(pt, 0)

            # Check bonus
            nb = self._apply_move(board_t, mv, color)
            if self._in_check(nb, self._other(color)):
                sc += 300

            # Small central-ish preference (columns d/e)
            _, fc = divmod(fr, 8)
            _, tc = divmod(to, 8)
            sc += (3 - abs(tc - 3)) * 2
            sc += (3 - abs(fc - 3)) * 1

            return sc

        return sorted(moves, key=mscore, reverse=True)

    # ----------------------------
    # Repetition reconstruction (from move_history)
    # ----------------------------
    def _reconstruct_repetition_counts(self, move_history: List[str]) -> Dict[Tuple[Tuple[str, ...], str], int]:
        # Replay from initial position to approximate engine's position_history.
        init = [
            ["R", "N", "P", "", "", "p", "n", "r"],
            ["K", "N", "P", "", "", "p", "n", "k"],
        ]
        b = self._encode_board(init)
        turn = self.WHITE
        counts: Dict[Tuple[Tuple[str, ...], str], int] = {}
        counts[(b, turn)] = 1

        for mv_str in move_history:
            parsed = self._parse_move_str(mv_str)
            if parsed is None:
                # If history contains something unexpected, stop reconstruction gracefully.
                break
            fr, to = parsed
            b_list = list(b)
            piece = b_list[fr]
            b_list[fr] = "."
            b_list[to] = piece

            # promotion
            if piece.upper() == "P":
                _, tc = divmod(to, 8)
                if (turn == self.WHITE and tc == 7) or (turn == self.BLACK and tc == 0):
                    b_list[to] = "R" if turn == self.WHITE else "r"

            b = tuple(b_list)
            turn = self._other(turn)
            counts[(b, turn)] = counts.get((b, turn), 0) + 1

        return counts

    def _parse_move_str(self, move_str: str) -> Optional[Tuple[int, int]]:
        if not isinstance(move_str, str):
            return None
        s = move_str.strip()
        if len(s) < 5:
            return None
        s_low = s.lower()
        if "x" in s_low:
            ix = s_low.index("x")
            from_sq = s[1:ix]
            to_sq = s[ix + 1: ix + 3]  # to square is 2 chars
        else:
            from_sq = s[1:3]
            to_sq = s[3:5]
        fr = self._notation_to_index(from_sq)
        to = self._notation_to_index(to_sq)
        if fr is None or to is None:
            return None
        return (fr, to)

    # ----------------------------
    # Notation / board utilities
    # ----------------------------
    def _encode_board(self, board_2d: List[List[str]]) -> Tuple[str, ...]:
        flat = []
        for r in range(2):
            for c in range(8):
                v = board_2d[r][c]
                flat.append(v if v else ".")
        return tuple(flat)

    def _format_move(self, board_t: Tuple[str, ...], mv: Tuple[int, int, bool]) -> str:
        fr, to, is_cap = mv
        piece = board_t[fr]
        pt = piece.upper()
        from_sq = self._index_to_notation(fr)
        to_sq = self._index_to_notation(to)
        if is_cap:
            return f"{pt}{from_sq}x{to_sq}"
        return f"{pt}{from_sq}{to_sq}"

    def _notation_to_index(self, sq: str) -> Optional[int]:
        if not isinstance(sq, str) or len(sq) != 2:
            return None
        file_c = sq[0].lower()
        if file_c not in self.COLS:
            return None
        try:
            rank = int(sq[1])
        except ValueError:
            return None
        if rank not in (1, 2):
            return None
        c = self.COLS.index(file_c)
        r = rank - 1
        return r * 8 + c

    def _index_to_notation(self, idx: int) -> str:
        r, c = divmod(idx, 8)
        return f"{self.COLS[c]}{r + 1}"

    def _is_own_piece(self, piece: str, color: str) -> bool:
        if piece == ".":
            return False
        return piece.isupper() if color == self.WHITE else piece.islower()

    def _is_enemy_piece(self, piece: str, color: str) -> bool:
        if piece == ".":
            return False
        return not self._is_own_piece(piece, color)

    def _other(self, color: str) -> str:
        return self.BLACK if color == self.WHITE else self.WHITE

    def _check_time(self):
        if time.perf_counter() > self._deadline:
            raise TimeoutError
