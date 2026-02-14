"""
Agent Code: A7-TwoByEightChess
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-14 13:38:57
"""

import time

import time

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, board, move_history):
        # Helper functions
        def is_own_piece(piece, color):
            if piece == '':
                return False
            if color == 'W':
                return piece.isupper()
            else:
                return piece.islower()

        def generate_pseudo_legal_moves(board, r, c, color):
            piece = board[r][c]
            ptype = piece.upper()
            moves = []
            if ptype == 'K':
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 2 and 0 <= nc < 8:
                            t = board[nr][nc]
                            if not is_own_piece(t, color):
                                moves.append((nr, nc, t != '' and not is_own_piece(t, color)))
            elif ptype == 'N':
                deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                          (-2, -1), (-2, 1), (2, -1), (2, 1),
                          (0, -2), (0, 2)]
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        t = board[nr][nc]
                        if not is_own_piece(t, color):
                            moves.append((nr, nc, t != '' and not is_own_piece(t, color)))
            elif ptype == 'R':
                # Vertical (only one step due to 2 rows)
                for nr in (0, 1):
                    if nr != r:
                        t = board[nr][c]
                        if t == '':
                            moves.append((nr, c, False))
                        elif not is_own_piece(t, color):
                            moves.append((nr, c, True))
                # Horizontal
                for dc in (-1, 1):
                    nc = c + dc
                    while 0 <= nc < 8:
                        t = board[r][nc]
                        if t == '':
                            moves.append((r, nc, False))
                        elif not is_own_piece(t, color):
                            moves.append((r, nc, True))
                            break
                        else:
                            break
                        nc += dc
            elif ptype == 'P':
                direction = 1 if color == 'W' else -1
                nc = c + direction
                if 0 <= nc < 8 and board[r][nc] == '':
                    moves.append((r, nc, False))
                for dr in (-1, 1):
                    nr = r + dr
                    nc = c + direction
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        t = board[nr][nc]
                        if t != '' and not is_own_piece(t, color):
                            moves.append((nr, nc, True))
            return moves

        def simulate(board, move, color):
            (fr, fc), (tr, tc) = move
            new_board = [row[:] for row in board]
            piece = new_board[fr][fc]
            new_board[tr][tc] = piece
            new_board[fr][fc] = ''
            if piece.upper() == 'P':
                if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                    new_board[tr][tc] = 'R' if color == 'W' else 'r'
            return new_board

        def is_square_attacked(board, sq, by_color):
            sr, sc = sq
            for r in range(2):
                for c in range(8):
                    p = board[r][c]
                    if p and is_own_piece(p, by_color):
                        pt = p.upper()
                        if pt == 'K':
                            if abs(r - sr) <= 1 and abs(c - sc) <= 1:
                                return True
                        elif pt == 'N':
                            dr, dc = abs(r - sr), abs(c - sc)
                            if (dr == 1 and dc == 2) or (dr == 2 and dc == 1) or (dr == 0 and dc == 2) or (dr == 2 and dc == 0):
                                return True
                        elif pt == 'R':
                            if r == sr:
                                step = 1 if c < sc else -1
                                for cc in range(c + step, sc, step):
                                    if board[r][cc] != '':
                                        break
                                else:
                                    return True
                            elif c == sc:
                                step = 1 if r < sr else -1
                                for rr in range(r + step, sr, step):
                                    if board[rr][c] != '':
                                        break
                                else:
                                    return True
                        elif pt == 'P':
                            direction = 1 if by_color == 'W' else -1
                            if sc == c + direction and abs(sr - r) == 1:
                                return True
            return False

        def is_in_check(board, color):
            king_char = 'K' if color == 'W' else 'k'
            for r in range(2):
                for c in range(8):
                    if board[r][c] == king_char:
                        return is_square_attacked(board, (r, c), 'B' if color == 'W' else 'W')
            return True  # King missing

        def generate_legal_moves(board, color):
            legal = []
            for r in range(2):
                for c in range(8):
                    p = board[r][c]
                    if p and is_own_piece(p, color):
                        for tr, tc, cap in generate_pseudo_legal_moves(board, r, c, color):
                            nb = simulate(board, ((r, c), (tr, tc)), color)
                            if not is_in_check(nb, color):
                                legal.append(((r, c), (tr, tc), cap, nb))
            return legal

        def evaluate(board):
            w = b = 0
            for r in range(2):
                for c in range(8):
                    p = board[r][c]
                    if p == 'P': w += 1
                    elif p == 'N': w += 3
                    elif p == 'R': w += 5
                    elif p == 'p': b += 1
                    elif p == 'n': b += 3
                    elif p == 'r': b += 5
            return w - b if self.color == 'W' else b - w

        def minimax(board, depth, turn):
            moves = generate_legal_moves(board, turn)
            if not moves:
                if is_in_check(board, turn):
                    return -10000 if turn == self.color else 10000
                return 0
            if depth == 0:
                return evaluate(board)
            opp = 'B' if turn == 'W' else 'W'
            if turn == self.color:
                best = -float('inf')
                for m in moves:
                    sc = minimax(m[3], depth - 1, opp)
                    best = max(best, sc)
                return best
            else:
                best = float('inf')
                for m in moves:
                    sc = minimax(m[3], depth - 1, self.color)
                    best = min(best, sc)
                return best

        # Main move selection
        legal_moves = generate_legal_moves(board, self.color)
        if not legal_moves:
            return "a0a0"  # Invalid fallback

        if len(legal_moves) == 1:
            best = legal_moves[0]
        else:
            best = None
            best_score = -float('inf')
            opp = 'B' if self.color == 'W' else 'W'
            start = time.time()
            for m in legal_moves:
                if time.time() - start > 0.9:
                    break
                score = minimax(m[3], 2, opp)
                if score > best_score:
                    best_score = score
                    best = m
            if best is None:
                best = legal_moves[0]

        (fr, fc), (tr, tc), cap, _ = best
        cols = 'abcdefgh'
        from_sq = f"{cols[fc]}{fr+1}"
        to_sq = f"{cols[tc]}{tr+1}"
        piece_char = board[fr][fc]
        return f"{piece_char}{from_sq}x{to_sq}" if cap else f"{piece_char}{from_sq}{to_sq}"
