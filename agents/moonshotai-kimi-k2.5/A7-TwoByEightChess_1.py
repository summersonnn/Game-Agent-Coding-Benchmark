"""
Agent Code: A7-TwoByEightChess
Model: moonshotai/kimi-k2.5
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
        self.is_white = (color == 'W')
        self.opponent = 'B' if color == 'W' else 'W'
        self.cols = 'abcdefgh'
        self.max_depth = 4
        
    def make_move(self, board, move_history):
        # Convert to internal format
        current_board = [row[:] for row in board]
        
        # Get legal moves
        moves = self.get_legal_moves(current_board, self.color)
        
        if not moves:
            return None
            
        # Use alpha-beta search with randomization for variety
        random.shuffle(moves)
        best_move = moves[0]
        best_score = -float('inf')
        
        for move in moves:
            new_board = self.apply_move(current_board, move)
            score = -self.alpha_beta(new_board, self.max_depth - 1, -float('inf'), float('inf'), False)
            
            # Prioritize checkmates and captures
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
    
    def alpha_beta(self, board, depth, alpha, beta, maximizing):
        color = self.color if maximizing else self.opponent
        
        # Check terminal conditions
        moves = self.get_legal_moves(board, color)
        
        if not moves:
            if self.is_in_check(board, color):
                return -10000 + (self.max_depth - depth)  # Checkmate, prefer sooner
            else:
                return 0  # Stalemate
        
        if depth == 0:
            return self.evaluate(board)
        
        if maximizing:
            value = -float('inf')
            for move in moves:
                new_board = self.apply_move(board, move)
                value = max(value, self.alpha_beta(new_board, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for move in moves:
                new_board = self.apply_move(board, move)
                value = min(value, self.alpha_beta(new_board, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value
    
    def evaluate(self, board):
        score = 0
        white_king_pos = None
        black_king_pos = None
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                    
                val = self.piece_value(piece)
                
                if self.is_white_piece(piece):
                    score += val
                    if piece == 'P':
                        score += c * 15  # Advance bonus
                        if c >= 6:
                            score += 200  # Near promotion
                    elif piece == 'K':
                        white_king_pos = (r, c)
                    elif piece == 'R':
                        # Rook on open files
                        if c >= 4:
                            score += 50
                else:
                    score -= val
                    if piece == 'p':
                        score -= (7 - c) * 15
                        if c <= 1:
                            score -= 200
                    elif piece == 'k':
                        black_king_pos = (r, c)
                    elif piece == 'r':
                        if c <= 3:
                            score -= 50
        
        # Mobility bonus
        if self.is_white:
            w_moves = len(self.get_legal_moves(board, 'W'))
            b_moves = len(self.get_legal_moves(board, 'B'))
            score += (w_moves - b_moves) * 5
            return score
        else:
            w_moves = len(self.get_legal_moves(board, 'W'))
            b_moves = len(self.get_legal_moves(board, 'B'))
            score -= (w_moves - b_moves) * 5
            return -score
    
    def piece_value(self, piece):
        p = piece.upper()
        if p == 'P': return 100
        if p == 'N': return 320
        if p == 'R': return 500
        if p == 'K': return 0  # King's value handled separately
        return 0
    
    def is_white_piece(self, piece):
        return piece in ('K', 'N', 'R', 'P')
    
    def is_black_piece(self, piece):
        return piece in ('k', 'n', 'r', 'p')
    
    def is_own_piece(self, piece, color):
        if color == 'W':
            return self.is_white_piece(piece)
        return self.is_black_piece(piece)
    
    def is_enemy_piece(self, piece, color):
        if not piece:
            return False
        return not self.is_own_piece(piece, color)
    
    def get_legal_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self.is_own_piece(piece, color):
                    moves.extend(self._piece_moves(board, r, c, piece, color))
        return moves
    
    def _piece_moves(self, board, r, c, piece, color):
        moves = []
        ptype = piece.upper()
        
        if ptype == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if not self.is_own_piece(target, color):
                            if not self._is_check_after_move(board, r, c, nr, nc, color):
                                moves.append(self._format_move(piece, r, c, nr, nc, target != ''))
        
        elif ptype == 'N':
            deltas = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1), (0,-2), (0,2)]
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not self.is_own_piece(target, color):
                        if not self._is_check_after_move(board, r, c, nr, nc, color):
                            moves.append(self._format_move(piece, r, c, nr, nc, target != ''))
        
        elif ptype == 'R':
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '':
                        if not self._is_check_after_move(board, r, c, nr, nc, color):
                            moves.append(self._format_move(piece, r, c, nr, nc, False))
                    elif self.is_enemy_piece(target, color):
                        if not self._is_check_after_move(board, r, c, nr, nc, color):
                            moves.append(self._format_move(piece, r, c, nr, nc, True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        
        elif ptype == 'P':
            direction = 1 if color == 'W' else -1
            # Forward move
            nc = c + direction
            if 0 <= nc < 8 and board[r][nc] == '':
                promoted = (color == 'W' and nc == 7) or (color == 'B' and nc == 0)
                if not self._is_check_after_move(board, r, c, r, nc, color, promoted):
                    moves.append(self._format_move(piece, r, c, r, nc, False, promoted))
            
            # Captures
            for dr in [-1, 1]:
                nr = r + dr
                nc = c + direction
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if self.is_enemy_piece(target, color):
                        promoted = (color == 'W' and nc == 7) or (color == 'B' and nc == 0)
                        if not self._is_check_after_move(board, r, c, nr, nc, color, promoted):
                            moves.append(self._format_move(piece, r, c, nr, nc, True, promoted))
        
        return moves
    
    def _is_check_after_move(self, board, fr, fc, tr, tc, color, promotion=False):
        # Fast check by simulating only the necessary parts
        piece = board[fr][fc]
        
        # Temporarily modify board
        original_target = board[tr][tc]
        board[tr][tc] = 'R' if (promotion and color == 'W') else ('r' if (promotion and color == 'B') else piece)
        board[fr][fc] = ''
        
        in_check = self.is_in_check(board, color)
        
        # Restore board
        board[fr][fc] = piece
        board[tr][tc] = original_target
        
        return in_check
    
    def is_in_check(self, board, color):
        king = 'K' if color == 'W' else 'k'
        king_pos = None
        
        for r in range(2):
            for c in range(8):
                if board[r][c] == king:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return True
            
        kr, kc = king_pos
        enemy = 'B' if color == 'W' else 'W'
        
        # Check enemy attacks
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self.is_own_piece(piece, enemy):
                    if self._can_attack_square(board, r, c, piece, kr, kc):
                        return True
        return False
    
    def _can_attack_square(self, board, r, c, piece, tr, tc):
        ptype = piece.upper()
        color = 'W' if self.is_white_piece(piece) else 'B'
        
        if ptype == 'K':
            return abs(r - tr) <= 1 and abs(c - tc) <= 1
        
        elif ptype == 'N':
            dr, dc = abs(r - tr), abs(c - tc)
            if dr == 0 and dc == 2:
                return True
            return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)
        
        elif ptype == 'R':
            if r == tr:
                step = 1 if tc > c else -1
                for col in range(c + step, tc, step):
                    if board[r][col] != '':
                        return False
                return True
            elif c == tc:
                if abs(r - tr) == 1:
                    return True
            return False
        
        elif ptype == 'P':
            direction = 1 if color == 'W' else -1
            return (tr == r - 1 or tr == r + 1) and tc == c + direction
        
        return False
    
    def _format_move(self, piece, fr, fc, tr, tc, is_capture, promotion=False):
        from_sq = self.cols[fc] + str(fr + 1)
        to_sq = self.cols[tc] + str(tr + 1)
        ptype = piece.upper()
        
        if is_capture:
            return f"{ptype}{from_sq}x{to_sq}"
        return f"{ptype}{from_sq}{to_sq}"
    
    def apply_move(self, board, move_str):
        new_board = [row[:] for row in board]
        
        # Parse
        piece = move_str[0]
        is_capture = 'x' in move_str
        
        if is_capture:
            idx = move_str.index('x')
            from_sq = move_str[1:idx]
            to_sq = move_str[idx+1:idx+3]
        else:
            from_sq = move_str[1:3]
            to_sq = move_str[3:5]
        
        fc = self.cols.index(from_sq[0])
        fr = int(from_sq[1]) - 1
        tc = self.cols.index(to_sq[0])
        tr = int(to_sq[1]) - 1
        
        moving = new_board[fr][fc]
        new_board[tr][tc] = moving
        new_board[fr][fc] = ''
        
        # Promotion
        if moving.upper() == 'P':
            if (moving == 'P' and tc == 7) or (moving == 'p' and tc == 0):
                new_board[tr][tc] = 'R' if moving == 'P' else 'r'
        
        return new_board
