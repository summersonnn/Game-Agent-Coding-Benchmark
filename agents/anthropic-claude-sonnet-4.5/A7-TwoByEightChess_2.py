"""
Agent Code: A7-TwoByEightChess
Model: anthropic-claude-sonnet-4.5
Run: 2
Generated: 2026-02-14 13:16:13
"""

import random
from copy import deepcopy


class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.COLS = 'abcdefgh'
        
    def make_move(self, board, move_history):
        valid_moves = self._get_all_valid_moves(board, self.color)
        if not valid_moves:
            return random.choice(self._get_all_valid_moves(board, self.color)) if self._get_all_valid_moves(board, self.color) else "Ka2b2"
        
        best_move = self._find_best_move(board, move_history)
        return best_move if best_move else valid_moves[0]
    
    def _find_best_move(self, board, move_history):
        valid_moves = self._get_all_valid_moves(board, self.color)
        if not valid_moves:
            return None
        
        best_score = float('-inf')
        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        
        for move in valid_moves:
            new_board = self._apply_move(deepcopy(board), move, self.color)
            score = -self._minimax(new_board, 3, -beta, -alpha, self._opponent_color())
            
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
        
        return best_move if best_move else valid_moves[0]
    
    def _minimax(self, board, depth, alpha, beta, color):
        if depth == 0:
            return self._evaluate_board(board)
        
        valid_moves = self._get_all_valid_moves(board, color)
        if not valid_moves:
            if self._is_in_check(board, color):
                return -10000
            return 0
        
        max_score = float('-inf')
        for move in valid_moves:
            new_board = self._apply_move(deepcopy(board), move, color)
            score = -self._minimax(new_board, depth - 1, -beta, -alpha, self._opponent_color(color))
            max_score = max(max_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        return max_score
    
    def _evaluate_board(self, board):
        piece_values = {'K': 0, 'N': 3, 'R': 5, 'P': 1, 'k': 0, 'n': -3, 'r': -5, 'p': -1, '': 0}
        score = 0
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    base_value = piece_values.get(piece, 0)
                    if self.color == 'W':
                        score += base_value
                    else:
                        score -= base_value
                    
                    if piece.upper() == 'P':
                        if self._is_white_piece(piece):
                            score += c * 0.1 if self.color == 'W' else -c * 0.1
                        else:
                            score += (7 - c) * 0.1 if self.color == 'B' else -(7 - c) * 0.1
        
        return score
    
    def _get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_moves = self._get_piece_moves(board, r, c, color)
                    moves.extend(piece_moves)
        return moves
    
    def _get_piece_moves(self, board, row, col, color):
        piece = board[row][col]
        piece_type = piece.upper()
        moves = []
        from_sq = self._pos_to_notation(row, col)
        
        destinations = self._get_valid_destinations(board, row, col, color)
        
        for (tr, tc), is_capture in destinations:
            to_sq = self._pos_to_notation(tr, tc)
            if is_capture:
                move_str = f"{piece_type}{from_sq}x{to_sq}"
            else:
                move_str = f"{piece_type}{from_sq}{to_sq}"
            moves.append(move_str)
        
        return moves
    
    def _get_valid_destinations(self, board, row, col, color):
        piece = board[row][col]
        piece_type = piece.upper()
        dests = []
        
        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            if self._is_move_safe(board, (row, col), (nr, nc), color):
                                dests.append(((nr, nc), self._is_enemy_piece(target, color)))
        
        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        if self._is_move_safe(board, (row, col), (nr, nc), color):
                            dests.append(((nr, nc), self._is_enemy_piece(target, color)))
        
        elif piece_type == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        if self._is_move_safe(board, (row, col), (nr, nc), color):
                            dests.append(((nr, nc), False))
                    elif self._is_enemy_piece(target, color):
                        if self._is_move_safe(board, (row, col), (nr, nc), color):
                            dests.append(((nr, nc), True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        
        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            nc = col + direction
            if self._in_bounds(row, nc) and board[row][nc] == '':
                if self._is_move_safe(board, (row, col), (row, nc), color):
                    dests.append(((row, nc), False))
            
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        if self._is_move_safe(board, (row, col), (nr, nc), color):
                            dests.append(((nr, nc), True))
        
        return dests
    
    def _is_move_safe(self, board, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        
        temp_board = deepcopy(board)
        moving_piece = temp_board[fr][fc]
        
        if moving_piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'
        
        temp_board[tr][tc] = moving_piece
        temp_board[fr][fc] = ''
        
        return not self._is_in_check(temp_board, color)
    
    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if not king_pos:
            return True
        
        enemy_color = 'B' if color == 'W' else 'W'
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    if self._can_attack(board, r, c, king_pos, enemy_color):
                        return True
        return False
    
    def _can_attack(self, board, row, col, target_pos, color):
        piece = board[row][col]
        piece_type = piece.upper()
        tr, tc = target_pos
        
        if piece_type == 'K':
            return abs(row - tr) <= 1 and abs(col - tc) <= 1
        
        elif piece_type == 'N':
            dr, dc = abs(row - tr), abs(col - tc)
            return (dr == 1 and dc == 2) or (dr == 2 and dc == 1) or (dr == 0 and dc == 2)
        
        elif piece_type == 'R':
            if row == tr:
                step = 1 if tc > col else -1
                for c in range(col + step, tc, step):
                    if board[row][c]:
                        return False
                return True
            elif col == tc:
                step = 1 if tr > row else -1
                for r in range(row + step, tr, step):
                    if board[r][col]:
                        return False
                return True
        
        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            return tc == col + direction and abs(tr - row) == 1
        
        return False
    
    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None
    
    def _apply_move(self, board, move_str, color):
        parsed = self._parse_move(move_str)
        if not parsed:
            return board
        
        _, from_pos, to_pos, _ = parsed
        fr, fc = from_pos
        tr, tc = to_pos
        
        board[tr][tc] = board[fr][fc]
        board[fr][fc] = ''
        
        piece = board[tr][tc]
        if piece.upper() == 'P':
            if (self._is_white_piece(piece) and tc == 7) or (self._is_black_piece(piece) and tc == 0):
                board[tr][tc] = 'R' if self._is_white_piece(piece) else 'r'
        
        return board
    
    def _parse_move(self, move_str):
        if len(move_str) < 5:
            return None
        
        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R', 'P'):
            return None
        
        if 'x' in move_str.lower():
            idx = move_str.lower().index('x')
            from_notation = move_str[1:idx]
            to_notation = move_str[idx+1:]
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
        if not self._in_bounds(row, col):
            return None
        return (row, col)
    
    def _pos_to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"
    
    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8
    
    def _is_white_piece(self, piece):
        return piece in ('K', 'N', 'R', 'P')
    
    def _is_black_piece(self, piece):
        return piece in ('k', 'n', 'r', 'p')
    
    def _is_own_piece(self, piece, color):
        if color == 'W':
            return self._is_white_piece(piece)
        return self._is_black_piece(piece)
    
    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self._is_own_piece(piece, color)
    
    def _opponent_color(self, color=None):
        if color is None:
            color = self.color
        return 'B' if color == 'W' else 'W'