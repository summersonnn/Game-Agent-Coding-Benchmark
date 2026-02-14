"""
Agent Code: A7-TwoByEightChess
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-14 13:17:43
"""



import random

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
                return piece in ('K', 'N', 'R', 'P')
            else:
                return piece in ('k', 'n', 'r', 'p')

        def is_enemy_piece(piece, color):
            if piece == '':
                return False
            return not is_own_piece(piece, color)

        def find_king(board, color):
            king = 'K' if color == 'W' else 'k'
            for r in range(2):
                for c in range(8):
                    if board[r][c] == king:
                        return (r, c)
            return None

        def get_attacked_squares(board, row, col, color):
            piece = board[row][col]
            if not piece:
                return set()
            pt = piece.upper()
            attacks = set()
            if pt == 'K':
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        r, c = row + dr, col + dc
                        if 0 <= r < 2 and 0 <= c < 8:
                            attacks.add((r, c))
            elif pt == 'N':
                deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                          (-2, -1), (-2, 1), (2, -1), (2, 1),
                          (0, -2), (0, 2)]
                for dr, dc in deltas:
                    r, c = row + dr, col + dc
                    if 0 <= r < 2 and 0 <= c < 8:
                        attacks.add((r, c))
            elif pt == 'R':
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    r, c = row + dr, col + dc
                    while 0 <= r < 2 and 0 <= c < 8:
                        target = board[r][c]
                        if target == '':
                            attacks.add((r, c))
                        elif is_enemy_piece(target, color):
                            attacks.add((r, c))
                            break
                        else:
                            break
                        r += dr
                        c += dc
            elif pt == 'P':
                direction = 1 if color == 'W' else -1
                nc = col + direction
                if 0 <= row < 2 and 0 <= nc < 8 and board[row][nc] == '':
                    attacks.add((row, nc))
                for dr in (-1, 1):
                    nr = row + dr
                    nc = col + direction
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if is_enemy_piece(target, color):
                            attacks.add((nr, nc))
            return attacks

        def is_square_attacked(board, row, col, attacker_color):
            for r in range(2):
                for c in range(8):
                    piece = board[r][c]
                    if piece and is_own_piece(piece, attacker_color):
                        if (row, col) in get_attacked_squares(board, r, c, attacker_color):
                            return True
            return False

        def is_king_in_check(board, color):
            king_pos = find_king(board, color)
            if king_pos is None:
                return True
            attacker = 'B' if color == 'W' else 'W'
            return is_square_attacked(board, king_pos[0], king_pos[1], attacker)

        def simulate_move(board, from_pos, to_pos, color):
            new_board = [row[:] for row in board]
            fr, fc = from_pos
            tr, tc = to_pos
            piece = new_board[fr][fc]
            new_board[tr][tc] = piece
            new_board[fr][fc] = ''
            if piece.upper() == 'P':
                if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                    new_board[tr][tc] = 'R' if color == 'W' else 'r'
            return new_board

        def generate_pseudo_moves(board, row, col, color):
            piece = board[row][col]
            if not piece:
                return []
            pt = piece.upper()
            moves = []
            if pt == 'K':
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        r, c = row + dr, col + dc
                        if 0 <= r < 2 and 0 <= c < 8:
                            target = board[r][c]
                            if not is_own_piece(target, color):
                                moves.append((r, c))
            elif pt == 'N':
                deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                          (-2, -1), (-2, 1), (2, -1), (2, 1),
                          (0, -2), (0, 2)]
                for dr, dc in deltas:
                    r, c = row + dr, col + dc
                    if 0 <= r < 2 and 0 <= c < 8:
                        target = board[r][c]
                        if not is_own_piece(target, color):
                            moves.append((r, c))
            elif pt == 'R':
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    r, c = row + dr, col + dc
                    while 0 <= r < 2 and 0 <= c < 8:
                        target = board[r][c]
                        if target == '':
                            moves.append((r, c))
                        elif is_enemy_piece(target, color):
                            moves.append((r, c))
                            break
                        else:
                            break
                        r += dr
                        c += dc
            elif pt == 'P':
                direction = 1 if color == 'W' else -1
                nc = col + direction
                if 0 <= row < 2 and 0 <= nc < 8 and board[row][nc] == '':
                    moves.append((row, nc))
                for dr in (-1, 1):
                    nr = row + dr
                    nc = col + direction
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if is_enemy_piece(target, color):
                            moves.append((nr, nc))
            return moves

        def pos_to_notation(row, col):
            cols = 'abcdefgh'
            return f"{cols[col]}{row + 1}"

        # Main logic
        in_check = is_king_in_check(board, self.color)
        legal_moves = []  # (piece, from_pos, to_pos, is_capture, gives_check)

        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and is_own_piece(piece, self.color):
                    pseudo_moves = generate_pseudo_moves(board, r, c, self.color)
                    for (tr, tc) in pseudo_moves:
                        from_pos = (r, c)
                        to_pos = (tr, tc)
                        is_capture = is_enemy_piece(board[tr][tc], self.color)
                        new_board = simulate_move(board, from_pos, to_pos, self.color)
                        safe = not is_king_in_check(new_board, self.color)
                        if safe:
                            opponent = 'B' if self.color == 'W' else 'W'
                            gives_check = is_king_in_check(new_board, opponent)
                            legal_moves.append((piece, from_pos, to_pos, is_capture, gives_check))

        if not legal_moves:
            return "a1a1"  # Invalid move; engine will replace with random valid move (if any)

        # Score moves
        scored = []
        for piece, from_pos, to_pos, is_capture, gives_check in legal_moves:
            score = 0
            if is_capture:
                score += 10
            if gives_check:
                score += 5

            fr, fc = from_pos
            tr, tc = to_pos
            pt = piece.upper()

            if pt == 'N':
                if 3 <= tc <= 6:
                    score += 2
            elif pt == 'R':
                if 3 <= tc <= 6:
                    score += 2
            elif pt == 'P':
                if self.color == 'W':
                    if tc > fc:
                        score += 1
                        if tc == 7:
                            score += 10
                else:
                    if tc < fc:
                        score += 1
                        if tc == 0:
                            score += 10
            elif pt == 'K':
                if not in_check:
                    score -= 5

            scored.append((score, piece, from_pos, to_pos, is_capture))

        max_score = max(s for s, *_ in scored)
        best = [ (piece, from_pos, to_pos, is_capture) for s, piece, from_pos, to_pos, is_capture in scored if s == max_score ]
        piece, from_pos, to_pos, is_capture = random.choice(best)

        from_sq = pos_to_notation(from_pos[0], from_pos[1])
        to_sq = pos_to_notation(to_pos[0], to_pos[1])
        piece_char = piece.upper() if self.color == 'W' else piece.lower()

        if is_capture:
            return f"{piece_char}{from_sq}x{to_sq}"
        else:
            return f"{piece_char}{from_sq}{to_sq}"
