"""
Agent Code: A7-TwoByEightChess
Model: google-gemini-3-pro-preview
Run: 2
Generated: 2026-02-14 13:16:13
"""

import time
import random

class TwoByEightChessAgent:
    def __init__(self, name, color):
        """
        Initialize the agent.
        Args:
            name: str - The agent's name
            color: str - 'W' for White or 'B' for Black
        """
        self.name = name
        self.color = color
        self.is_white = (color == 'W')
        self.opponent = 'B' if self.is_white else 'W'
        self.cols = 'abcdefgh'
        self.time_limit = 0.9  # Safety buffer for 1s limit

    def make_move(self, board, move_history):
        """
        Decide the next move using Iterative Deepening Minimax.
        """
        start_time = time.time()
        
        # --- Internal Helper Functions (Rule Implementation) ---

        def get_pt(piece):
            return piece.upper()

        def is_own(piece, c):
            if not piece: return False
            return piece.isupper() if c == 'W' else piece.islower()

        def is_enemy(piece, c):
            if not piece: return False
            return piece.islower() if c == 'W' else piece.isupper()

        def to_notation(r, c):
            return f"{self.cols[c]}{r+1}"

        def find_king(b, c):
            target = 'K' if c == 'W' else 'k'
            for r in range(2):
                for col in range(8):
                    if b[r][col] == target:
                        return (r, col)
            return None

        def is_square_attacked(b, r, c, attacker_color):
            # Check for Knight attacks (L-shape + Linear jump)
            n_moves = [(-1, -2), (-1, 2), (1, -2), (1, 2), 
                       (-2, -1), (-2, 1), (2, -1), (2, 1), 
                       (0, -2), (0, 2)]
            for dr, dc in n_moves:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    p = b[nr][nc]
                    if p and is_own(p, attacker_color) and get_pt(p) == 'N':
                        return True

            # Check for King attacks
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        p = b[nr][nc]
                        if p and is_own(p, attacker_color) and get_pt(p) == 'K':
                            return True

            # Check for Rook attacks
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    p = b[nr][nc]
                    if p:
                        if is_own(p, attacker_color) and get_pt(p) == 'R':
                            return True
                        break
                    nr, nc = nr + dr, nc + dc

            # Check for Pawn attacks
            # If attacker is White, they are to the left (c-1)
            # If attacker is Black, they are to the right (c+1)
            pawn_col = c - 1 if attacker_color == 'W' else c + 1
            for dr in [-1, 1]:
                nr = r + dr
                if 0 <= nr < 2 and 0 <= pawn_col < 8:
                    p = b[nr][pawn_col]
                    if p and is_own(p, attacker_color) and get_pt(p) == 'P':
                        return True
            return False

        def is_in_check(b, c):
            kp = find_king(b, c)
            if not kp: return True # Should not happen unless King captured
            enemy_c = 'B' if c == 'W' else 'W'
            return is_square_attacked(b, kp[0], kp[1], enemy_c)

        def get_valid_moves(b, c):
            moves = [] # List of (move_str, next_board_state)
            direction = 1 if c == 'W' else -1

            for r in range(2):
                for col in range(8):
                    p = b[r][col]
                    if not p or not is_own(p, c): continue
                    
                    pt = get_pt(p)
                    candidates = []

                    if pt == 'K':
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                if dr==0 and dc==0: continue
                                candidates.append((r+dr, col+dc))
                    
                    elif pt == 'N':
                        # All jumps (L + Linear)
                        deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2), 
                                  (-2, -1), (-2, 1), (2, -1), (2, 1), 
                                  (0, -2), (0, 2)]
                        for dr, dc in deltas:
                            candidates.append((r+dr, col+dc))
                            
                    elif pt == 'R':
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r+dr, col+dc
                            while 0 <= nr < 2 and 0 <= nc < 8:
                                candidates.append((nr, nc))
                                if b[nr][nc]: break
                                nr, nc = nr+dr, nc+dc
                                
                    elif pt == 'P':
                        # Move 1
                        nr, nc = r, col + direction
                        if 0 <= nc < 8 and b[nr][nc] == '':
                            candidates.append((nr, nc))
                        # Capture
                        for dr in [-1, 1]:
                            nr, nc = r+dr, col + direction
                            if 0 <= nr < 2 and 0 <= nc < 8:
                                if is_enemy(b[nr][nc], c):
                                    candidates.append((nr, nc))

                    # Process Candidates
                    for tr, tc in candidates:
                        if not (0 <= tr < 2 and 0 <= tc < 8): continue
                        target = b[tr][tc]
                        if is_own(target, c): continue
                        
                        is_cap = (target != '')
                        
                        # Validate Pawn diagonal rule logic
                        if pt == 'P':
                            if tc == col and is_cap: continue # Straight must be empty
                            if tc != col and not is_cap: continue # Diag must be capture

                        # Simulate
                        new_b = [row[:] for row in b]
                        new_b[r][col] = ''
                        moving_p = p
                        
                        # Promotion
                        if pt == 'P':
                            if (c == 'W' and tc == 7) or (c == 'B' and tc == 0):
                                moving_p = 'R' if c == 'W' else 'r'
                        
                        new_b[tr][tc] = moving_p
                        
                        # King Safety
                        if not is_in_check(new_b, c):
                            m_str = f"{pt}{to_notation(r,col)}{'x' if is_cap else ''}{to_notation(tr,tc)}"
                            moves.append((m_str, new_b))
            return moves

        def evaluate(b):
            # Material Scores
            vals = {'P': 100, 'N': 320, 'R': 500, 'K': 20000}
            score = 0
            
            w_count = 0
            b_count = 0
            
            for r in range(2):
                for col in range(8):
                    p = b[r][col]
                    if not p: continue
                    pt = get_pt(p)
                    val = vals[pt]
                    
                    # Heuristics
                    if pt == 'P':
                        # Reward advancement
                        if p.isupper(): val += col * 15
                        else: val += (7 - col) * 15
                    elif pt == 'N':
                        # Reward center presence
                        if 2 <= col <= 5: val += 15
                    
                    if p.isupper(): 
                        score += val
                        w_count += 1
                    else: 
                        score -= val
                        b_count += 1
            
            # Mobility bonus (simple estimation based on piece count)
            # score += (w_count - b_count) * 10
            
            return score if self.is_white else -score

        def minimax(b, depth, alpha, beta, maximizing):
            if time.time() - start_time > self.time_limit:
                raise TimeoutError

            if depth == 0:
                return evaluate(b)

            curr_c = self.color if maximizing else self.opponent
            moves = get_valid_moves(b, curr_c)

            if not moves:
                if is_in_check(b, curr_c):
                    return -999999 + depth # Checkmate
                return 0 # Stalemate

            # Move ordering: Captures first
            moves.sort(key=lambda x: 'x' in x[0], reverse=True)

            if maximizing:
                max_eval = float('-inf')
                for _, next_b in moves:
                    eval_val = minimax(next_b, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval_val)
                    alpha = max(alpha, eval_val)
                    if beta <= alpha: break
                return max_eval
            else:
                min_eval = float('inf')
                for _, next_b in moves:
                    eval_val = minimax(next_b, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval_val)
                    beta = min(beta, eval_val)
                    if beta <= alpha: break
                return min_eval

        # --- Main Execution ---
        
        # 1. Generate all legal moves
        legal_moves = get_valid_moves(board, self.color)
        
        if not legal_moves:
            return "" # Surrender/Draw state
            
        best_move_str = legal_moves[0][0]
        
        # 2. Iterative Deepening
        try:
            depth = 1
            while True:
                best_val = float('-inf')
                current_depth_best = None
                
                # Sort root moves
                legal_moves.sort(key=lambda x: 'x' in x[0], reverse=True)
                
                for m_str, next_b in legal_moves:
                    val = minimax(next_b, depth, float('-inf'), float('inf'), False)
                    if val > best_val:
                        best_val = val
                        current_depth_best = m_str
                
                if current_depth_best:
                    best_move_str = current_depth_best
                
                depth += 1
                # Check time before starting next depth
                if time.time() - start_time > 0.6: 
                    break
                    
        except TimeoutError:
            pass # Return the best move found so far

        return best_move_str