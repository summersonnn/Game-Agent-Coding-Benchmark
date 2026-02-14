"""
Agent Code: A7-TwoByEightChess
Model: anthropic/claude-haiku-4.5
Run: 1
Generated: 2026-02-14 13:17:43
"""



class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.cols = 'abcdefgh'
    
    def make_move(self, board, move_history):
        valid_moves = self._get_all_valid_moves(board, self.color)
        
        if not valid_moves:
            return "Ka1a1"
        
        best_move = None
        best_score = float('-inf')
        
        for move in valid_moves:
            new_board = self._apply_move(board, move)
            score = self._minimax(new_board, 3, float('-inf'), float('inf'), False, self.color)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move else valid_moves[0]
    
    def _get_all_valid_moves(self, board, color):
        moves = []
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not self._is_own_piece(piece, color):
                    continue
                
                piece_type = piece.upper()
                from_sq = self._pos_to_notation(r, c)
                destinations = self._get_destinations(board, r, c, color)
                
                for to_r, to_c, is_capture in destinations:
                    test_board = self._apply_move_internally(board, r, c, to_r, to_c)
                    if self._is_in_check(test_board, color):
                        continue
                    
                    to_sq = self._pos_to_notation(to_r, to_c)
                    if is_capture:
                        move = f"{piece_type}{from_sq}x{to_sq}"
                    else:
                        move = f"{piece_type}{from_sq}{to_sq}"
                    moves.append((move, is_capture))
        
        moves.sort(key=lambda x: (not x[1],))
        return [move for move, _ in moves]
    
    def _get_destinations(self, board, r, c, color):
        piece = board[r][c]
        piece_type = piece.upper()
        destinations = []
        
        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            destinations.append((nr, nc, is_capture))
        
        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        destinations.append((nr, nc, is_capture))
        
        elif piece_type == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        destinations.append((nr, nc, False))
                    elif self._is_enemy_piece(target, color):
                        destinations.append((nr, nc, True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        
        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            nc = c + direction
            if self._in_bounds(r, nc) and board[r][nc] == '':
                destinations.append((r, nc, False))
            for dr in [-1, 1]:
                nr = r + dr
                nc = c + direction
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        destinations.append((nr, nc, True))
        
        return destinations
    
    def _apply_move_internally(self, board, fr, fc, tr, tc):
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''
        
        if piece and piece.upper() == 'P':
            if (piece.isupper() and tc == 7) or (piece.islower() and tc == 0):
                new_board[tr][tc] = 'R' if piece.isupper() else 'r'
        
        return new_board
    
    def _apply_move(self, board, move_str):
        if 'x' in move_str.lower():
            idx = move_str.lower().index('x')
            from_notation = move_str[1:idx]
            to_notation = move_str[idx+1:]
        else:
            from_notation = move_str[1:3]
            to_notation = move_str[3:5]
        
        from_pos = self._notation_to_pos(from_notation)
        to_pos = self._notation_to_pos(to_notation)
        
        if not from_pos or not to_pos:
            return board
        
        fr, fc = from_pos
        tr, tc = to_pos
        return self._apply_move_internally(board, fr, fc, tr, tc)
    
    def _minimax(self, board, depth, alpha, beta, is_maximizing, my_color):
        if depth == 0:
            return self._evaluate_board(board, my_color)
        
        opponent_color = 'B' if my_color == 'W' else 'W'
        current_color = my_color if is_maximizing else opponent_color
        
        valid_moves = self._get_all_valid_moves(board, current_color)
        
        if not valid_moves:
            if self._is_in_check(board, current_color):
                return float('inf') if not is_maximizing else float('-inf')
            else:
                return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in valid_moves:
                new_board = self._apply_move(board, move)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, False, my_color)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid_moves:
                new_board = self._apply_move(board, move)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True, my_color)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def _evaluate_board(self, board, my_color):
        my_material = 0
        opp_material = 0
        
        piece_values = {'P': 1, 'N': 3, 'R': 5, 'K': 100}
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                
                value = piece_values.get(piece.upper(), 0)
                is_mine = (my_color == 'W' and piece.isupper()) or (my_color == 'B' and piece.islower())
                
                if is_mine:
                    my_material += value
                    if piece.upper() == 'P':
                        if my_color == 'W':
                            my_material += c * 0.1
                        else:
                            my_material += (7 - c) * 0.1
                else:
                    opp_material += value
        
        return my_material - opp_material
    
    def _is_in_check(self, board, color):
        king_char = 'K' if color == 'W' else 'k'
        king_pos = None
        
        for r in range(2):
            for c in range(8):
                if board[r][c] == king_char:
                    king_pos = (r, c)
                    break
        
        if not king_pos:
            return True
        
        opponent_color = 'B' if color == 'W' else 'W'
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not self._is_own_piece(piece, opponent_color):
                    continue
                
                destinations = self._get_destinations(board, r, c, opponent_color)
                for dest_r, dest_c, _ in destinations:
                    if (dest_r, dest_c) == king_pos:
                        return True
        
        return False
    
    def _is_own_piece(self, piece, color):
        if not piece:
            return False
        return (color == 'W' and piece.isupper()) or (color == 'B' and piece.islower())
    
    def _is_enemy_piece(self, piece, color):
        if not piece:
            return False
        return not self._is_own_piece(piece, color)
    
    def _in_bounds(self, r, c):
        return 0 <= r < 2 and 0 <= c < 8
    
    def _pos_to_notation(self, r, c):
        return f"{self.cols[c]}{r + 1}"
    
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
        if not self._in_bounds(row, col):
            return None
        return (row, col)
