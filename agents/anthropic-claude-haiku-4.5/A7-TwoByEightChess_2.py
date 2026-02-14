"""
Agent Code: A7-TwoByEightChess
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-14 14:32:41
"""



class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.COLS = 'abcdefgh'
    
    def _is_white_piece(self, piece):
        return piece in ('K', 'N', 'R', 'P')
    
    def _is_black_piece(self, piece):
        return piece in ('k', 'n', 'r', 'p')
    
    def _is_own_piece(self, piece, color):
        return self._is_white_piece(piece) if color == 'W' else self._is_black_piece(piece)
    
    def _is_enemy_piece(self, piece, color):
        return piece != '' and not self._is_own_piece(piece, color)
    
    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8
    
    def _pos_to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"
    
    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None
    
    def _get_piece_type(self, piece):
        return piece.upper() if piece else ''
    
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
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))
        
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
            nc = col + direction
            if self._in_bounds(row, nc) and board[row][nc] == '':
                moves.append(((row, nc), False))
            for dr in [-1, 1]:
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
        original_from = board[fr][fc]
        original_to = board[tr][tc]
        
        moving_piece = original_from
        if moving_piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'
        board[tr][tc] = moving_piece
        board[fr][fc] = ''
        
        in_check = self._is_in_check(board, color)
        
        board[fr][fc] = original_from
        board[tr][tc] = original_to
        
        return not in_check
    
    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True
        
        enemy_color = 'B' if color == 'W' else 'W'
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    enemy_moves = self._get_valid_moves_for_piece(board, r, c, enemy_color, ignore_check=True)
                    for to_pos, _ in enemy_moves:
                        if to_pos == king_pos:
                            return True
        return False
    
    def _has_legal_moves(self, board, color):
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    if self._get_valid_moves_for_piece(board, r, c, color):
                        return True
        return False
    
    def _get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_type = self._get_piece_type(piece)
                    from_sq = self._pos_to_notation(r, c)
                    for to_pos, is_capture in self._get_valid_moves_for_piece(board, r, c, color):
                        to_sq = self._pos_to_notation(to_pos[0], to_pos[1])
                        if is_capture:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        moves.append((move_str, (r, c), to_pos))
        return moves
    
    def _make_move_on_board(self, board, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        piece = board[fr][fc]
        board[tr][tc] = piece
        board[fr][fc] = ''
        
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                board[tr][tc] = 'R' if color == 'W' else 'r'
    
    def _evaluate(self, board):
        values = {'P': 1, 'N': 3, 'R': 5, 'K': 0}
        score = 0
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    val = values.get(piece.upper(), 0)
                    if self._is_white_piece(piece):
                        score += val
                        if piece == 'P':
                            score += c * 0.05
                    else:
                        score -= val
                        if piece == 'p':
                            score -= (7 - c) * 0.05
        
        return score
    
    def _search(self, board, depth, alpha, beta, is_white_turn):
        color = 'W' if is_white_turn else 'B'
        
        in_check = self._is_in_check(board, color)
        has_moves = self._has_legal_moves(board, color)
        
        if not has_moves:
            if in_check:
                return -1000 if is_white_turn else 1000
            else:
                return 0
        
        if depth == 0:
            return self._evaluate(board)
        
        moves = self._get_all_valid_moves(board, color)
        
        if is_white_turn:
            max_eval = -float('inf')
            for move_str, from_pos, to_pos in moves:
                board_copy = [row[:] for row in board]
                self._make_move_on_board(board_copy, from_pos, to_pos, 'W')
                eval_val = self._search(board_copy, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move_str, from_pos, to_pos in moves:
                board_copy = [row[:] for row in board]
                self._make_move_on_board(board_copy, from_pos, to_pos, 'B')
                eval_val = self._search(board_copy, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval
    
    def make_move(self, board, move_history):
        is_white = len(move_history) % 2 == 0
        color = 'W' if is_white else 'B'
        
        moves = self._get_all_valid_moves(board, color)
        
        if not moves:
            return None
        
        depth = 5
        best_move = moves[0][0]
        
        if is_white:
            best_eval = -float('inf')
            for move_str, from_pos, to_pos in moves:
                board_copy = [row[:] for row in board]
                self._make_move_on_board(board_copy, from_pos, to_pos, 'W')
                eval_val = self._search(board_copy, depth - 1, -float('inf'), float('inf'), False)
                if eval_val > best_eval:
                    best_eval = eval_val
                    best_move = move_str
        else:
            best_eval = float('inf')
            for move_str, from_pos, to_pos in moves:
                board_copy = [row[:] for row in board]
                self._make_move_on_board(board_copy, from_pos, to_pos, 'B')
                eval_val = self._search(board_copy, depth - 1, -float('inf'), float('inf'), True)
                if eval_val < best_eval:
                    best_eval = eval_val
                    best_move = move_str
        
        return best_move
