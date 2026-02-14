"""
Agent Code: A7-TwoByEightChess
Model: z-ai-glm-5-fp8-speedy
Run: 1
Generated: 2026-02-14 13:30:59
"""

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.WHITE = 'W'
        self.BLACK = 'B'
        self.COLS = 'abcdefgh'
        self.max_depth = 5
        self.PIECE_VAL = {'K': 10000, 'R': 600, 'N': 350, 'P': 100}
    
    def _is_white(self, p): return p in ('K', 'N', 'R', 'P')
    def _is_black(self, p): return p in ('k', 'n', 'r', 'p')
    def _color(self, p): return self.WHITE if p and self._is_white(p) else self.BLACK if p else None
    def _enemy(self, color): return self.BLACK if color == self.WHITE else self.WHITE
    def _in_bounds(self, r, c): return 0 <= r < 2 and 0 <= c < 8
    def _pos_to_sq(self, r, c): return f"{self.COLS[c]}{r+1}"
    
    def _find_king(self, bd, color):
        k = 'K' if color == self.WHITE else 'k'
        for r in range(2):
            for c in range(8):
                if bd[r][c] == k: return (r, c)
        return None
    
    def _get_attack_squares(self, bd, r, c):
        p, attacks = bd[r][c], []
        if not p: return attacks
        color, pt = self._color(p), p.upper()
        if pt == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr or dc:
                        nr, nc = r+dr, c+dc
                        if self._in_bounds(nr, nc): attacks.append((nr, nc))
        elif pt == 'N':
            for dr, dc in [(-1,-2),(-1,2),(1,-2),(1,2),(-2,-1),(-2,1),(2,-1),(2,1)]:
                nr, nc = r+dr, c+dc
                if self._in_bounds(nr, nc): attacks.append((nr, nc))
            for dc in [-2, 2]:
                if self._in_bounds(r, c+dc): attacks.append((r, c+dc))
        elif pt == 'R':
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                while self._in_bounds(nr, nc):
                    attacks.append((nr, nc))
                    if bd[nr][nc]: break
                    nr, nc = nr+dr, nc+dc
        elif pt == 'P':
            direction = 1 if color == self.WHITE else -1
            for dr in [-1, 1]:
                nr, nc = r+dr, c+direction
                if self._in_bounds(nr, nc): attacks.append((nr, nc))
        return attacks
    
    def _is_attacked(self, bd, r, c, by_color):
        for pr in range(2):
            for pc in range(8):
                if bd[pr][pc] and self._color(bd[pr][pc]) == by_color:
                    if (r, c) in self._get_attack_squares(bd, pr, pc): return True
        return False
    
    def _is_in_check(self, bd, color):
        kp = self._find_king(bd, color)
        return not kp or self._is_attacked(bd, kp[0], kp[1], self._enemy(color))
    
    def _get_pseudo_moves(self, bd, r, c):
        p = bd[r][c]
        if not p: return []
        color, pt, moves = self._color(p), p.upper(), []
        if pt == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr or dc:
                        nr, nc = r+dr, c+dc
                        if self._in_bounds(nr, nc) and (not bd[nr][nc] or self._color(bd[nr][nc]) != color):
                            moves.append((nr, nc))
        elif pt == 'N':
            for dr, dc in [(-1,-2),(-1,2),(1,-2),(1,2),(-2,-1),(-2,1),(2,-1),(2,1)]:
                nr, nc = r+dr, c+dc
                if self._in_bounds(nr, nc) and (not bd[nr][nc] or self._color(bd[nr][nc]) != color):
                    moves.append((nr, nc))
            for dc in [-2, 2]:
                nr, nc = r, c+dc
                if self._in_bounds(nr, nc) and (not bd[nr][nc] or self._color(bd[nr][nc]) != color):
                    moves.append((nr, nc))
        elif pt == 'R':
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                while self._in_bounds(nr, nc):
                    if not bd[nr][nc]: moves.append((nr, nc))
                    elif self._color(bd[nr][nc]) != color: moves.append((nr, nc)); break
                    else: break
                    nr, nc = nr+dr, nc+dc
        elif pt == 'P':
            direction = 1 if color == self.WHITE else -1
            if self._in_bounds(r, c+direction) and not bd[r][c+direction]: moves.append((r, c+direction))
            for dr in [-1, 1]:
                nr, nc = r+dr, c+direction
                if self._in_bounds(nr, nc) and bd[nr][nc] and self._color(bd[nr][nc]) != color:
                    moves.append((nr, nc))
        return moves
    
    def _make_move_bd(self, bd, fr, fc, tr, tc):
        new_bd = [row[:] for row in bd]
        p, color = new_bd[fr][fc], self._color(new_bd[fr][fc])
        if p.upper() == 'P' and ((color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0)):
            p = 'R' if color == self.WHITE else 'r'
        new_bd[tr][tc], new_bd[fr][fc] = p, ''
        return new_bd
    
    def _get_legal_moves(self, bd, color):
        moves = []
        for r in range(2):
            for c in range(8):
                if bd[r][c] and self._color(bd[r][c]) == color:
                    for tr, tc in self._get_pseudo_moves(bd, r, c):
                        new_bd = self._make_move_bd(bd, r, c, tr, tc)
                        if not self._is_in_check(new_bd, color):
                            moves.append((r, c, tr, tc, bd[tr][tc] != ''))
        return moves
    
    def _eval(self, bd, for_color):
        score = 0
        for r in range(2):
            for c in range(8):
                p = bd[r][c]
                if p:
                    val = self.PIECE_VAL.get(p.upper(), 0)
                    score += val if self._is_white(p) else -val
                    if p == 'P': score += c * 15
                    elif p == 'p': score -= (7 - c) * 15
        score += (len(self._get_legal_moves(bd, self.WHITE)) - len(self._get_legal_moves(bd, self.BLACK))) * 8
        if self._is_in_check(bd, self.BLACK): score += 80
        if self._is_in_check(bd, self.WHITE): score -= 80
        wk, bk = self._find_king(bd, self.WHITE), self._find_king(bd, self.BLACK)
        if wk:
            for r in range(2):
                for c in range(8):
                    if bd[r][c] and self._is_white(bd[r][c]) and bd[r][c] != 'K' and abs(c - wk[1]) <= 2: score += 10
        if bk:
            for r in range(2):
                for c in range(8):
                    if bd[r][c] and self._is_black(bd[r][c]) and bd[r][c] != 'k' and abs(c - bk[1]) <= 2: score -= 10
        return score if for_color == self.WHITE else -score
    
    def _minimax(self, bd, depth, alpha, beta, maximizing, color):
        curr = color if maximizing else self._enemy(color)
        moves = self._get_legal_moves(bd, curr)
        if not moves: return (-50000 + (self.max_depth - depth) if maximizing else 50000 - (self.max_depth - depth), None) if self._is_in_check(bd, curr) else (0, None)
        if depth == 0: return (self._eval(bd, color), None)
        moves.sort(key=lambda m: -self.PIECE_VAL.get(bd[m[3]][m[4]].upper(), 0) * 10 if m[4] else 0)
        best = None
        if maximizing:
            max_eval = float('-inf')
            for fr, fc, tr, tc, is_cap in moves:
                ev, _ = self._minimax(self._make_move_bd(bd, fr, fc, tr, tc), depth-1, alpha, beta, False, color)
                if ev > max_eval: max_eval, best = ev, (fr, fc, tr, tc, is_cap)
                alpha = max(alpha, ev)
                if beta <= alpha: break
            return (max_eval, best)
        else:
            min_eval = float('inf')
            for fr, fc, tr, tc, is_cap in moves:
                ev, _ = self._minimax(self._make_move_bd(bd, fr, fc, tr, tc), depth-1, alpha, beta, True, color)
                if ev < min_eval: min_eval, best = ev, (fr, fc, tr, tc, is_cap)
                beta = min(beta, ev)
                if beta <= alpha: break
            return (min_eval, best)
    
    def make_move(self, board, move_history):
        bd = [list(row) for row in board]
        moves = self._get_legal_moves(bd, self.color)
        if not moves: return ""
        enemy = self._enemy(self.color)
        for fr, fc, tr, tc, is_cap in moves:
            new_bd = self._make_move_bd(bd, fr, fc, tr, tc)
            if self._is_in_check(new_bd, enemy) and not self._get_legal_moves(new_bd, enemy):
                return f"{bd[fr][fc].upper()}{self._pos_to_sq(fr,fc)}x{self._pos_to_sq(tr,tc)}" if is_cap else f"{bd[fr][fc].upper()}{self._pos_to_sq(fr,fc)}{self._pos_to_sq(tr,tc)}"
        _, best = self._minimax(bd, self.max_depth, float('-inf'), float('inf'), True, self.color)
        fr, fc, tr, tc, is_cap = best if best else moves[0]
        return f"{bd[fr][fc].upper()}{self._pos_to_sq(fr,fc)}x{self._pos_to_sq(tr,tc)}" if is_cap else f"{bd[fr][fc].upper()}{self._pos_to_sq(fr,fc)}{self._pos_to_sq(tr,tc)}"