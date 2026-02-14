"""
Agent Code: A7-TwoByEightChess
Model: openai/gpt-5.2-codex
Run: 1
Generated: 2026-02-14 13:30:59
"""



class TwoByEightChessAgent:
    COLS = 'abcdefgh'
    MATE_VALUE = 10000
    PIECE_VALUES = {'K': 0, 'R': 5, 'N': 3, 'P': 1}

    def __init__(self, name, color):
        self.name = name
        self.color = color  # 'W' or 'B'

    def make_move(self, board, move_history):
        color = self.color
        moves = self._get_all_valid_moves(board, color)
        if not moves:
            # Fallback (should not occur if game state is checked)
            return "Ka2b2"

        opponent = self._opponent(color)

        # Check for immediate checkmate
        for move in moves:
            new_board = self._apply_move(board, move)
            if not self._get_all_valid_moves(new_board, opponent) and self._is_in_check(new_board, opponent):
                return self._move_to_notation(move)

        depth = self._choose_depth(board)
        cache = {}

        best_val = -float('inf')
        best_move = moves[0]

        alpha = -float('inf')
        beta = float('inf')

        for move in self._order_moves(board, color, moves):
            new_board = self._apply_move(board, move)
            val = -self._negamax(new_board, opponent, depth - 1, -beta, -alpha, cache)
            if val > best_val:
                best_val = val
                best_move = move
            if val > alpha:
                alpha = val

        return self._move_to_notation(best_move)

    # ----------------- Helper Methods ----------------- #

    def _opponent(self, color):
        return 'B' if color == 'W' else 'W'

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _pos_to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"

    def _is_own_piece(self, piece, color):
        if not piece:
            return False
        return piece.isupper() if color == 'W' else piece.islower()

    def _is_enemy_piece(self, piece, color):
        if not piece:
            return False
        return not self._is_own_piece(piece, color)

    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _get_valid_moves_for_piece(self, board, row, col, ignore_check=False):
        piece = board[row][col]
        if not piece:
            return []

        color = 'W' if piece.isupper() else 'B'
        piece_type = piece.upper()
        moves = []

        if piece_type == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            moves.append(((nr, nc), self._is_enemy_piece(target, color)))

        elif piece_type == 'N':
            deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                      (-2, -1), (-2, 1), (2, -1), (2, 1),
                      (0, -2), (0, 2)]
            for dr, dc in deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        moves.append(((nr, nc), self._is_enemy_piece(target, color)))

        elif piece_type == 'R':
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

        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            # forward move
            nc = col + direction
            if self._in_bounds(row, nc) and board[row][nc] == '':
                moves.append(((row, nc), False))
            # diagonal captures
            for dr in (-1, 1):
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))

        if ignore_check:
            return moves

        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe(board, (row, col), to_pos, color):
                valid_moves.append((to_pos, is_capture))
        return valid_moves

    def _is_move_safe(self, board, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        original_piece = board[fr][fc]
        captured_piece = board[tr][tc]

        board[fr][fc] = ''
        moving_piece = original_piece

        if moving_piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'

        board[tr][tc] = moving_piece
        in_check = self._is_in_check(board, color)

        # Undo move
        board[fr][fc] = original_piece
        board[tr][tc] = captured_piece

        return not in_check

    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True

        enemy = self._opponent(color)
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy):
                    moves = self._get_valid_moves_for_piece(board, r, c, ignore_check=True)
                    for to_pos, _ in moves:
                        if to_pos == king_pos:
                            return True
        return False

    def _get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_type = piece.upper()
                    for to_pos, is_capture in self._get_valid_moves_for_piece(board, r, c):
                        tr, tc = to_pos
                        moves.append((r, c, tr, tc, piece_type, is_capture))
        return moves

    def _apply_move(self, board, move):
        fr, fc, tr, tc, _, _ = move
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        new_board[fr][fc] = ''

        color = 'W' if piece.isupper() else 'B'
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                piece = 'R' if color == 'W' else 'r'

        new_board[tr][tc] = piece
        return new_board

    def _piece_value(self, piece):
        if not piece:
            return 0
        return self.PIECE_VALUES.get(piece.upper(), 0)

    def _evaluate(self, board, color):
        score = 0.0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    val = self.PIECE_VALUES[piece.upper()]
                    if piece.isupper() == (color == 'W'):
                        score += val
                        if piece.upper() == 'P':
                            score += 0.05 * (c if piece.isupper() else 7 - c)
                    else:
                        score -= val
                        if piece.upper() == 'P':
                            score -= 0.05 * (c if piece.isupper() else 7 - c)

        opp = self._opponent(color)
        if self._is_in_check(board, opp):
            score += 0.3
        if self._is_in_check(board, color):
            score -= 0.3
        return score

    def _negamax(self, board, color, depth, alpha, beta, cache):
        key = (self._board_key(board), color, depth)
        if key in cache:
            return cache[key]

        moves = self._get_all_valid_moves(board, color)
        if not moves:
            if self._is_in_check(board, color):
                val = -self.MATE_VALUE + depth
            else:
                val = 0
            cache[key] = val
            return val

        if depth == 0:
            val = self._evaluate(board, color)
            cache[key] = val
            return val

        best = -float('inf')
        opp = self._opponent(color)

        for move in self._order_moves(board, color, moves):
            new_board = self._apply_move(board, move)
            val = -self._negamax(new_board, opp, depth - 1, -beta, -alpha, cache)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        cache[key] = best
        return best

    def _board_key(self, board):
        return tuple(tuple(row) for row in board)

    def _choose_depth(self, board):
        pieces = sum(1 for row in board for p in row if p)
        if pieces <= 4:
            return 5
        elif pieces <= 6:
            return 4
        else:
            return 3

    def _order_moves(self, board, color, moves):
        def score(move):
            fr, fc, tr, tc, _, is_capture = move
            s = 0
            if is_capture:
                s += 10 * self._piece_value(board[tr][tc])
                s -= self._piece_value(board[fr][fc])
            piece = board[fr][fc]
            if piece.upper() == 'P':
                if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                    s += 9  # promotion bonus
            return s

        return sorted(moves, key=score, reverse=True)

    def _move_to_notation(self, move):
        fr, fc, tr, tc, piece_type, is_capture = move
        from_sq = self._pos_to_notation(fr, fc)
        to_sq = self._pos_to_notation(tr, tc)
        if is_capture:
            return f"{piece_type}{from_sq}x{to_sq}"
        else:
            return f"{piece_type}{from_sq}{to_sq}"
