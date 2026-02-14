"""
Agent Code: A7-TwoByEightChess
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-14 14:14:44
"""



class TwoByEightChessAgent:
    COLS = 'abcdefgh'

    def __init__(self, name, color):
        """
        Args:
            name: str
            color: 'W' or 'B'
        """
        self.name = name
        self.color = color  # 'W' or 'B'

    # --- Helper predicates ---
    def _is_white_piece(self, piece):
        return bool(piece) and piece.isupper()

    def _is_black_piece(self, piece):
        return bool(piece) and piece.islower()

    def _is_own_piece(self, piece, color):
        if not piece:
            return False
        return self._is_white_piece(piece) if color == 'W' else self._is_black_piece(piece)

    def _is_enemy_piece(self, piece, color):
        if not piece:
            return False
        return not self._is_own_piece(piece, color)

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"

    # --- Core move generation & validation (mirrors engine rules) ---
    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _get_valid_moves_for_piece(self, board, row, col, ignore_check=False):
        """
        Return list of ((nr,nc), is_capture) for piece at (row,col).
        If ignore_check is False, filter out moves leaving own king in check.
        """
        piece = board[row][col]
        if not piece:
            return []

        color = 'W' if self._is_white_piece(piece) else 'B'
        ptype = piece.upper()
        moves = []

        if ptype == 'K':
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

        elif ptype == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))

        elif ptype == 'R':
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

        elif ptype == 'P':
            direction = 1 if color == 'W' else -1
            # forward
            nc = col + direction
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

        # Filter moves that would leave own king in check
        valid = []
        for to_pos, is_cap in moves:
            if self._is_move_safe(board, (row, col), to_pos):
                valid.append((to_pos, is_cap))
        return valid

    def _is_move_safe(self, board, from_pos, to_pos):
        """Return True if move does not leave mover's king in check."""
        fr, fc = from_pos
        tr, tc = to_pos
        piece = board[fr][fc]
        if not piece:
            return False
        color = 'W' if self._is_white_piece(piece) else 'B'

        # simulate move on a copy
        new_board = [row.copy() for row in board]
        moving_piece = piece
        if moving_piece.upper() == 'P':
            # promotion to rook if reaching last column
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'
        new_board[tr][tc] = moving_piece
        new_board[fr][fc] = ''

        return not self._is_in_check(new_board, color)

    def _is_in_check(self, board, color):
        """Return True if color's king is under attack on given board."""
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True  # missing king considered in-check

        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    moves = self._get_valid_moves_for_piece(board, r, c, ignore_check=True)
                    for to_pos, _ in moves:
                        if to_pos == king_pos:
                            return True
        return False

    # --- Move selection ---
    def _all_legal_moves_with_meta(self, board, color):
        """
        Returns list of dicts with keys:
        'move' (str), 'from' (r,c), 'to' (r,c), 'is_capture' (bool),
        'capture_value' (int), 'gives_check' (bool), 'promotes' (bool), 'piece' (str)
        """
        value_map = {'K': 1000, 'R': 5, 'N': 3, 'P': 1}
        moves = []
        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not self._is_own_piece(piece, color):
                    continue
                ptype = piece.upper()
                from_not = self._to_notation(r, c)
                valid_moves = self._get_valid_moves_for_piece(board, r, c, ignore_check=False)
                for (tr, tc), is_cap in valid_moves:
                    to_not = self._to_notation(tr, tc)
                    move_str = f"{ptype}{from_not}{'x' if is_cap else ''}{to_not}"
                    capture_value = 0
                    if is_cap:
                        captured = board[tr][tc]
                        capture_value = value_map.get(captured.upper(), 0) if captured else 0
                    promotes = (ptype == 'P') and ((color == 'W' and tc == 7) or (color == 'B' and tc == 0))
                    # simulate to see if move gives check
                    new_board = [row.copy() for row in board]
                    moving_piece = piece
                    if ptype == 'P' and promotes:
                        moving_piece = 'R' if color == 'W' else 'r'
                    new_board[tr][tc] = moving_piece
                    new_board[r][c] = ''
                    gives_check = self._is_in_check(new_board, enemy_color)
                    moves.append({
                        'move': move_str,
                        'from': (r, c),
                        'to': (tr, tc),
                        'is_capture': is_cap,
                        'capture_value': capture_value,
                        'gives_check': gives_check,
                        'promotes': promotes,
                        'piece': ptype
                    })
        return moves

    def _all_pseudo_legal_moves(self, board, color):
        """Return simple pseudo-legal move strings (ignore leaving king in check)."""
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not self._is_own_piece(piece, color):
                    continue
                ptype = piece.upper()
                from_not = self._to_notation(r, c)
                # get moves ignoring check safety
                for (tr, tc), is_cap in self._get_valid_moves_for_piece(board, r, c, ignore_check=True):
                    to_not = self._to_notation(tr, tc)
                    move_str = f"{ptype}{from_not}{'x' if is_cap else ''}{to_not}"
                    moves.append(move_str)
        return moves

    def make_move(self, board, move_history):
        """
        Decide and return a move string for the current board and move_history.
        """
        color = self.color
        legal_moves = self._all_legal_moves_with_meta(board, color)

        if not legal_moves:
            # No legal moves (checkmate/stalemate) or cannot find: fallback to pseudo-legal
            pseudo = self._all_pseudo_legal_moves(board, color)
            if not pseudo:
                # No moves at all: return a dummy move (engine will handle)
                # Try to move King in place as last resort
                return f"K{self._to_notation(0,0)}{self._to_notation(0,0)}"
            return random.choice(pseudo)

        # Prefer promotions, then high-value captures, then moves that give check, otherwise random
        def score(m):
            s = 0
            if m['promotes']:
                s += 1000
            s += m['capture_value'] * 10
            if m['gives_check']:
                s += 5
            # small bias: prefer moving Rook and Knight slightly
            if m['piece'] == 'R':
                s += 1
            if m['piece'] == 'N':
                s += 0.5
            # random tie-breaker
            s += random.random() * 0.1
            return s

        best = max(legal_moves, key=score)
        return best['move']
