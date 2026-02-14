"""
Agent Code: A7-TwoByEightChess
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-14 13:30:59
"""



import random

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color  # 'W' or 'B'
        self.piece_vals = {'K': 1000, 'R': 5, 'N': 3, 'P': 1}
    
    def _get_piece_color(self, piece):
        if piece == '':
            return None
        return 'W' if piece.isupper() else 'B'
    
    def _is_own_piece(self, piece, color):
        return piece != '' and self._get_piece_color(piece) == color
    
    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None
    
    def _is_square_attacked(self, board, square, attacker_color):
        kr, kc = square
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece == '' or self._get_piece_color(piece) != attacker_color:
                    continue
                piece_type = piece.upper()
                if piece_type == 'K':
                    if abs(r - kr) <= 1 and abs(c - kc) <= 1 and (r != kr or c != kc):
                        return True
                elif piece_type == 'N':
                    dr = abs(r - kr)
                    dc = abs(c - kc)
                    if (dr == 1 and dc == 2) or (dr == 2 and dc == 1):
                        return True
                    if r == kr and abs(c - kc) == 2:
                        return True
                elif piece_type == 'R':
                    if r == kr and c != kc:
                        step = 1 if c < kc else -1
                        for col in range(c + step, kc, step):
                            if board[r][col] != '':
                                break
                        else:
                            return True
                    elif c == kc and r != kr:
                        step = 1 if r < kr else -1
                        for row in range(r + step, kr, step):
                            if board[row][c] != '':
                                break
                        else:
                            return True
                elif piece_type == 'P':
                    if attacker_color == 'W':
                        if (kr == r - 1 and kc == c + 1) or (kr == r + 1 and kc == c + 1):
                            return True
                    else:
                        if (kr == r - 1 and kc == c - 1) or (kr == r + 1 and kc == c - 1):
                            return True
        return False

    def _generate_pseudo_moves(self, board, r, c, color):
        piece = board[r][c]
        if piece == '':
            return []
        piece_type = piece.upper()
        moves = []
        
        if piece_type == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            moves.append((nr, nc))
        elif piece_type == 'N':
            deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                     (-2, -1), (-2, 1), (2, -1), (2, 1),
                     (0, -2), (0, 2)]
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        moves.append((nr, nc))
        elif piece_type == 'R':
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '':
                        moves.append((nr, nc))
                    elif not self._is_own_piece(target, color):
                        moves.append((nr, nc))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        elif piece_type == 'P':
            dc = 1 if color == 'W' else -1
            nc = c + dc
            if 0 <= nc < 8 and board[r][nc] == '':
                moves.append((r, nc))
            for dr in (-1, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target != '' and not self._is_own_piece(target, color):
                        moves.append((nr, nc))
        return moves

    def _simulate_move(self, board, fr, fc, tr, tc):
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        new_board[fr][fc] = ''
        new_board[tr][tc] = piece
        
        if piece.upper() == 'P':
            if piece == 'P' and tc == 7:
                new_board[tr][tc] = 'R'
            elif piece == 'p' and tc == 0:
                new_board[tr][tc] = 'r'
        return new_board

    def _evaluate_board(self, board):
        agent_score = 0
        opponent_score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece == '':
                    continue
                val = self.piece_vals.get(piece.upper(), 0)
                if self._is_own_piece(piece, self.color):
                    agent_score += val
                else:
                    opponent_score += val
        return agent_score - opponent_score

    def _pos_to_notation(self, r, c):
        col_char = chr(ord('a') + c)
        return f"{col_char}{r + 1}"
    
    def make_move(self, board, move_history):
        legal_moves = []
        opponent_color = 'B' if self.color == 'W' else 'W'
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not self._is_own_piece(piece, self.color):
                    continue
                piece_type = piece.upper()
                from_sq = self._pos_to_notation(r, c)
                pseudo_moves = self._generate_pseudo_moves(board, r, c, self.color)
                
                for tr, tc in pseudo_moves:
                    is_capture = board[tr][tc] != ''
                    new_board = self._simulate_move(board, r, c, tr, tc)
                    king_pos = self._find_king(new_board, self.color)
                    if king_pos is None:
                        continue
                    if not self._is_square_attacked(new_board, king_pos, opponent_color):
                        to_sq = self._pos_to_notation(tr, tc)
                        move_str = f"{piece_type}{from_sq}x{to_sq}" if is_capture else f"{piece_type}{from_sq}{to_sq}"
                        legal_moves.append((move_str, new_board))
        
        if not legal_moves:
            for r in range(2):
                for c in range(8):
                    piece = board[r][c]
                    if piece and self._is_own_piece(piece, self.color):
                        ps_moves = self._generate_pseudo_moves(board, r, c, self.color)
                        for tr, tc in ps_moves:
                            from_sq = self._pos_to_notation(r, c)
                            to_sq = self._pos_to_notation(tr, tc)
                            return f"{piece.upper()}{from_sq}{to_sq}"
            return "Ka1a2"
        
        best_move = None
        best_score = -float('inf')
        for move_str, new_board in legal_moves:
            score = self._evaluate_board(new_board)
            if score > best_score:
                best_score = score
                best_move = move_str
        
        return best_move if best_move else random.choice([m[0] for m in legal_moves])
