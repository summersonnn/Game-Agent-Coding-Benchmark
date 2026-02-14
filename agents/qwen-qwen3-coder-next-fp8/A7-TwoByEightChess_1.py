"""
Agent Code: A7-TwoByEightChess
Model: qwen/qwen3-coder-next@preset/fp8
Run: 1
Generated: 2026-02-14 14:14:44
"""



import random

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, board, move_history):
        # Convert board to internal representation for easier handling
        # board[0] is row 1, board[1] is row 2
        
        # Generate all valid moves for current player
        moves = self._get_valid_moves(board, self.color)
        
        if not moves:
            # No legal moves - will be handled by engine (stalemate or checkmate)
            return ""
        
        # Simple evaluation: prioritize captures, then central control, then check
        # Sort moves by priority
        scored_moves = []
        for move in moves:
            score = self._evaluate_move(move, board)
            scored_moves.append((score, move))
        
        # Sort by score descending
        scored_moves.sort(key=lambda x: -x[0])
        
        # Pick the best move (with some randomness to avoid identical games)
        best_score = scored_moves[0][0]
        best_moves = [m for s, m in scored_moves if s == best_score]
        
        return random.choice(best_moves)

    def _get_valid_moves(self, board, color):
        """Generate all valid moves for the current player."""
        moves = []
        
        # Helper to check bounds
        def in_bounds(r, c):
            return 0 <= r < 2 and 0 <= c < 8
        
        # Helper to identify piece type
        def get_piece_type(piece):
            return piece.upper() if piece else ''
        
        # Helper to check if own piece
        def is_own_piece(piece):
            if color == 'W':
                return piece in ('K', 'N', 'R', 'P')
            else:
                return piece in ('k', 'n', 'r', 'p')
        
        # Helper to check if enemy piece
        def is_enemy_piece(piece):
            if not piece:
                return False
            if color == 'W':
                return piece in ('k', 'n', 'r', 'p')
            else:
                return piece in ('K', 'N', 'R', 'P')
        
        # Helper to check if move leaves king in check
        def is_move_safe(fr, fc, tr, tc):
            # Simulate move
            original_from = board[fr][fc]
            original_to = board[tr][tc]
            moving_piece = original_from
            
            # Handle pawn promotion in simulation
            if moving_piece.upper() == 'P':
                if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                    moving_piece = 'R' if color == 'W' else 'r'
            
            board[tr][tc] = moving_piece
            board[fr][fc] = ''
            
            # Check if own king is in check
            in_check = self._is_king_in_check(board, color)
            
            # Undo move
            board[fr][fc] = original_from
            board[tr][tc] = original_to
            
            return not in_check
        
        # Helper to find king position
        def find_king():
            target = 'K' if color == 'W' else 'k'
            for r in range(2):
                for c in range(8):
                    if board[r][c] == target:
                        return (r, c)
            return None
        
        # Helper to check if square is attacked by enemy
        def is_square_attacked(tr, tc, color):
            enemy_color = 'B' if color == 'W' else 'W'
            for r in range(2):
                for c in range(8):
                    piece = board[r][c]
                    if not piece:
                        continue
                    if (enemy_color == 'W' and piece in ('K', 'N', 'R', 'P')) or \
                       (enemy_color == 'B' and piece in ('k', 'n', 'r', 'p')):
                        # Check if this piece can attack (tr, tc)
                        pt = piece.upper()
                        dr, dc = tr - r, tc - c
                        
                        if pt == 'K':
                            if abs(dr) <= 1 and abs(dc) <= 1 and (dr != 0 or dc != 0):
                                return True
                        elif pt == 'N':
                            # L-shape or 2-square linear jump
                            if (abs(dr), abs(dc)) in [(1, 2), (2, 1), (0, 2)]:
                                return True
                        elif pt == 'R':
                            # Rook moves: same row or same column
                            if dr == 0:  # same row
                                step = 1 if dc > 0 else -1
                                blocked = False
                                for c2 in range(c + step, tc, step):
                                    if board[r][c2]:
                                        blocked = True
                                        break
                                if not blocked:
                                    return True
                            elif dc == 0:  # same column
                                step = 1 if dr > 0 else -1
                                blocked = False
                                for r2 in range(r + step, tr, step):
                                    if board[r2][c]:
                                        blocked = True
                                        break
                                if not blocked:
                                    return True
                        elif pt == 'P':
                            # Pawn attacks diagonally forward
                            direction = 1 if enemy_color == 'W' else -1
                            if dr == direction and abs(dc) == 1:
                                return True
            return False
        
        # Helper to check if king is in check
        def _is_king_in_check(board, color):
            king_pos = find_king()
            if not king_pos:
                return True  # King not found - should not happen in valid game
            return is_square_attacked(king_pos[0], king_pos[1], color)
        
        # Generate moves for each piece
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not is_own_piece(piece):
                    continue
                
                pt = get_piece_type(piece)
                from_sq = f"{'abcdefgh'[c]}{r+1}"
                
                if pt == 'K':
                    # King moves: 1 square in any direction
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if in_bounds(nr, nc):
                                target = board[nr][nc]
                                if not is_own_piece(target):
                                    if is_move_safe(r, c, nr, nc):
                                        to_sq = f"{'abcdefgh'[nc]}{nr+1}"
                                        is_capture = is_enemy_piece(target)
                                        if is_capture:
                                            moves.append(f"K{from_sq}x{to_sq}")
                                        else:
                                            moves.append(f"K{from_sq}{to_sq}")
                
                elif pt == 'N':
                    # Knight moves: L-shape and linear 2-square jump
                    l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                                (-2, -1), (-2, 1), (2, -1), (2, 1)]
                    linear_deltas = [(0, -2), (0, 2)]
                    for dr, dc in l_deltas + linear_deltas:
                        nr, nc = r + dr, c + dc
                        if in_bounds(nr, nc):
                            target = board[nr][nc]
                            if not is_own_piece(target):
                                if is_move_safe(r, c, nr, nc):
                                    to_sq = f"{'abcdefgh'[nc]}{nr+1}"
                                    is_capture = is_enemy_piece(target)
                                    if is_capture:
                                        moves.append(f"N{from_sq}x{to_sq}")
                                    else:
                                        moves.append(f"N{from_sq}{to_sq}")
                
                elif pt == 'R':
                    # Rook moves: slide in 4 directions
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        while in_bounds(nr, nc):
                            target = board[nr][nc]
                            if target == '':
                                if is_move_safe(r, c, nr, nc):
                                    to_sq = f"{'abcdefgh'[nc]}{nr+1}"
                                    moves.append(f"R{from_sq}{to_sq}")
                            elif is_enemy_piece(target):
                                if is_move_safe(r, c, nr, nc):
                                    to_sq = f"{'abcdefgh'[nc]}{nr+1}"
                                    moves.append(f"R{from_sq}x{to_sq}")
                                break
                            else:
                                break
                            nr += dr
                            nc += dc
                
                elif pt == 'P':
                    # Pawn moves
                    direction = 1 if color == 'W' else -1
                    # Forward move
                    nc = c + direction
                    if in_bounds(r, nc) and board[r][nc] == '':
                        if is_move_safe(r, c, r, nc):
                            to_sq = f"{'abcdefgh'[nc]}{r+1}"
                            # Check promotion
                            if (color == 'W' and nc == 7) or (color == 'B' and nc == 0):
                                moves.append(f"P{from_sq}{to_sq}")
                            else:
                                moves.append(f"P{from_sq}{to_sq}")
                    # Diagonal captures
                    for dr in [-1, 1]:
                        nr = r + dr
                        nc = c + direction
                        if in_bounds(nr, nc):
                            target = board[nr][nc]
                            if is_enemy_piece(target):
                                if is_move_safe(r, c, nr, nc):
                                    to_sq = f"{'abcdefgh'[nc]}{nr+1}"
                                    # Check promotion
                                    if (color == 'W' and nc == 7) or (color == 'B' and nc == 0):
                                        moves.append(f"P{from_sq}x{to_sq}")
                                    else:
                                        moves.append(f"P{from_sq}x{to_sq}")
        
        return moves

    def _evaluate_move(self, move, board):
        """Evaluate the quality of a move."""
        score = 0
        
        # Extract from and to squares
        if 'x' in move:
            from_sq = move[1:3]
            to_sq = move[4:6]
            score += 10  # Bonus for captures
        else:
            from_sq = move[1:3]
            to_sq = move[3:5]
        
        # Extract piece type
        piece = move[0]
        
        # Map to positions
        col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        from_col = col_map[from_sq[0]]
        from_row = int(from_sq[1]) - 1
        to_col = col_map[to_sq[0]]
        to_row = int(to_sq[1]) - 1
        
        # Bonus for controlling center squares (d, e columns)
        if to_col in [3, 4]:
            score += 5
        
        # Bonus for advancing pawns
        if piece == 'P':
            direction = 1 if self.color == 'W' else -1
            if (self.color == 'W' and to_col > from_col) or (self.color == 'B' and to_col < from_col):
                score += 3
        
        # Bonus for knight centralization
        if piece == 'N':
            if to_col in [2, 3, 4, 5]:
                score += 5
        
        # Bonus for rook opening
        if piece == 'R':
            # Rook gets bonus for moving to open files or central files
            if to_col in [2, 3, 4, 5]:
                score += 2
        
        # Bonus for king safety (moving toward center in early game)
        if piece == 'K':
            if to_col in [2, 3, 4, 5]:
                score += 2
        
        # Check if move gives check
        # (Simplified check detection - just see if king is attacked after move)
        # This is computationally expensive, so we'll use a simplified version
        # Only check for immediate check if it's a promising move
        
        return score
