"""
Agent Code: A7-TwoByEightChess
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-14 13:30:59
"""



class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, board, move_history):
        color = self.color
        legal_moves = []
        cols = 'abcdefgh'
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    moves = self._get_piece_moves(board, r, c, color, ignore_check=False)
                    for (to_r, to_c) in moves:
                        from_sq = f"{cols[c]}{r+1}"
                        to_sq = f"{cols[to_c]}{to_r+1}"
                        is_capture = (board[to_r][to_c] != '')
                        move_str = f"{piece}{from_sq}x{to_sq}" if is_capture else f"{piece}{from_sq}{to_sq}"
                        
                        new_board = [row[:] for row in board]
                        new_board[to_r][to_c] = piece
                        new_board[r][c] = ''
                        if piece in 'Pp':
                            if (piece == 'P' and to_c == 7) or (piece == 'p' and to_c == 0):
                                new_board[to_r][to_c] = 'R' if piece == 'P' else 'r'
                        
                        opponent_color = 'B' if color == 'W' else 'W'
                        opponent_in_check = self._is_in_check(new_board, opponent_color)
                        score = 0
                        if opponent_in_check:
                            if not self._has_legal_moves(new_board, opponent_color):
                                score = 1000
                            else:
                                score = 500
                        if is_capture:
                            captured = board[to_r][to_c]
                            cap_type = captured.upper()
                            if cap_type == 'R':
                                score += 50
                            elif cap_type == 'N':
                                score += 30
                            elif cap_type == 'P':
                                score += 10
                        legal_moves.append((move_str, score))
        
        if not legal_moves:
            for r in range(2):
                for c in range(8):
                    piece = board[r][c]
                    if piece and self._is_own_piece(piece, color):
                        moves = self._get_piece_moves(board, r, c, color, ignore_check=True)
                        if moves:
                            to_r, to_c = moves[0]
                            from_sq = f"{cols[c]}{r+1}"
                            to_sq = f"{cols[to_c]}{to_r+1}"
                            is_capture = (board[to_r][to_c] != '')
                            return f"{piece}{from_sq}x{to_sq}" if is_capture else f"{piece}{from_sq}{to_sq}"
            return "Ka1a2"
        
        best_move = None
        best_score = -1
        for move_str, score in legal_moves:
            if score > best_score:
                best_score = score
                best_move = move_str
        return best_move

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _is_own_piece(self, piece, color):
        if color == 'W':
            return piece in ['K', 'N', 'R', 'P']
        else:
            return piece in ['k', 'n', 'r', 'p']

    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        if color == 'W':
            return piece in ['k', 'n', 'r', 'p']
        else:
            return piece in ['K', 'N', 'R', 'P']

    def _is_in_check(self, board, color):
        king_char = 'K' if color == 'W' else 'k'
        king_pos = None
        for r in range(2):
            for c in range(8):
                if board[r][c] == king_char:
                    king_pos = (r, c)
                    break
            if king_pos is not None:
                break
        if king_pos is None:
            return True
        r, c = king_pos
        for r0 in range(2):
            for c0 in range(8):
                piece = board[r0][c0]
                if piece and self._is_enemy_piece(piece, color):
                    if self._piece_attacks_square(board, r0, c0, r, c):
                        return True
        return False

    def _piece_attacks_square(self, board, fr, fc, tr, tc):
        piece = board[fr][fc].upper()
        if piece == 'K':
            return (abs(fr - tr) <= 1 and abs(fc - tc) <= 1) and (fr != tr or fc != tc)
        elif piece == 'N':
            dr = abs(fr - tr)
            dc = abs(fc - tc)
            return (dr == 1 and dc == 2) or (dr == 2 and dc == 1) or (dr == 0 and dc == 2)
        elif piece == 'R':
            if fr == tr and fc == tc:
                return False
            if fr == tr:
                step = 1 if fc < tc else -1
                start = fc + step
                end = tc
                if step > 0:
                    for col in range(start, end, step):
                        if board[fr][col] != '':
                            return False
                else:
                    for col in range(start, end, step):
                        if board[fr][col] != '':
                            return False
                return True
            elif fc == tc:
                return True
            return False
        elif piece == 'P':
            direction = 1 if board[fr][fc] == 'P' else -1
            return (abs(fr - tr) == 1) and (tc == fc + direction)
        return False

    def _has_legal_moves(self, board, color):
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    moves = self._get_piece_moves(board, r, c, color, ignore_check=True)
                    for (to_r, to_c) in moves:
                        if not self._leaves_king_in_check(board, r, c, to_r, to_c, color):
                            return True
        return False

    def _leaves_king_in_check(self, board, fr, fc, to_r, to_c, color):
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        new_board[fr][fc] = ''
        new_board[to_r][to_c] = piece
        if piece in 'Pp':
            if (piece == 'P' and to_c == 7) or (piece == 'p' and to_c == 0):
                new_board[to_r][to_c] = 'R' if piece == 'P' else 'r'
        return self._is_in_check(new_board, color)

    def _get_piece_moves(self, board, r, c, color, ignore_check):
        piece = board[r][c]
        if not piece or not self._is_own_piece(piece, color):
            return []
        piece_type = piece.upper()
        moves = []
        
        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            moves.append((nr, nc))
        elif piece_type == 'N':
            deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                      (-2, -1), (-2, 1), (2, -1), (2, 1),
                      (0, -2), (0, 2)]
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        moves.append((nr, nc))
        elif piece_type == 'R':
            for dc in [-1, 1]:
                nc = c + dc
                while self._in_bounds(r, nc):
                    target = board[r][nc]
                    if target == '':
                        moves.append((r, nc))
                    else:
                        if not self._is_own_piece(target, color):
                            moves.append((r, nc))
                        break
                    nc += dc
            for dr in [-1, 1]:
                nr = r + dr
                if self._in_bounds(nr, c):
                    target = board[nr][c]
                    if not self._is_own_piece(target, color):
                        moves.append((nr, c))
        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            nc = c + direction
            if self._in_bounds(r, nc) and board[r][nc] == '':
                moves.append((r, nc))
            for dr in [-1, 1]:
                nr = r + dr
                nc = c + direction
                if self._in_bounds(nr, nc) and self._is_enemy_piece(board[nr][nc], color):
                    moves.append((nr, nc))
        
        if ignore_check:
            return moves
        
        safe_moves = []
        for (to_r, to_c) in moves:
            if not self._leaves_king_in_check(board, r, c, to_r, to_c, color):
                safe_moves.append((to_r, to_c))
        return safe_moves
