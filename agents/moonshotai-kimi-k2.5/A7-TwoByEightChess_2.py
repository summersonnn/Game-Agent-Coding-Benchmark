"""
Agent Code: A7-TwoByEightChess
Model: moonshotai/kimi-k2.5
Run: 2
Generated: 2026-02-14 13:30:59
"""

import time
import copy

import time
import copy
import random

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.is_white = (color == 'W')
        self.opponent = 'B' if self.is_white else 'W'
        self.time_limit = 0.9  # seconds
        self.start_time = None
        
        # Piece values
        self.values = {'P': 100, 'p': 100, 'N': 320, 'n': 320, 
                      'R': 500, 'r': 500, 'K': 10000, 'k': 10000}
        
        # Position bonuses for Knights (central control is key)
        self.knight_bonus = [
            [0, 5, 10, 20, 20, 10, 5, 0],  # Row 0
            [0, 5, 10, 20, 20, 10, 5, 0]   # Row 1
        ]
        
        # Pawn advancement bonus
        self.pawn_bonus_w = [[0, 10, 20, 30, 40, 50, 60, 70],
                            [0, 10, 20, 30, 40, 50, 60, 70]]
        self.pawn_bonus_b = [[70, 60, 50, 40, 30, 20, 10, 0],
                            [70, 60, 50, 40, 30, 20, 10, 0]]
    
    def make_move(self, board, move_history):
        self.start_time = time.time()
        
        # Opening book: immediate central Knight deployment
        if len(move_history) == 0 and self.is_white:
            # White first move: play Knight to d1 or d2
            # Prefer d1 via b1 for the fork threat
            if board[0][1] == 'N':  # b1
                return "Nb1d1"
            elif board[1][1] == 'N':  # b2
                return "Nb2d2"
        
        # If opponent opened with central Knight, we need to respond carefully
        if len(move_history) == 1 and not self.is_white:
            # Check if White played a central Knight move
            last_move = move_history[0]
            if 'd1' in last_move or 'd2' in last_move:
                # Emergency: our pawns are forked
                # Best defense: advance one pawn to attack the Knight
                # and prepare to save material
                # Move f2 pawn to e2 to attack the Knight
                if board[1][5] == 'p':  # f2
                    # Check if we can play Pf2e2
                    if self._is_valid_move(board, 'p', 1, 5, 1, 4):
                        return "Pf2e2"
                if board[0][5] == 'p':  # f1
                    if self._is_valid_move(board, 'p', 0, 5, 0, 4):
                        return "Pf1e1"
        
        # Iterative deepening search
        best_move = None
        depth = 1
        max_depth = 6
        
        # Get all valid moves
        moves = self._get_all_moves(board, self.is_white)
        
        if not moves:
            return "Ka2a2"  # Should not happen in legal position
        
        # If only one move, play it immediately
        if len(moves) == 1:
            return self._move_to_notation(board, moves[0])
        
        # Order moves for better alpha-beta pruning
        moves = self._order_moves(board, moves)
        
        try:
            while depth <= max_depth:
                current_best = None
                current_score = -float('inf')
                alpha = -float('inf')
                beta = float('inf')
                
                for move in moves:
                    if time.time() - self.start_time > self.time_limit:
                        raise TimeoutError
                    
                    new_board = self._apply_move(board, move)
                    score = -self._negamax(new_board, depth-1, -beta, -alpha, not self.is_white)
                    
                    if score > current_score:
                        current_score = score
                        current_best = move
                    
                    if score > alpha:
                        alpha = score
                
                if current_best:
                    best_move = current_best
                
                depth += 1
                
        except TimeoutError:
            pass
        
        if best_move is None:
            best_move = moves[0]
            
        return self._move_to_notation(board, best_move)
    
    def _is_valid_move(self, board, piece, fr, fc, tr, tc):
        """Quick check for pawn moves in opening book"""
        if not (0 <= tr < 2 and 0 <= tc < 8):
            return False
        # Simplified check for opening book
        return board[tr][tc] == ''
    
    def _get_all_moves(self, board, is_white):
        """Generate all legal moves for side"""
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece == '':
                    continue
                if is_white and piece.islower():
                    continue
                if not is_white and piece.isupper():
                    continue
                
                piece_type = piece.upper()
                
                if piece_type == 'K':
                    moves.extend(self._get_king_moves(board, r, c, is_white))
                elif piece_type == 'N':
                    moves.extend(self._get_knight_moves(board, r, c, is_white))
                elif piece_type == 'R':
                    moves.extend(self._get_rook_moves(board, r, c, is_white))
                elif piece_type == 'P':
                    moves.extend(self._get_pawn_moves(board, r, c, is_white))
        return moves
    
    def _get_king_moves(self, board, r, c, is_white):
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '' or (is_white and target.islower()) or (not is_white and target.isupper()):
                        # Check if move leaves king in check
                        if not self._is_check_after_move(board, r, c, nr, nc, is_white):
                            moves.append((r, c, nr, nc, target != ''))
        return moves
    
    def _get_knight_moves(self, board, r, c, is_white):
        moves = []
        # L-shape + linear 2
        deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), 
                 (1, -2), (1, 2), (2, -1), (2, 1),
                 (0, -2), (0, 2)]
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 2 and 0 <= nc < 8:
                target = board[nr][nc]
                if target == '' or (is_white and target.islower()) or (not is_white and target.isupper()):
                    if not self._is_check_after_move(board, r, c, nr, nc, is_white):
                        moves.append((r, c, nr, nc, target != ''))
        return moves
    
    def _get_rook_moves(self, board, r, c, is_white):
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 2 and 0 <= nc < 8:
                target = board[nr][nc]
                if target == '':
                    if not self._is_check_after_move(board, r, c, nr, nc, is_white):
                        moves.append((r, c, nr, nc, False))
                elif (is_white and target.islower()) or (not is_white and target.isupper()):
                    if not self._is_check_after_move(board, r, c, nr, nc, is_white):
                        moves.append((r, c, nr, nc, True))
                    break
                else:
                    break
                nr += dr
                nc += dc
        return moves
    
    def _get_pawn_moves(self, board, r, c, is_white):
        moves = []
        direction = 1 if is_white else -1
        
        # Forward move
        nc = c + direction
        if 0 <= nc < 8 and board[r][nc] == '':
            # Check promotion
            is_promotion = (is_white and nc == 7) or (not is_white and nc == 0)
            if not self._is_check_after_move(board, r, c, r, nc, is_white, promotion=is_promotion):
                moves.append((r, c, r, nc, False, is_promotion))
        
        # Captures
        for dr in [-1, 1]:
            nr = r + dr
            nc = c + direction
            if 0 <= nr < 2 and 0 <= nc < 8:
                target = board[nr][nc]
                if target != '' and ((is_white and target.islower()) or (not is_white and target.isupper())):
                    is_promotion = (is_white and nc == 7) or (not is_white and nc == 0)
                    if not self._is_check_after_move(board, r, c, nr, nc, is_white, promotion=is_promotion):
                        moves.append((r, c, nr, nc, True, is_promotion))
        return moves
    
    def _is_check_after_move(self, board, fr, fc, tr, tc, is_white, promotion=False):
        """Check if king is in check after making move"""
        # Copy board
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''
        
        # Handle promotion
        if promotion:
            new_board[tr][tc] = 'R' if is_white else 'r'
        elif piece.upper() == 'P':
            # Auto-promotion check
            if (is_white and tc == 7) or (not is_white and tc == 0):
                new_board[tr][tc] = 'R' if is_white else 'r'
        
        # Find king
        king_char = 'K' if is_white else 'k'
        king_pos = None
        for r in range(2):
            for c in range(8):
                if new_board[r][c] == king_char:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return True
        
        # Check if any enemy piece attacks king
        enemy_is_white = not is_white
        for r in range(2):
            for c in range(8):
                p = new_board[r][c]
                if p == '':
                    continue
                if enemy_is_white and p.islower():
                    continue
                if not enemy_is_white and p.isupper():
                    continue
                
                if self._attacks_square(new_board, r, c, king_pos[0], king_pos[1]):
                    return True
        return False
    
    def _attacks_square(self, board, r, c, tr, tc):
        """Check if piece at r,c attacks target square tr,tc"""
        piece = board[r][c].upper()
        
        if piece == 'K':
            return abs(r - tr) <= 1 and abs(c - tc) <= 1 and (r != tr or c != tc)
        
        elif piece == 'N':
            dr, dc = abs(r - tr), abs(c - tc)
            # L-shape or linear 2
            return (dr == 2 and dc == 1) or (dr == 1 and dc == 2) or (dr == 0 and dc == 2)
        
        elif piece == 'R':
            if r == tr:  # Horizontal
                step = 1 if tc > c else -1
                for cc in range(c + step, tc, step):
                    if board[r][cc] != '':
                        return False
                return True
            elif c == tc:  # Vertical
                step = 1 if tr > r else -1
                for rr in range(r + step, tr, step):
                    if board[rr][c] != '':
                        return False
                return True
            return False
        
        elif piece == 'P':
            color = 1 if board[r][c].isupper() else -1
            # Pawn captures diagonally
            if tc == c + color and abs(tr - r) == 1:
                return True
            return False
        
        return False
    
    def _apply_move(self, board, move):
        """Apply move and return new board state"""
        new_board = [row[:] for row in board]
        if len(move) == 5:  # with promotion flag
            fr, fc, tr, tc, prom = move
        else:
            fr, fc, tr, tc, is_cap = move
            prom = False
        
        piece = new_board[fr][fc]
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''
        
        # Promotion
        if piece.upper() == 'P':
            if (piece.isupper() and tc == 7) or (piece.islower() and tc == 0):
                new_board[tr][tc] = 'R' if piece.isupper() else 'r'
        
        return new_board
    
    def _order_moves(self, board, moves):
        """Order moves for better pruning: captures first, then central moves"""
        def score_move(m):
            fr, fc, tr, tc, is_cap = m[:5]
            score = 0
            if is_cap:
                victim = board[tr][tc]
                attacker = board[fr][fc]
                score += 10 * self.values.get(victim, 0) - self.values.get(attacker, 0)
            # Favor central columns (d, e = 3, 4)
            if tc in [3, 4]:
                score += 50
            return -score  # Negative because we sort ascending and want high scores first
        
        return sorted(moves, key=score_move)
    
    def _negamax(self, board, depth, alpha, beta, is_white):
        """Negamax search with alpha-beta pruning"""
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError
        
        # Terminal check
        moves = self._get_all_moves(board, is_white)
        
        # Check for checkmate or stalemate
        if not moves:
            if self._is_in_check(board, is_white):
                return -50000  # Checkmate
            else:
                return 0  # Stalemate
        
        if depth == 0:
            return self._evaluate(board)
        
        max_score = -float('inf')
        for move in moves:
            new_board = self._apply_move(board, move)
            score = -self._negamax(new_board, depth-1, -beta, -alpha, not is_white)
            
            if score > max_score:
                max_score = score
            
            if score > alpha:
                alpha = score
            
            if alpha >= beta:
                break
        
        return max_score
    
    def _is_in_check(self, board, is_white):
        """Check if king is in check"""
        king_char = 'K' if is_white else 'k'
        king_pos = None
        for r in range(2):
            for c in range(8):
                if board[r][c] == king_char:
                    king_pos = (r, c)
                    break
        
        if not king_pos:
            return True
        
        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if p == '':
                    continue
                if is_white and p.isupper():
                    continue
                if not is_white and p.islower():
                    continue
                
                if self._attacks_square(board, r, c, king_pos[0], king_pos[1]):
                    return True
        return False
    
    def _evaluate(self, board):
        """Evaluate board position"""
        score = 0
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece == '':
                    continue
                
                val = self.values.get(piece, 0)
                
                if piece.isupper():  # White
                    score += val
                    if piece == 'N':
                        score += self.knight_bonus[r][c]
                    elif piece == 'P':
                        score += self.pawn_bonus_w[r][c]
                else:  # Black
                    score -= val
                    if piece == 'n':
                        score -= self.knight_bonus[r][c]
                    elif piece == 'p':
                        score -= self.pawn_bonus_b[r][c]
        
        return score if self.is_white else -score
    
    def _move_to_notation(self, board, move):
        """Convert move tuple to notation string"""
        if len(move) == 6:
            fr, fc, tr, tc, is_cap, prom = move
        else:
            fr, fc, tr, tc, is_cap = move
            prom = False
        
        piece = board[fr][fc].upper()
        from_sq = chr(ord('a') + fc) + str(fr + 1)
        to_sq = chr(ord('a') + tc) + str(tr + 1)
        
        if is_cap:
            return f"{piece}{from_sq}x{to_sq}"
        else:
            return f"{piece}{from_sq}{to_sq}"
