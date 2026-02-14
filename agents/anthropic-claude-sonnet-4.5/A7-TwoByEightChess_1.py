"""
Agent Code: A7-TwoByEightChess
Model: anthropic-claude-sonnet-4.5
Run: 1
Generated: 2026-02-14 13:16:13
"""

import random

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.opponent_color = 'B' if color == 'W' else 'W'
        self.piece_values = {'K': 0, 'N': 3, 'R': 5, 'P': 1, 'k': 0, 'n': -3, 'r': -5, 'p': -1, '': 0}
    
    def make_move(self, board, move_history):
        valid_moves = self._get_all_valid_moves(board, self.color)
        if not valid_moves:
            return "Ka2b2"
        
        best_move = None
        best_score = float('-inf')
        
        for move in valid_moves:
            new_board = self._apply_move(board, move)
            score = self._minimax(new_board, 3, float('-inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move else random.choice(valid_moves)
    
    def _minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0:
            return self._evaluate(board)
        
        color = self.color if maximizing else self.opponent_color
        moves = self._get_all_valid_moves(board, color)
        
        if not moves:
            if self._is_in_check(board, color):
                return float('-inf') if maximizing else float('inf')
            return 0
        
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                new_board = self._apply_move(board, move)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = self._apply_move(board, move)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def _evaluate(self, board):
        score = sum(self.piece_values.get(piece, 0) for row in board for piece in row)
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    if 3 <= c <= 4:
                        score += 0.1 if piece.isupper() else -0.1
                    if piece == 'P':
                        score += c * 0.15
                    elif piece == 'p':
                        score -= (7 - c) * 0.15
        
        return score
    
    def _get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own(piece, color):
                    moves.extend(self._get_piece_moves(board, r, c, color))
        return moves
    
    def _get_piece_moves(self, board, row, col, color):
        piece = board[row][col]
        piece_type = piece.upper()
        moves = []
        
        for to_row, to_col, is_cap in self._get_candidates(board, row, col, piece_type, color):
            if self._is_safe(board, (row, col), (to_row, to_col), color):
                from_sq = f"{'abcdefgh'[col]}{row + 1}"
                to_sq = f"{'abcdefgh'[to_col]}{to_row + 1}"
                moves.append(f"{piece_type}{from_sq}{'x' if is_cap else ''}{to_sq}")
        
        return moves
    
    def _get_candidates(self, board, row, col, piece_type, color):
        candidates = []
        
        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if not self._is_own(target, color):
                            candidates.append((nr, nc, self._is_enemy(target, color)))
        
        elif piece_type == 'N':
            for dr, dc in [(-1,-2),(-1,2),(1,-2),(1,2),(-2,-1),(-2,1),(2,-1),(2,1),(0,-2),(0,2)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not self._is_own(target, color):
                        candidates.append((nr, nc, self._is_enemy(target, color)))
        
        elif piece_type == 'R':
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = row + dr, col + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '':
                        candidates.append((nr, nc, False))
                    elif self._is_enemy(target, color):
                        candidates.append((nr, nc, True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        
        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            nc = col + direction
            if 0 <= nc < 8 and board[row][nc] == '':
                candidates.append((row, nc, False))
            
            for dr in [-1, 1]:
                nr, nc = row + dr, col + direction
                if 0 <= nr < 2 and 0 <= nc < 8 and self._is_enemy(board[nr][nc], color):
                    candidates.append((nr, nc, True))
        
        return candidates
    
    def _is_safe(self, board, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        
        new_board = [row[:] for row in board]
        moving = new_board[fr][fc]
        
        if moving.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving = 'R' if color == 'W' else 'r'
        
        new_board[tr][tc] = moving
        new_board[fr][fc] = ''
        
        return not self._is_in_check(new_board, color)
    
    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if not king_pos:
            return True
        
        enemy = 'B' if color == 'W' else 'W'
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own(piece, enemy):
                    if self._can_attack(board, r, c, king_pos, piece.upper()):
                        return True
        return False
    
    def _can_attack(self, board, fr, fc, target, piece_type):
        tr, tc = target
        
        if piece_type == 'K':
            return abs(fr - tr) <= 1 and abs(fc - tc) <= 1 and (fr != tr or fc != tc)
        
        elif piece_type == 'N':
            dr, dc = abs(fr - tr), abs(fc - tc)
            return (dr == 1 and dc == 2) or (dr == 2 and dc == 1) or (dr == 0 and dc == 2)
        
        elif piece_type == 'R':
            if fr == tr:
                step = 1 if tc > fc else -1
                for c in range(fc + step, tc, step):
                    if board[fr][c]:
                        return False
                return True
            elif fc == tc:
                step = 1 if tr > fr else -1
                for r in range(fr + step, tr, step):
                    if board[r][fc]:
                        return False
                return True
            return False
        
        elif piece_type == 'P':
            color = 'W' if board[fr][fc].isupper() else 'B'
            direction = 1 if color == 'W' else -1
            return fc + direction == tc and abs(fr - tr) == 1
        
        return False
    
    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None
    
    def _apply_move(self, board, move_str):
        new_board = [row[:] for row in board]
        parsed = self._parse(move_str)
        if not parsed:
            return new_board
        
        _, (fr, fc), (tr, tc), _ = parsed
        moving = new_board[fr][fc]
        
        if moving.upper() == 'P':
            color = 'W' if moving.isupper() else 'B'
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving = 'R' if color == 'W' else 'r'
        
        new_board[tr][tc] = moving
        new_board[fr][fc] = ''
        return new_board
    
    def _parse(self, move_str):
        if not isinstance(move_str, str) or len(move_str) < 5:
            return None
        
        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R', 'P'):
            return None
        
        if 'x' in move_str.lower():
            idx = move_str.lower().index('x')
            from_n, to_n = move_str[1:idx], move_str[idx+1:]
            is_cap = True
        else:
            from_n, to_n = move_str[1:3], move_str[3:5]
            is_cap = False
        
        from_pos = self._to_pos(from_n)
        to_pos = self._to_pos(to_n)
        
        return (piece, from_pos, to_pos, is_cap) if from_pos and to_pos else None
    
    def _to_pos(self, notation):
        if len(notation) != 2 or notation[0] not in 'abcdefgh':
            return None
        try:
            row = int(notation[1]) - 1
            col = 'abcdefgh'.index(notation[0])
            return (row, col) if 0 <= row < 2 and 0 <= col < 8 else None
        except ValueError:
            return None
    
    def _is_own(self, piece, color):
        return piece in ('K','N','R','P') if color == 'W' else piece in ('k','n','r','p')
    
    def _is_enemy(self, piece, color):
        return piece != '' and not self._is_own(piece, color)