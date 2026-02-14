"""
Agent Code: A7-TwoByEightChess
Model: qwen/qwen3-max-thinking
Run: 2
Generated: 2026-02-14 13:30:59
"""



class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color  # 'W' for White, 'B' for Black

    def make_move(self, board, move_history):
        legal_moves = []
        cols = "abcdefgh"
        
        # Helper: Convert (row, col) to notation
        def pos_to_notation(r, c):
            return f"{cols[c]}{r + 1}"
        
        # Helper: Check if piece belongs to current agent
        def owns_piece(piece):
            return (self.color == 'W' and piece.isupper()) or (self.color == 'B' and piece.islower())
        
        # Helper: Get pseudo-legal moves for a piece
        def getPseudoMoves(piece, r, c):
            moves = []
            p_type = piece.upper()
            if p_type == 'K':
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0: 
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 2 and 0 <= nc < 8:
                            target = board[nr][nc]
                            if target == '' or not owns_piece(target):
                                moves.append((nr, nc, target != ''))
            elif p_type == 'N':
                deltas = [(-1,-2), (-1,2), (1,-2), (1,2), (-2,-1), (-2,1), (2,-1), (2,1), (0,-2), (0,2)]
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if target == '' or not owns_piece(target):
                            moves.append((nr, nc, target != ''))
            elif p_type == 'R':
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if target == '':
                            moves.append((nr, nc, False))
                        elif not owns_piece(target):
                            moves.append((nr, nc, True))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc
            elif p_type == 'P':
                dir = 1 if self.color == 'W' else -1
                # Forward move
                nc = c + dir
                if 0 <= nc < 8 and board[r][nc] == '':
                    moves.append((r, nc, False))
                # Diagonal captures
                for dr in (-1, 1):
                    nr, nc = r + dr, c + dir
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if target != '' and not owns_piece(target):
                            moves.append((nr, nc, True))
            return moves
        
        # Helper: Simulate move and handle promotion
        def simulate_move(fr, fc, tr, tc):
            new_board = [row[:] for row in board]
            piece = new_board[fr][fc]
            # Handle promotion
            if piece.upper() == 'P':
                if (self.color == 'W' and tc == 7) or (self.color == 'B' and tc == 0):
                    piece = 'R' if self.color == 'W' else 'r'
            new_board[tr][tc] = piece
            new_board[fr][fc] = ''
            return new_board
        
        # Helper: Check if King is in check
        def in_check(b, color):
            # Find target King
            target_king = 'K' if color == 'W' else 'k'
            kr, kc = None, None
            for r in [0, 1]:
                for c in range(8):
                    if b[r][c] == target_king:
                        kr, kc = r, c
                        break
                if kr is not None:
                    break
            if kr is None:
                return True
            
            opp_color = 'B' if color == 'W' else 'W'
            for r in [0, 1]:
                for c in range(8):
                    piece = b[r][c]
                    if piece == '' or ((piece.isupper() and color == 'W') or (piece.islower() and color == 'B')):
                        continue
                    # Check if this opposes piece attack kingsquare
                    p_type = piece.upper()
                    if p_type == 'K':
                        if max(abs(r - kr), abs(c - kc)) <= 1 and (r != kr or c != kc):
                            return True
                    elif p_type == 'N':
                        dr, dc = abs(r - kr), abs(c - kc)
                        if (dr == 1 and dc == 2) or (dr == 2 and dc == 1) or (dr == 0 and dc == 2):
                            return True
                    elif p_type == 'R':
                        if r == kr:
                            step = 1 if c < kc else -1
                            for cc in range(c + step, kc, step):
                                if b[r][cc] != '':
                                    break
                            else:
                                return True
                        elif c == kc:
                            step = 1 if r < kr else -1
                            for rr in range(r + step, kr, step):
                                if b[rr][c] != '':
                                    break
                            else:
                                return True
                    elif p_type == 'P':
                        if piece.isupper():  # White pawn
                            if kc == c + 1 and abs(kr - r) == 1:
                                return True
                        else:  # Black pawn
                            if kc == c - 1 and abs(kr - r) == 1:
                                return True
            return False
        
        # Helper: Evaluate board state
        def evaluate_board(b):
            scores = {'R': 10, 'N': 3, 'P': 1}
            agent_score = 0
            opp_score = 0
            for r in [0, 1]:
                for c in range(8):
                    piece = b[r][c]
                    if piece == '':
                        continue
                    val = scores.get(piece.upper(), 0)
                    if owns_piece(piece):
                        agent_score += val
                    else:
                        opp_score += val
            return agent_score - opp_score
        
        # Generate valid moves
        for r in [0, 1]:
            for c in range(8):
                piece = board[r][c]
                if piece == '' or not owns_piece(piece):
                    continue
                p_moves = getPseudoMoves(piece, r, c)
                for tr, tc, is_cap in p_moves:
                    new_b = simulate_move(r, c, tr, tc)
                    if not in_check(new_b, self.color):
                        from_sq = pos_to_notation(r, c)
                        to_sq = pos_to_notation(tr, tc)
                        move_str = f"{piece.upper()}{from_sq}{'x' if is_cap else ''}{to_sq}"
                        eval_val = evaluate_board(new_b)
                        legal_moves.append((move_str, eval_val))
        
        # Fallback if no legal moves (should not occur in valid game state)
        if not legal_moves:
            for r in [0, 1]:
                for c in range(8):
                    piece = board[r][c]
                    if piece == '' or not owns_piece(piece):
                        continue
                    p_moves = getPseudoMoves(piece, r, c)
                    for tr, tc, is_cap in p_moves:
                        from_sq = pos_to_notation(r, c)
                        to_sq = pos_to_notation(tr, tc)
                        return f"{piece.upper()}{from_sq}{'x' if is_cap else ''}{to_sq}"
            return "Ka1b1"  # Ultimate fallback
        
        # Select optimal move
        legal_moves.sort(key=lambda x: x[1], reverse=True)
        return legal_moves[0][0]
