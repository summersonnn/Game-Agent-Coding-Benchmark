"""
Agent Code: A7-TwoByEightChess
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-14 13:30:59
"""

import copy

import copy
import random

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.COLS = 'abcdefgh'

    def _pos_to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"

    def _notation_to_pos(self, notation):
        if len(notation) != 2:
            return None
        col_char = notation[0].lower()
        if col_char not in self.COLS:
            return None
        try:
            row = int(notation[1]) - 1
        except ValueError:
            return None
        col = self.COLS.index(col_char)
        if not (0 <= row < 2 and 0 <= col < 8):
            return None
        return (row, col)

    def _is_white_piece(self, piece):
        return piece in 'KNRP'

    def _is_black_piece(self, piece):
        return piece in 'knrp'

    def _is_own_piece(self, piece, color):
        return self._is_white_piece(piece) if color == 'W' else self._is_black_piece(piece)

    def _is_enemy_piece(self, piece, color):
        return bool(piece) and not self._is_own_piece(piece, color)

    def _get_piece_type(self, piece):
        return piece.upper() if piece else ''

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _get_valid_moves_for_piece(self, board, row, col, color, ignore_check=False):
        piece = board[row][col]
        if not piece or not self._is_own_piece(piece, color):
            return []
        piece_type = self._get_piece_type(piece)
        moves = []
        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            moves.append(((nr, nc), is_capture))
        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))
        elif piece_type == 'R':
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        moves.append(((nr, nc), False))
                        nr += dr
                        nc += dc
                        continue
                    if self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))
                    break
        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            nc = col + direction
            if self._in_bounds(row, nc) and board[row][nc] == '':
                moves.append(((row, nc), False))
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc) and self._is_enemy_piece(board[nr][nc], color):
                    moves.append(((nr, nc), True))
        if ignore_check:
            return moves
        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe(board, (row, col), to_pos, color):
                valid_moves.append((to_pos, is_capture))
        return valid_moves

    def _is_move_safe(self, board, from_pos, to_pos, color):
        sim_board = copy.deepcopy(board)
        fr, fc = from_pos
        tr, tc = to_pos
        piece = sim_board[fr][fc]
        sim_board[tr][tc] = piece
        sim_board[fr][fc] = ''
        if self._get_piece_type(piece) == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                sim_board[tr][tc] = 'R' if color == 'W' else 'r'
        return not self._is_in_check(sim_board, color)

    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if not king_pos:
            return True
        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                if self._is_own_piece(board[r][c], enemy_color):
                    attacks = self._get_valid_moves_for_piece(board, r, c, enemy_color, ignore_check=True)
                    for to_pos, _ in attacks:
                        if to_pos == king_pos:
                            return True
        return False

    def _has_legal_moves(self, board, color):
        for r in range(2):
            for c in range(8):
                if self._is_own_piece(board[r][c], color):
                    if self._get_valid_moves_for_piece(board, r, c, color):
                        return True
        return False

    def _is_insufficient_material(self, board):
        for r in range(2):
            for c in range(8):
                if board[r][c] and board[r][c].upper() != 'K':
                    return False
        return True

    def _apply_move(self, board, from_pos, to_pos, color):
        new_board = copy.deepcopy(board)
        fr, fc = from_pos
        tr, tc = to_pos
        piece = new_board[fr][fc]
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                new_board[tr][tc] = 'R' if color == 'W' else 'r'
        return new_board

    def _evaluate(self, board):
        values = {'P': 1, 'N': 3, 'R': 5, 'K': 0}
        my_material = 0
        opp_material = 0
        pawn_advance = 0
        opp_color = 'B' if self.color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if not p:
                    continue
                pt = p.upper()
                v = values[pt]
                if self._is_own_piece(p, self.color):
                    my_material += v
                    if pt == 'P':
                        if self.color == 'W':
                            pawn_advance += c
                        else:
                            pawn_advance += (7 - c)
                else:
                    opp_material += v
                    if pt == 'P':
                        if opp_color == 'W':
                            pawn_advance -= c
                        else:
                            pawn_advance -= (7 - c)
        score = my_material - opp_material + pawn_advance * 0.1
        return score

    def _minimax(self, board, depth, alpha, beta, is_max):
        opp_color = 'B' if self.color == 'W' else 'W'
        current_color = self.color if is_max else opp_color
        if self._is_insufficient_material(board):
            return 0, None
        in_check = self._is_in_check(board, current_color)
        has_moves = self._has_legal_moves(board, current_color)
        if not has_moves:
            if in_check:
                return -10000 if is_max else 10000, None
            else:
                return 0, None
        if depth == 0:
            return self._evaluate(board), None
        best_score = -float('inf') if is_max else float('inf')
        best_move = None
        move_list = []
        for r in range(2):
            for c in range(8):
                if self._is_own_piece(board[r][c], current_color):
                    from_pos = (r, c)
                    for to_pos, is_cap in self._get_valid_moves_for_piece(board, r, c, current_color):
                        new_board = self._apply_move(board, from_pos, to_pos, current_color)
                        piece_type = board[r][c].upper()
                        from_sq = self._pos_to_notation(r, c)
                        to_sq = self._pos_to_notation(to_pos[0], to_pos[1])
                        move_str = f"{piece_type}{from_sq}{'x' if is_cap else ''}{to_sq}"
                        move_list.append((move_str, new_board))
        move_list.sort(key=lambda x: 'x' in x[0], reverse=True)
        if is_max:
            for move_str, new_board in move_list:
                score, _ = self._minimax(new_board, depth - 1, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_move = move_str
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break
            return best_score, best_move
        else:
            for move_str, new_board in move_list:
                score, _ = self._minimax(new_board, depth - 1, alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_move = move_str
                beta = min(beta, best_score)
                if alpha >= beta:
                    break
            return best_score, best_move

    def get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                if self._is_own_piece(board[r][c], color):
                    piece_type = self._get_piece_type(board[r][c])
                    from_sq = self._pos_to_notation(r, c)
                    for to_pos, is_capture in self._get_valid_moves_for_piece(board, r, c, color):
                        to_sq = self._pos_to_notation(to_pos[0], to_pos[1])
                        if is_capture:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        moves.append(move_str)
        return moves

    def make_move(self, board, move_history):
        current_board = copy.deepcopy(board)
        depth = 4
        _, best_move = self._minimax(current_board, depth, -float('inf'), float('inf'), True)
        if best_move is None:
            moves = self.get_all_valid_moves(board, self.color)
            if moves:
                return random.choice(moves)
            return ""
        return best_move
