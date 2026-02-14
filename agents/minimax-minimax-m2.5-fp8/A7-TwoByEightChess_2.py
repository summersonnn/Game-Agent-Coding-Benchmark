"""
Agent Code: A7-TwoByEightChess
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-14 13:30:59
"""



class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.cols = 'abcdefgh'               # column letters a‑h
        self.piece_values = {'R': 5, 'N': 3, 'P': 1, 'K': 0}
        self.search_depth = 3                # plies to look ahead

    # ---------------------------------------------------------------------
    # Main entry point
    # ---------------------------------------------------------------------
    def make_move(self, board, move_history):
        """Return a legal move in algebraic notation."""
        # all legal moves for our colour
        moves = self.legal_moves(board, self.color)
        if not moves:                         # should not happen unless game over
            return ""

        # check for an immediate checkmate
        for move in moves:
            new_board = self.apply_move(board, move, self.color)
            if not self.has_any_legal_moves(new_board, self.other_color()):
                if self.is_in_check(new_board, self.other_color()):
                    return self.move_to_string(move, board)

        # otherwise use minimax with alpha‑beta pruning
        best_move = None
        best_value = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        depth = self.search_depth

        for move in moves:
            new_board = self.apply_move(board, move, self.color)
            val = self.minimax(new_board, depth - 1, alpha, beta,
                               self.other_color())
            if val > best_value:
                best_value = val
                best_move = move

        return self.move_to_string(best_move, board)

    # ---------------------------------------------------------------------
    # Helper methods
    # ---------------------------------------------------------------------
    def other_color(self):
        return 'B' if self.color == 'W' else 'W'

    def is_own_piece(self, piece, color):
        if piece == '':
            return False
        return piece.isupper() if color == 'W' else piece.islower()

    def is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self.is_own_piece(piece, color)

    # ---------------------------------------------------------------------
    # Move generation (ignoring check)
    # ---------------------------------------------------------------------
    def get_moves(self, board, r, c, color):
        """All pseudo‑legal destinations for the piece at (r,c)."""
        piece = board[r][c]
        if not piece:
            return []
        ptype = piece.upper()
        moves = []

        if ptype == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if not self.is_own_piece(target, color):
                            capture = self.is_enemy_piece(target, color)
                            moves.append(((nr, nc), capture))

        elif ptype == 'N':
            # L‑shape
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            # 2‑square horizontal jump
            linear = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not self.is_own_piece(target, color):
                        capture = self.is_enemy_piece(target, color)
                        moves.append(((nr, nc), capture))

        elif ptype == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '':
                        moves.append(((nr, nc), False))
                    elif self.is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif ptype == 'P':
            direction = 1 if color == 'W' else -1
            # forward move (no capture)
            nc = c + direction
            if 0 <= nc < 8 and board[r][nc] == '':
                moves.append(((r, nc), False))
            # diagonal captures
            for dr in (-1, 1):
                nr = r + dr
                nc = c + direction
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if self.is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))
        return moves

    # ---------------------------------------------------------------------
    # Legal move filtering (respecting check)
    # ---------------------------------------------------------------------
    def legal_moves(self, board, color):
        """All legal moves for colour (no move leaves own king in check)."""
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self.is_own_piece(piece, color):
                    for (tr, tc), is_capture in self.get_moves(board, r, c, color):
                        new_board = self.apply_move(board,
                                                    (r, c, tr, tc, is_capture),
                                                    color)
                        if not self.is_in_check(new_board, color):
                            moves.append((r, c, tr, tc, is_capture))
        return moves

    def has_any_legal_moves(self, board, color):
        """True if colour has at least one legal move."""
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self.is_own_piece(piece, color):
                    for (tr, tc), is_capture in self.get_moves(board, r, c, color):
                        new_board = self.apply_move(board,
                                                    (r, c, tr, tc, is_capture),
                                                    color)
                        if not self.is_in_check(new_board, color):
                            return True
        return False

    # ---------------------------------------------------------------------
    # Move execution (does not check legality)
    # ---------------------------------------------------------------------
    def apply_move(self, board, move, color):
        """Return a new board after applying the move (promotion handled)."""
        fr, fc, tr, tc, _ = move
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''
        # automatic pawn promotion to rook
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                new_board[tr][tc] = 'R' if color == 'W' else 'r'
        return new_board

    # ---------------------------------------------------------------------
    # Check / stalemate detection
    # ---------------------------------------------------------------------
    def is_in_check(self, board, color):
        """True if the king of given colour is under attack."""
        king = 'K' if color == 'W' else 'k'
        king_pos = None
        for r in range(2):
            for c in range(8):
                if board[r][c] == king:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        if not king_pos:            # should not happen
            return True
        enemy = self.other_color()
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self.is_enemy_piece(piece, color):
                    for (tr, tc), _ in self.get_moves(board, r, c, enemy):
                        if (tr, tc) == king_pos:
                            return True
        return False

    # ---------------------------------------------------------------------
    # Static evaluation (material + colour perspective)
    # ---------------------------------------------------------------------
    def static_eval(self, board):
        """Higher score is better for our colour."""
        white = black = 0
        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if p == '':
                    continue
                val = self.piece_values.get(p.upper(), 0)
                if p.isupper():
                    white += val
                else:
                    black += val
        diff = white - black
        return diff if self.color == 'W' else -diff

    # ---------------------------------------------------------------------
    # Minimax with alpha‑beta pruning
    # ---------------------------------------------------------------------
    def minimax(self, board, depth, alpha, beta, turn):
        """Recursive minimax. turn is the colour to move."""
        moves = self.legal_moves(board, turn)

        # terminal node
        if depth == 0 or not moves:
            if not moves:                     # no legal moves
                if self.is_in_check(board, turn):
                    # checkmate: current player loses
                    big = 10000
                    return -big if turn == self.color else big
                else:
                    # stalemate
                    return 0
            # depth limit reached – use static evaluation
            return self.static_eval(board)

        if turn == self.color:                # maximizing for us
            max_eval = -float('inf')
            for move in moves:
                new_board = self.apply_move(board, move, turn)
                eval_child = self.minimax(new_board, depth - 1,
                                          alpha, beta, self.other_color())
                max_eval = max(max_eval, eval_child)
                alpha = max(alpha, max_eval)
                if beta <= alpha:
                    break
            return max_eval
        else:                                 # minimizing for opponent
            min_eval = float('inf')
            for move in moves:
                new_board = self.apply_move(board, move, turn)
                eval_child = self.minimax(new_board, depth - 1,
                                          alpha, beta, self.other_color())
                min_eval = min(min_eval, eval_child)
                beta = min(beta, min_eval)
                if beta <= alpha:
                    break
            return min_eval

    # ---------------------------------------------------------------------
    # Convert internal move to notation string
    # ---------------------------------------------------------------------
    def move_to_string(self, move, board):
        """Translate (fr,fc,tr,tc,is_capture) into e.g. 'Nb2d1'."""
        fr, fc, tr, tc, is_capture = move
        piece = board[fr][fc].upper()
        from_sq = self.cols[fc] + str(fr + 1)
        to_sq = self.cols[tc] + str(tr + 1)
        cap = 'x' if is_capture else ''
        return f"{piece}{from_sq}{cap}{to_sq}"
