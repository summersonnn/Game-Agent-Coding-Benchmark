"""
Agent Code: A7-TwoByEightChess
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 1
Generated: 2026-02-14 14:28:53
"""

import copy

import copy

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color  # 'W' or 'B'
        self.cols = 'abcdefgh'
    
    def _pos_to_notation(self, row, col):
        return f"{self.cols[col]}{row+1}"
    
    def _notation_to_pos(self, notation):
        if len(notation) != 2:
            return None
        col_char = notation[0].lower()
        if col_char not in self.cols:
            return None
        try:
            row = int(notation[1]) - 1
        except ValueError:
            return None
        col = self.cols.index(col_char)
        if not (0 <= row < 2 and 0 <= col < 8):
            return None
        return (row, col)
    
    def _is_own_piece(self, piece, color):
        if not piece:
            return False
        if color == 'W':
            return piece in 'KNRP'
        else:
            return piece in 'knrp'
    
    def _is_enemy_piece(self, piece, color):
        if not piece:
            return False
        return not self._is_own_piece(piece, color)
    
    def _get_piece_type(self, piece):
        return piece.upper() if piece else ''
    
    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None
    
    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True
        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    moves = self._get_pseudo_moves(board, r, c, enemy_color)
                    for (tr, tc, _) in moves:
                        if (tr, tc) == king_pos:
                            return True
        return False
    
    def _get_pseudo_moves(self, board, row, col, color):
        piece = board[row][col]
        if not piece:
            return []
        piece_type = self._get_piece_type(piece)
        moves = []
        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            moves.append((nr, nc, is_capture))
        elif piece_type == 'N':
            deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                      (-2, -1), (-2, 1), (2, -1), (2, 1),
                      (0, -2), (0, 2)]
            for dr, dc in deltas:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append((nr, nc, is_capture))
        elif piece_type == 'R':
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '':
                        moves.append((nr, nc, False))
                    elif self._is_enemy_piece(target, color):
                        moves.append((nr, nc, True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            # Forward move
            nc = col + direction
            if 0 <= nc < 8:
                if board[row][nc] == '':
                    moves.append((row, nc, False))
            # Diagonal captures
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append((nr, nc, True))
        return moves
    
    def _is_move_safe(self, board, from_row, from_col, to_row, to_col, color):
        temp_board = copy.deepcopy(board)
        piece = temp_board[from_row][from_col]
        # Handle pawn promotion
        if piece.upper() == 'P':
            if (color == 'W' and to_col == 7) or (color == 'B' and to_col == 0):
                piece = 'R' if color == 'W' else 'r'
        temp_board[to_row][to_col] = piece
        temp_board[from_row][from_col] = ''
        return not self._is_in_check(temp_board, color)
    
    def _generate_legal_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    pseudo_moves = self._get_pseudo_moves(board, r, c, color)
                    for (tr, tc, is_capture) in pseudo_moves:
                        if self._is_move_safe(board, r, c, tr, tc, color):
                            from_sq = self._pos_to_notation(r, c)
                            to_sq = self._pos_to_notation(tr, tc)
                            piece_type = self._get_piece_type(piece)
                            if is_capture:
                                move_str = f"{piece_type}{from_sq}x{to_sq}"
                            else:
                                move_str = f"{piece_type}{from_sq}{to_sq}"
                            moves.append(move_str)
        return moves
    
    def _simulate_move(self, board, move_str, color):
        new_board = copy.deepcopy(board)
        parsed = self._parse_move(move_str)
        if parsed is None:
            return new_board
        _, from_pos, to_pos, _ = parsed
        fr, fc = from_pos
        tr, tc = to_pos
        piece = new_board[fr][fc]
        # Handle pawn promotion
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                piece = 'R' if color == 'W' else 'r'
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''
        return new_board
    
    def _parse_move(self, move_str):
        if not isinstance(move_str, str) or len(move_str) < 5:
            return None
        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R', 'P'):
            return None
        if 'x' in move_str:
            parts = move_str.split('x')
            if len(parts) != 2:
                return None
            from_notation = parts[0][1:]
            to_notation = parts[1]
            is_capture = True
        else:
            from_notation = move_str[1:3]
            to_notation = move_str[3:5]
            is_capture = False
        from_pos = self._notation_to_pos(from_notation)
        to_pos = self._notation_to_pos(to_notation)
        if from_pos is None or to_pos is None:
            return None
        return (piece, from_pos, to_pos, is_capture)
    
    def _evaluate(self, board, color):
        opp_color = 'B' if color == 'W' else 'W'
        material = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                if self._is_own_piece(piece, color):
                    if piece.upper() == 'R': material += 5
                    elif piece.upper() == 'N': material += 3
                    elif piece.upper() == 'P': material += 1
                elif self._is_own_piece(piece, opp_color):
                    if piece.upper() == 'R': material -= 5
                    elif piece.upper() == 'N': material -= 3
                    elif piece.upper() == 'P': material -= 1
        positional = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                if self._is_own_piece(piece, color):
                    if piece.upper() == 'P':
                        if color == 'W':
                            positional += (c - 2) * 0.1
                        else:
                            positional += (2 - c) * 0.1
                    elif piece.upper() == 'N':
                        if c in (3, 4):
                            positional += 0.2
                    elif piece.upper() == 'R':
                        has_pawn = False
                        for rr in range(2):
                            p = board[rr][c]
                            if p and p.upper() == 'P':
                                has_pawn = True
                                break
                        if not has_pawn:
                            positional += 0.5
                elif self._is_own_piece(piece, opp_color):
                    if piece.upper() == 'P':
                        if opp_color == 'W':
                            positional -= (c - 2) * 0.1
                        else:
                            positional -= (2 - c) * 0.1
                    elif piece.upper() == 'N':
                        if c in (3, 4):
                            positional -= 0.2
                    elif piece.upper() == 'R':
                        has_pawn = False
                        for rr in range(2):
                            p = board[rr][c]
                            if p and p.upper() == 'P':
                                has_pawn = True
                                break
                        if not has_pawn:
                            positional -= 0.5
        check_penalty = 0.0
        if self._is_in_check(board, color):
            check_penalty = -1.0
        return material + positional + check_penalty
    
    def make_move(self, board, move_history):
        our_color = self.color
        opp_color = 'B' if our_color == 'W' else 'W'
        moves = self._generate_legal_moves(board, our_color)
        if not moves:
            return "00000"
        best_move = None
        best_value = -float('inf')
        for move_str in moves:
            new_board = self._simulate_move(board, move_str, our_color)
            if self._is_in_check(new_board, opp_color):
                opp_moves = self._generate_legal_moves(new_board, opp_color)
                if not opp_moves:
                    return move_str
            value = self._evaluate(new_board, our_color)
            if value > best_value:
                best_value = value
                best_move = move_str
        return best_move
