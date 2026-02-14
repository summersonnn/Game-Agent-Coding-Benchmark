"""
Agent Code: A7-TwoByEightChess
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-14 13:30:59
"""

import time
from typing import List, Tuple, Optional, Dict, Any

import time
from typing import List, Tuple, Optional, Dict, Any


class TwoByEightChessAgent:
    COLS = "abcdefgh"
    WHITE = "W"
    BLACK = "B"

    # Search / eval constants
    MATE = 100000
    INF = 10**9
    PIECE_VALUE = {"K": 0, "R": 500, "N": 300, "P": 100}

    def __init__(self, name, color):
        self.name = name
        self.color = color  # 'W' or 'B'
        self._tt: Dict[Any, Tuple[int, int]] = {}  # (board, turn) -> (depth, value)

    # ------------------------ Public API ------------------------

    def make_move(self, board, move_history):
        # Time management: engine allows 1s; keep a safety buffer.
        start = time.time()
        time_limit = 0.92

        b = self._freeze_board(board)
        color = self.color

        legal = self._get_all_legal_moves(b, color)
        if not legal:
            # Should rarely/never happen if engine ends earlier; return something.
            return "Ka1a1"

        # Iterative deepening
        best_move = legal[0]
        best_val = -self.INF

        self._tt.clear()

        max_depth = 8  # usually won't reach due to time
        for depth in range(1, max_depth + 1):
            if time.time() - start > time_limit:
                break
            try:
                move, val = self._search_root(b, color, depth, start, time_limit)
                if move is not None:
                    best_move, best_val = move, val
            except TimeoutError:
                break

        return self._move_to_str(b, best_move, color)

    # ------------------------ Core search ------------------------

    def _search_root(self, board, color, depth, start, time_limit):
        moves = self._get_all_legal_moves(board, color)
        if not moves:
            return None, self._terminal_score(board, color, depth_left=depth)

        moves = self._order_moves(board, color, moves)

        best_move = None
        best_val = -self.INF
        alpha = -self.INF
        beta = self.INF

        opp = self._opp(color)
        for mv in moves:
            self._check_time(start, time_limit)
            child = self._apply_move(board, mv, color)
            val = -self._negamax(child, opp, depth - 1, -beta, -alpha, start, time_limit)
            if val > best_val:
                best_val = val
                best_move = mv
            if val > alpha:
                alpha = val

        return best_move, best_val

    def _negamax(self, board, color, depth, alpha, beta, start, time_limit):
        self._check_time(start, time_limit)

        tt_key = (board, color)
        tt_hit = self._tt.get(tt_key)
        if tt_hit is not None:
            tt_depth, tt_val = tt_hit
            if tt_depth >= depth:
                return tt_val

        # Terminal / horizon
        legal = self._get_all_legal_moves(board, color)
        if depth <= 0 or not legal or self._only_kings(board):
            val = self._terminal_or_eval(board, color, legal, depth)
            self._tt[tt_key] = (depth, val)
            return val

        legal = self._order_moves(board, color, legal)

        best = -self.INF
        opp = self._opp(color)

        for mv in legal:
            child = self._apply_move(board, mv, color)
            val = -self._negamax(child, opp, depth - 1, -beta, -alpha, start, time_limit)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        self._tt[tt_key] = (depth, best)
        return best

    def _terminal_or_eval(self, board, color, legal_moves, depth):
        # If no moves: checkmate or stalemate
        if not legal_moves:
            return self._terminal_score(board, color, depth_left=depth)
        if self._only_kings(board):
            return 0
        return self._evaluate(board, color)

    def _terminal_score(self, board, color, depth_left):
        # Side to move has no legal moves.
        if self._is_in_check(board, color):
            # Checkmated: prefer faster mates (depth_left higher => sooner)
            return -self.MATE + (10 - depth_left)
        # Stalemate
        return 0

    # ------------------------ Move generation ------------------------

    def _get_all_legal_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if not p or not self._is_own_piece(p, color):
                    continue
                pseudo = self._pseudo_moves_for_piece(board, r, c, color)
                for (tr, tc, is_cap) in pseudo:
                    mv = (r, c, tr, tc, is_cap)
                    if self._is_move_safe(board, mv, color):
                        moves.append(mv)
        return moves

    def _pseudo_moves_for_piece(self, board, r, c, color):
        p = board[r][c]
        if not p:
            return []
        t = p.upper()
        out = []

        if t == "K":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if not self._in_bounds(nr, nc):
                        continue
                    target = board[nr][nc]
                    if self._is_own_piece(target, color):
                        continue
                    out.append((nr, nc, self._is_enemy_piece(target, color)))

        elif t == "N":
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear:
                nr, nc = r + dr, c + dc
                if not self._in_bounds(nr, nc):
                    continue
                target = board[nr][nc]
                if self._is_own_piece(target, color):
                    continue
                out.append((nr, nc, self._is_enemy_piece(target, color)))

        elif t == "R":
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == "":
                        out.append((nr, nc, False))
                    else:
                        if self._is_enemy_piece(target, color):
                            out.append((nr, nc, True))
                        break
                    nr += dr
                    nc += dc

        elif t == "P":
            direction = 1 if color == self.WHITE else -1
            # forward
            nc = c + direction
            if self._in_bounds(r, nc) and board[r][nc] == "":
                out.append((r, nc, False))
            # diagonal captures
            for dr in (-1, 1):
                nr, nc = r + dr, c + direction
                if not self._in_bounds(nr, nc):
                    continue
                target = board[nr][nc]
                if self._is_enemy_piece(target, color):
                    out.append((nr, nc, True))

        return out

    def _is_move_safe(self, board, mv, color):
        child = self._apply_move(board, mv, color, promote=True)
        return not self._is_in_check(child, color)

    # ------------------------ Check detection ------------------------

    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True  # king missing -> treated as in check
        kr, kc = king_pos
        enemy = self._opp(color)

        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if not p or not self._is_own_piece(p, enemy):
                    continue
                for (tr, tc, _) in self._pseudo_moves_for_piece(board, r, c, enemy):
                    if tr == kr and tc == kc:
                        return True
        return False

    def _find_king(self, board, color):
        target = "K" if color == self.WHITE else "k"
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    # ------------------------ Apply / encode moves ------------------------

    def _apply_move(self, board, mv, color, promote=True):
        fr, fc, tr, tc, _ = mv
        moving = board[fr][fc]

        b0 = list(board[0])
        b1 = list(board[1])
        b = [b0, b1]

        b[fr][fc] = ""
        placed = moving

        if promote and moving.upper() == "P":
            if (color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0):
                placed = "R" if color == self.WHITE else "r"

        b[tr][tc] = placed
        return (tuple(b[0]), tuple(b[1]))

    def _move_to_str(self, board, mv, color):
        fr, fc, tr, tc, is_cap = mv
        p = board[fr][fc]
        piece_type = p.upper() if p else "K"
        from_sq = self._pos_to_notation(fr, fc)
        to_sq = self._pos_to_notation(tr, tc)
        if is_cap:
            return f"{piece_type}{from_sq}x{to_sq}"
        return f"{piece_type}{from_sq}{to_sq}"

    # ------------------------ Move ordering ------------------------

    def _order_moves(self, board, color, moves):
        # Higher score first
        def mscore(mv):
            fr, fc, tr, tc, is_cap = mv
            moving = board[fr][fc]
            target = board[tr][tc]
            score = 0

            if is_cap:
                score += 10000
                score += 10 * self._piece_val(target) - self._piece_val(moving)

            # promotion (pawn reaches last file)
            if moving.upper() == "P":
                if (color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0):
                    score += 8000

            # check bonus
            child = self._apply_move(board, mv, color, promote=True)
            if self._is_in_check(child, self._opp(color)):
                score += 5000

            # slight centralization: columns d/e (3/4)
            score += 2 * (4 - abs(3.5 - tc))
            return score

        return sorted(moves, key=mscore, reverse=True)

    # ------------------------ Evaluation ------------------------

    def _evaluate(self, board, color_to_move):
        # Base: material + pawn progress + activity; returned from POV of side to move.
        base = 0

        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if not p:
                    continue
                sgn = 1 if self._is_white_piece(p) else -1
                t = p.upper()

                base += sgn * self.PIECE_VALUE.get(t, 0)

                # pawn progress (strong on 2x8)
                if t == "P":
                    # white advances to the right (higher col), black to the left
                    progress = c if sgn == 1 else (7 - c)
                    base += sgn * (12 * progress)  # up to ~84

                # minor piece activity (prefer central-ish)
                if t in ("N", "R"):
                    base += sgn * int(4 - abs(3.5 - c))  # small

        # Check pressure
        if self._is_in_check(board, self._opp(color_to_move)):
            # If opponent currently in check, that's good for side to move.
            base += 35 if color_to_move == self.WHITE else -35

        # Convert to POV of side to move
        return base if color_to_move == self.WHITE else -base

    # ------------------------ Utilities ------------------------

    def _check_time(self, start, time_limit):
        if time.time() - start > time_limit:
            raise TimeoutError

    def _freeze_board(self, board_ll: List[List[str]]):
        # Normalize empties to '' as engine uses.
        r0 = tuple(x if x is not None else "" for x in board_ll[0])
        r1 = tuple(x if x is not None else "" for x in board_ll[1])
        return (r0, r1)

    def _pos_to_notation(self, r, c):
        return f"{self.COLS[c]}{r + 1}"

    def _in_bounds(self, r, c):
        return 0 <= r < 2 and 0 <= c < 8

    def _opp(self, color):
        return self.BLACK if color == self.WHITE else self.WHITE

    def _is_white_piece(self, p):
        return p in ("K", "N", "R", "P")

    def _is_black_piece(self, p):
        return p in ("k", "n", "r", "p")

    def _is_own_piece(self, p, color):
        if not p:
            return False
        return self._is_white_piece(p) if color == self.WHITE else self._is_black_piece(p)

    def _is_enemy_piece(self, p, color):
        if not p:
            return False
        return not self._is_own_piece(p, color)

    def _piece_val(self, p):
        if not p:
            return 0
        return self.PIECE_VALUE.get(p.upper(), 0)

    def _only_kings(self, board):
        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if p and p.upper() != "K":
                    return False
        return True
