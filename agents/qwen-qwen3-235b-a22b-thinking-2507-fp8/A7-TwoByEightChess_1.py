"""
Agent Code: A7-TwoByEightChess
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-14 13:30:59
"""



class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, board, move_history):
        color = self.color
        our_moves = self._get_valid_moves_structured(board, color)
        if not our_moves:
            return "Ka1a2"
        
        opponent_color = 'B' if color == 'W' else 'W'
        
        for move in our_moves:
            new_board1 = self._apply_move_structured(board, move)
            if self._is_in_check(new_board1, opponent_color) and not self._has_legal_moves(new_board1, opponent_color):
                return self._move_structured_to_string(move, board, color)
        
        safe_moves = []
        for move in our_moves:
            new_board1 = self._apply_move_structured(board, move)
            opp_moves = self._get_valid_moves_structured(new_board1, opponent_color)
            is_safe = True
            for opp_move in opp_moves:
                new_board2 = self._apply_move_structured(new_board1, opp_move)
                if self._is_in_check(new_board2, color) and not self._has_legal_moves(new_board2, color):
                    is_safe = False
                    break
            if is_safe:
                safe_moves.append(move)
        
        if safe_moves:
            best_move = None
            best_score = -1
            for move in safe_moves:
                fr, fc, tr, tc, is_capture = move
                score = 0
                if is_capture:
                    captured_piece = board[tr][tc]
                    score = self._get_piece_value(captured_piece)
                if score > best_score:
                    best_score = score
                    best_move = move
            return self._move_structured_to_string(best_move, board, color)
        
        best_move = None
        best_score = -1
        for move in our_moves:
            fr, fc, tr, tc, is_capture = move
            score = 0
            if is_capture:
                captured_piece = board[tr][tc]
                score = self._get_piece_value(captured_piece)
            if score > best_score:
                best_score = score
                best_move = move
        if best_move is not None:
            return self._move_structured_to_string(best_move, board, color)
        
        return self._move_structured_to_string(our_moves[0], board, color)

    def _get_piece_value(self, piece):
        if piece in ['R', 'r']:
            return 5
        if piece in ['N', 'n']:
            return 3
        if piece in ['P', 'p']:
            return 1
        return 0

    def _has_legal_moves(self, board, color):
        return len(self._get_valid_moves_structured(board, color)) > 0

    def _apply_move_structured(self, board, move):
        fr, fc, tr, tc, is_capture = move
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        if piece == 'P' and tc == 7:
            piece = 'R'
        elif piece == 'p' and tc == 0:
            piece = 'r'
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''
        return new_board

    def _move_structured_to_string(self, move, board, color):
        fr, fc, tr, tc, is_capture = move
        piece_char = board[fr][fc]
        piece_type = piece_char.upper()
        from_sq = f"{chr(ord('a') + fc)}{fr + 1}"
        to_sq = f"{chr(ord('a') + tc)}{tr + 1}"
        if is_capture:
            return f"{piece_type}{from_sq}x{to_sq}"
        else:
            return f"{piece_type}{from_sq}{to_sq}"

    def _is_in_check(self, board, color):
        king_char = 'K' if color == 'W' else 'k'
        king_pos = None
        for r in range(2):
            for c in range(8):
                if board[r][c] == king_char:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        if king_pos is None:
            return True
        kr, kc = king_pos
        
        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                if enemy_color == 'W' and not piece.isupper():
                    continue
                if enemy_color == 'B' and not piece.islower():
                    continue
                piece_type = piece.upper()
                
                if piece_type == 'K':
                    if abs(r - kr) <= 1 and abs(c - kc) <= 1 and (r != kr or c != kc):
                        return True
                elif piece_type == 'N':
                    dr = abs(r - kr)
                    dc = abs(c - kc)
                    if (dr == 1 and dc == 2) or (dr == 2 and dc == 1) or (dr == 0 and dc == 2):
                        return True
                elif piece_type == 'R':
                    if r == kr:
                        step = 1 if c < kc else -1
                        col = c + step
                        while col != kc:
                            if board[r][col] != '':
                                break
                            col += step
                        else:
                            return True
                    if c == kc:
                        if r != kr:
                            return True
                elif piece_type == 'P':
                    if enemy_color == 'W':
                        if (kr == r - 1 or kr == r + 1) and kc == c + 1:
                            return True
                    else:
                        if (kr == r - 1 or kr == r + 1) and kc == c - 1:
                            return True
        return False

    def _get_valid_moves_structured(self, board, color):
        raw_moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                if color == 'W' and not piece.isupper():
                    continue
                if color == 'B' and not piece.islower():
                    continue
                piece_type = piece.upper()
                
                if piece_type == 'K':
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 2 and 0 <= nc < 8:
                                target = board[nr][nc]
                                is_capture = (target != '')
                                if not target or (color == 'W' and target.islower()) or (color == 'B' and target.isupper()):
                                    raw_moves.append((r, c, nr, nc, is_capture))
                elif piece_type == 'N':
                    l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                                (-2, -1), (-2, 1), (2, -1), (2, 1)]
                    linear_deltas = [(0, -2), (0, 2)]
                    for dr, dc in l_deltas + linear_deltas:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 2 and 0 <= nc < 8:
                            target = board[nr][nc]
                            is_capture = (target != '')
                            if not target or (color == 'W' and target.islower()) or (color == 'B' and target.isupper()):
                                raw_moves.append((r, c, nr, nc, is_capture))
                elif piece_type == 'R':
                    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        while 0 <= nr < 2 and 0 <= nc < 8:
                            target = board[nr][nc]
                            is_capture = (target != '')
                            if not target:
                                raw_moves.append((r, c, nr, nc, False))
                            else:
                                if (color == 'W' and target.islower()) or (color == 'B' and target.isupper()):
                                    raw_moves.append((r, c, nr, nc, True))
                                break
                            nr += dr
                            nc += dc
                elif piece_type == 'P':
                    direction = 1 if color == 'W' else -1
                    nc = c + direction
                    if 0 <= nc < 8 and board[r][nc] == '':
                        raw_moves.append((r, c, r, nc, False))
                    for dr in [-1, 1]:
                        nr = r + dr
                        nc = c + direction
                        if 0 <= nr < 2 and 0 <= nc < 8:
                            target = board[nr][nc]
                            if target and ((color == 'W' and target.islower()) or (color == 'B' and target.isupper())):
                                raw_moves.append((r, c, nr, nc, True))
        
        valid_moves = []
        for move in raw_moves:
            fr, fc, tr, tc, is_capture = move
            new_board = [row[:] for row in board]
            p = new_board[fr][fc]
            if p == 'P' and tc == 7:
                p = 'R'
            elif p == 'p' and tc == 0:
                p = 'r'
            new_board[tr][tc] = p
            new_board[fr][fc] = ''
            if not self._is_in_check(new_board, color):
                valid_moves.append(move)
        return valid_moves
