"""
Agent Code: A7-TwoByEightChess
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-14 14:14:44
"""



class TwoByEightChessAgent:
    COLS = 'abcdefgh'

    def __init__(self, name, color):
        """
        Args:
            name: str - agent name
            color: 'W' or 'B'
        """
        self.name = name
        self.color = color  # 'W' or 'B'

    # ---------- Helper utilities ----------
    def _in_bounds(self, r, c):
        return 0 <= r < 2 and 0 <= c < 8

    def _is_white_piece(self, p):
        return p in ('K', 'N', 'R', 'P')

    def _is_black_piece(self, p):
        return p in ('k', 'n', 'r', 'p')

    def _is_own_piece(self, p, color):
        if p == '':
            return False
        return self._is_white_piece(p) if color == 'W' else self._is_black_piece(p)

    def _is_enemy_piece(self, p, color):
        if p == '':
            return False
        return not self._is_own_piece(p, color)

    def _piece_type(self, p):
        return p.upper() if p else ''

    def _pos_to_notation(self, r, c):
        return f"{self.COLS[c]}{r + 1}"

    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    # ---------- Move generation & legality (mirrors engine rules) ----------
    def _get_valid_moves_for_piece(self, board, row, col, ignore_check=False):
        piece = board[row][col]
        if not piece:
            return []
        color = 'W' if self._is_white_piece(piece) else 'B'
        pt = self._piece_type(piece)
        moves = []

        if pt == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            moves.append(((nr, nc), is_capture))

        elif pt == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear = [(0, -2), (0, 2)]
            for dr, dc in (l_deltas + linear):
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))

        elif pt == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        moves.append(((nr, nc), False))
                    elif self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif pt == 'P':
            direction = 1 if color == 'W' else -1
            nc = col + direction
            # forward
            if self._in_bounds(row, nc) and board[row][nc] == '':
                moves.append(((row, nc), False))
            # captures
            for dr in (-1, 1):
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))

        if ignore_check:
            return moves

        # filter moves that leave own king in check
        valid = []
        for to_pos, is_capture in moves:
            if self._is_move_safe(board, (row, col), to_pos, color):
                valid.append((to_pos, is_capture))
        return valid

    def _is_move_safe(self, board, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        original_from = board[fr][fc]
        original_to = board[tr][tc]

        moving_piece = original_from
        # simulate promotion
        if moving_piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'

        board[tr][tc] = moving_piece
        board[fr][fc] = ''

        in_check = self._is_in_check(board, color)

        # undo
        board[fr][fc] = original_from
        board[tr][tc] = original_to

        return not in_check

    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True
        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    enemy_moves = self._get_valid_moves_for_piece(board, r, c, ignore_check=True)
                    for to_pos, _ in enemy_moves:
                        if to_pos == king_pos:
                            return True
        return False

    def _simulate_move(self, board, from_pos, to_pos, color):
        bd = [row[:] for row in board]
        fr, fc = from_pos
        tr, tc = to_pos
        moving_piece = bd[fr][fc]
        if moving_piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'
        bd[tr][tc] = moving_piece
        bd[fr][fc] = ''
        return bd

    def _get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    pt = self._piece_type(piece)
                    valid = self._get_valid_moves_for_piece(board, r, c)
                    for (tr, tc), is_capture in valid:
                        moves.append((pt, (r, c), (tr, tc), is_capture))
        return moves

    # ---------- Move selection strategy ----------
    def make_move(self, board, move_history):
        """
        Decide the next move. Returns a move string in the required notation.
        Strategy:
            - Generate all legal moves (not leaving king in check).
            - Score moves prioritizing: capture value, pawn promotion, giving check.
            - Return highest-scoring move; deterministic tie-breaker by lexicographic move string.
            - If no legal moves, return a fallback move generated ignoring check (engine will handle it).
        """
        bd = [row[:] for row in board]  # local copy (do not mutate caller board)
        color = self.color
        opponent = 'B' if color == 'W' else 'W'

        # Piece capture value weights (upper-case)
        cap_values = {'K': 1000, 'R': 5, 'N': 3, 'P': 1}

        legal_moves = self._get_all_valid_moves(bd, color)

        candidates = []
        for pt, from_pos, to_pos, is_capture in legal_moves:
            fr, fc = from_pos
            tr, tc = to_pos
            target_piece = bd[tr][tc]
            score = 0

            # capture value
            if is_capture and target_piece:
                score += cap_values.get(target_piece.upper(), 0) * 100

            # promotion
            if pt == 'P':
                if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                    score += 500

            # check after move
            sim_bd = self._simulate_move(bd, from_pos, to_pos, color)
            if self._is_in_check(sim_bd, opponent):
                score += 200

            # small preference to advance pawns and to use non-king moves
            if pt == 'P':
                # advancing pawn one step towards promotion gets a small bonus
                if (color == 'W' and tc > fc) or (color == 'B' and tc < fc):
                    score += 5
            if pt == 'K':
                score -= 1

            # Build move notation
            from_not = self._pos_to_notation(fr, fc)
            to_not = self._pos_to_notation(tr, tc)
            move_str = f"{pt}{from_not}{'x' if is_capture else ''}{to_not}"
            candidates.append((score, move_str))

        if candidates:
            # choose highest score; tie-breaker lexicographically smallest move string
            candidates.sort(key=lambda x: (-x[0], x[1]))
            return candidates[0][1]

        # Fallback: try moves ignoring check (the engine will use a random valid move if this is invalid)
        fallback_moves = []
        for r in range(2):
            for c in range(8):
                piece = bd[r][c]
                if piece and self._is_own_piece(piece, color):
                    pt = self._piece_type(piece)
                    moves_ignore = self._get_valid_moves_for_piece(bd, r, c, ignore_check=True)
                    for (tr, tc), is_capture in moves_ignore:
                        from_not = self._pos_to_notation(r, c)
                        to_not = self._pos_to_notation(tr, tc)
                        move_str = f"{pt}{from_not}{'x' if is_capture else ''}{to_not}"
                        fallback_moves.append(move_str)
        if fallback_moves:
            fallback_moves.sort()
            return fallback_moves[0]

        # As an absolute last resort (should be rare) return a trivially formatted move that will be rejected
        # and cause the engine to play a random valid move on our behalf.
        # Choose a from-square where we have a piece (if any), else default 'a1'.
        for r in range(2):
            for c in range(8):
                if bd[r][c] and self._is_own_piece(bd[r][c], color):
                    from_not = self._pos_to_notation(r, c)
                    to_not = from_not
                    return f"{self._piece_type(bd[r][c])}{from_not}{to_not}"
        return "Ka1a1"
