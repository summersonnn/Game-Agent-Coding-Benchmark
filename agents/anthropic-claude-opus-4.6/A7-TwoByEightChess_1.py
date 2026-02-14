"""
Agent Code: A7-TwoByEightChess
Model: anthropic-claude-opus-4.6
Run: 1
Generated: 2026-02-14 13:16:13
"""

import time


class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.opp_color = 'B' if color == 'W' else 'W'
        self.tt = {}  # Transposition table: key -> (depth, score, flag, best_move)
        self.start_time = 0
        self.time_limit = 0.85

    def make_move(self, board, move_history):
        self.start_time = time.time()
        if len(self.tt) > 800000:
            self.tt = {}

        bd = [board[0][:], board[1][:]]
        moves = self._gen_moves(bd, self.color)

        if not moves:
            return "Ka1a2"
        if len(moves) == 1:
            return self._fmt(moves[0])

        best = moves[0]
        for depth in range(1, 100):
            if time.time() - self.start_time > 0.45:
                break
            try:
                m, s = self._root_search(bd, moves, depth)
                best = m
                if abs(s) > 9000:
                    break
            except TimeoutError:
                break

        return self._fmt(best)

    def _root_search(self, bd, moves, depth):
        alpha, beta = -99999, 99999
        best_s, best_m = -99999, moves[0]
        key = self._bkey(bd, self.color)
        e = self.tt.get(key)
        tm = e[3] if e else None

        for m in self._order(bd, moves, tm):
            u = self._do(bd, m)
            s = -self._search(bd, depth - 1, -beta, -alpha, self.opp_color)
            self._undo(bd, u)
            if s > best_s:
                best_s, best_m = s, m
            alpha = max(alpha, s)

        self.tt[key] = (depth, best_s, 0, best_m)
        return best_m, best_s

    def _search(self, bd, depth, alpha, beta, color):
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError()

        key = self._bkey(bd, color)
        e = self.tt.get(key)
        tm = None
        if e:
            tm = e[3]
            if e[0] >= depth:
                s, f = e[1], e[2]
                if f == 0: return s
                if f == 1 and s >= beta: return s
                if f == -1 and s <= alpha: return s

        opp = 'B' if color == 'W' else 'W'
        ic = self._in_check(bd, color)

        if depth <= 0 and not ic:
            return self._qsearch(bd, alpha, beta, color, 6)

        moves = self._gen_moves(bd, color)
        if not moves:
            return (-10000 - depth) if ic else 0

        a0 = alpha
        best_s, best_m = -99999, moves[0]

        for m in self._order(bd, moves, tm):
            u = self._do(bd, m)
            s = -self._search(bd, depth - 1, -beta, -alpha, opp)
            self._undo(bd, u)
            if s > best_s:
                best_s, best_m = s, m
            alpha = max(alpha, s)
            if alpha >= beta:
                break

        f = 0 if a0 < best_s < beta else (1 if best_s >= beta else -1)
        self.tt[key] = (depth, best_s, f, best_m)
        return best_s

    def _qsearch(self, bd, alpha, beta, color, qd):
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError()

        ic = self._in_check(bd, color)

        if ic:
            moves = self._gen_moves(bd, color)
            if not moves:
                return -10000 - qd
            opp = 'B' if color == 'W' else 'W'
            best = -99999
            for m in moves:
                u = self._do(bd, m)
                s = -self._qsearch(bd, -beta, -alpha, opp, qd - 1)
                self._undo(bd, u)
                best = max(best, s)
                alpha = max(alpha, s)
                if alpha >= beta:
                    break
            return best

        ev = self._eval(bd, color)
        if ev >= beta: return beta
        alpha = max(alpha, ev)
        if qd <= 0: return alpha

        opp = 'B' if color == 'W' else 'W'
        for m in self._gen_moves(bd, color, tactical=True):
            u = self._do(bd, m)
            s = -self._qsearch(bd, -beta, -alpha, opp, qd - 1)
            self._undo(bd, u)
            if s >= beta: return beta
            alpha = max(alpha, s)

        return alpha

    def _eval(self, bd, color):
        s = 0
        for r in range(2):
            for c in range(8):
                p = bd[r][c]
                if not p: continue
                pt = p.upper()
                v = 0
                if pt == 'K':
                    v = 10000
                elif pt == 'R':
                    v = 500
                elif pt == 'N':
                    v = 300 + min(c, 7 - c, 3) * 8
                elif pt == 'P':
                    v = 100
                    if p.isupper():
                        adv = max(0, c - 2)
                        v += adv * 60
                        if c >= 6: v += 100
                    else:
                        adv = max(0, 5 - c)
                        v += adv * 60
                        if c <= 1: v += 100
                s += v if p.isupper() else -v
        return s if color == 'W' else -s

    def _order(self, bd, moves, tm=None):
        PV = {'K':100,'R':5,'N':3,'P':1,'k':100,'r':5,'n':3,'p':1}
        def sc(m):
            if m == tm: return -999999
            s = 0
            if m[5]:
                s -= 10000 + PV.get(m[5], 0) * 100 - PV.get(m[0].upper(), 0)
            if m[6]: s -= 5000
            return s
        return sorted(moves, key=sc)

    def _do(self, bd, m):
        _, fr, fc, tr, tc, _, pr = m
        of, ot = bd[fr][fc], bd[tr][tc]
        bd[fr][fc] = ''
        bd[tr][tc] = pr if pr else of
        return (of, fr, fc, ot, tr, tc)

    def _undo(self, bd, u):
        of, fr, fc, ot, tr, tc = u
        bd[fr][fc] = of
        bd[tr][tc] = ot

    def _gen_moves(self, bd, color, tactical=False):
        moves = []
        w = color == 'W'
        for r in range(2):
            for c in range(8):
                p = bd[r][c]
                if not p or (w != p.isupper()): continue
                pt = p.upper()
                for tr, tc, cap in self._targets(bd, r, c, pt, w):
                    if tactical:
                        is_promo = pt == 'P' and ((w and tc == 7) or (not w and tc == 0))
                        if not cap and not is_promo: continue

                    capt = bd[tr][tc] if cap else ''
                    pr = ''
                    if pt == 'P' and ((w and tc == 7) or (not w and tc == 0)):
                        pr = 'R' if w else 'r'

                    of, ot = bd[r][c], bd[tr][tc]
                    bd[r][c] = ''
                    bd[tr][tc] = pr if pr else p
                    ok = not self._in_check(bd, color)
                    bd[r][c] = of
                    bd[tr][tc] = ot

                    if ok:
                        moves.append((p, r, c, tr, tc, capt, pr))
        return moves

    def _targets(self, bd, r, c, pt, w):
        res = []
        if pt == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        t = bd[nr][nc]
                        if not t: res.append((nr, nc, False))
                        elif w != t.isupper(): res.append((nr, nc, True))
        elif pt == 'N':
            for dr, dc in ((-1,-2),(-1,2),(1,-2),(1,2),(0,-2),(0,2)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    t = bd[nr][nc]
                    if not t: res.append((nr, nc, False))
                    elif w != t.isupper(): res.append((nr, nc, True))
        elif pt == 'R':
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr, nc = r + dr, c + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    t = bd[nr][nc]
                    if not t: res.append((nr, nc, False))
                    elif w != t.isupper(): res.append((nr, nc, True)); break
                    else: break
                    nr += dr; nc += dc
        elif pt == 'P':
            d = 1 if w else -1
            nc = c + d
            if 0 <= nc < 8:
                if not bd[r][nc]: res.append((r, nc, False))
                for dr in (-1, 1):
                    nr = r + dr
                    if 0 <= nr < 2:
                        t = bd[nr][nc]
                        if t and w != t.isupper(): res.append((nr, nc, True))
        return res

    def _in_check(self, bd, color):
        kg = 'K' if color == 'W' else 'k'
        kr = kc = -1
        for r in range(2):
            for c in range(8):
                if bd[r][c] == kg:
                    kr, kc = r, c
                    break
            if kr >= 0: break
        if kr < 0: return True

        ew = color != 'W'
        for r in range(2):
            for c in range(8):
                p = bd[r][c]
                if not p or (ew != p.isupper()): continue
                pt = p.upper()
                if pt == 'K':
                    if abs(r - kr) <= 1 and abs(c - kc) <= 1: return True
                elif pt == 'N':
                    dr, dc = kr - r, kc - c
                    if (abs(dr) == 1 and abs(dc) == 2) or (dr == 0 and abs(dc) == 2):
                        return True
                elif pt == 'R':
                    if r == kr:
                        step = 1 if kc > c else -1
                        blocked = False
                        for cc in range(c + step, kc, step):
                            if bd[r][cc]: blocked = True; break
                        if not blocked: return True
                    elif c == kc:
                        return True
                elif pt == 'P':
                    d = 1 if ew else -1
                    if kc == c + d and abs(kr - r) == 1: return True
        return False

    def _bkey(self, bd, color):
        return (tuple(bd[0]), tuple(bd[1]), color)

    def _fmt(self, m):
        p, fr, fc, tr, tc, cap, pr = m
        C = 'abcdefgh'
        return f"{p.upper()}{C[fc]}{fr+1}{'x' if cap else ''}{C[tc]}{tr+1}"