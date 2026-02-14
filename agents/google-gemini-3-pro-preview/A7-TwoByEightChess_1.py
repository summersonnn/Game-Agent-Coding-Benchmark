"""
Agent Code: A7-TwoByEightChess
Model: google-gemini-3-pro-preview
Run: 1
Generated: 2026-02-14 13:16:13
"""

import time
import random
import copy

class TwoByEightChessAgent:
    def __init__(self, name, color):
        """
        Initialize the agent.

        Args:
            name: str - The agent's name (e.g., "Agent-1")
            color: str - 'W' for White or 'B' for Black
        """
        self.name = name
        self.color = color
        self.opp_color = 'B' if self.color == 'W' else 'W'
        self.max_depth = 4  # Search depth
        self.cols_map = 'abcdefgh'
        
        # Piece values for evaluation
        self.piece_values = {
            'K': 20000, 'k': -20000,
            'R': 500,   'r': -500,
            'N': 300,   'n': -300,
            'P': 100,   'p': -100
        }

    def make_move(self, board, move_history):
        """
        Decide the next move based on the current board state.
        """
        start_time = time.time()
        
        # Get all valid moves
        valid_moves = self._get_all_valid_moves(board, self.color)
        
        if not valid_moves:
            return "" # Should not happen unless checkmate/stalemate logic in engine handles it
        
        # If only one move, take it
        if len(valid_moves) == 1:
            return valid_moves[0]

        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        # Shuffle to add randomness for equal moves and prevent predictability
        random.shuffle(valid_moves)

        for move in valid_moves:
            # Simulate move
            sim_board = self._simulate_move(board, move, self.color)
            
            # Minimax search
            score = self._minimax(sim_board, self.max_depth - 1, alpha, beta, False)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, best_score)
            
            # Safety check for time (leave 100ms buffer)
            if time.time() - start_time > 0.85:
                break
                
        return best_move if best_move else random.choice(valid_moves)

    def _minimax(self, board, depth, alpha, beta, is_maximizing):
        # Base cases
        if depth == 0:
            return self._evaluate_board(board)
        
        # Check for game over states (simplified: if no moves available)
        current_color = self.color if is_maximizing else self.opp_color
        valid_moves = self._get_all_valid_moves(board, current_color)
        
        if not valid_moves:
            # If in check, it's mate. If not, stalemate.
            if self._is_in_check(board, current_color):
                return -float('inf') if is_maximizing else float('inf')
            return 0  # Stalemate

        if is_maximizing:
            max_eval = -float('inf')
            for move in valid_moves:
                sim_board = self._simulate_move(board, move, self.color)
                eval_val = self._minimax(sim_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid_moves:
                sim_board = self._simulate_move(board, move, self.opp_color)
                eval_val = self._minimax(sim_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate_board(self, board):
        score = 0
        w_king_pos = None
        b_king_pos = None

        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                
                # Material Score
                score += self.piece_values.get(piece, 0)
                
                # Positional adjustments
                ptype = piece.upper()
                
                # Encourage Pawns to advance
                if ptype == 'P':
                    if piece == 'P':
                        score += c * 10  # White advances right
                    else:
                        score -= (7 - c) * 10 # Black advances left
                
                # Track Kings for safety eval
                if piece == 'K':
                    w_king_pos = (r, c)
                elif piece == 'k':
                    b_king_pos = (r, c)

        # Return score from perspective of self.color
        final_score = score if self.color == 'W' else -score
        return final_score

    # --- Move Generation & Simulation Helpers ---

    def _simulate_move(self, board, move_str, color):
        """Returns a new deepcopied board after the move."""
        new_board = [row[:] for row in board]
        parsed = self._parse_move_internal(move_str)
        if not parsed:
            return new_board
        
        _, (fr, fc), (tr, tc), _ = parsed
        
        piece = new_board[fr][fc]
        new_board[fr][fc] = ''
        
        # Promotion Logic
        promoted = False
        if piece.upper() == 'P':
            if (piece == 'P' and tc == 7) or (piece == 'p' and tc == 0):
                new_board[tr][tc] = 'R' if piece == 'P' else 'r'
                promoted = True
        
        if not promoted:
            new_board[tr][tc] = piece
            
        return new_board

    def _get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_moves = self._get_pseudo_legal_moves(board, r, c)
                    
                    # Filter for check safety
                    for move_str in piece_moves:
                        sim_board = self._simulate_move(board, move_str, color)
                        if not self._is_in_check(sim_board, color):
                            moves.append(move_str)
        return moves

    def _get_pseudo_legal_moves(self, board, r, c):
        """Generates moves without checking if they leave King in check."""
        piece = board[r][c]
        ptype = piece.upper()
        color = 'W' if piece.isupper() else 'B'
        moves = []
        
        candidate_destinations = [] # List of (r, c, is_capture)

        if ptype == 'K':
            deltas = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
            for dr, dc in deltas:
                nr, nc = r+dr, c+dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        candidate_destinations.append((nr, nc, target != ''))

        elif ptype == 'N':
            # L-shapes + Linear Jump (2 squares horizontal)
            deltas = [(-1,-2), (-1,2), (1,-2), (1,2), (-2,-1), (-2,1), (2,-1), (2,1),
                      (0, -2), (0, 2)] 
            for dr, dc in deltas:
                nr, nc = r+dr, c+dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        candidate_destinations.append((nr, nc, target != ''))

        elif ptype == 'R':
            dirs = [(-1,0), (1,0), (0,-1), (0,1)]
            for dr, dc in dirs:
                nr, nc = r+dr, c+dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        candidate_destinations.append((nr, nc, False))
                    elif not self._is_own_piece(target, color):
                        candidate_destinations.append((nr, nc, True))
                        break # Capture and stop
                    else:
                        break # Blocked by own piece
                    nr, nc = nr+dr, nc+dc

        elif ptype == 'P':
            direction = 1 if color == 'W' else -1
            # Forward 1
            nc = c + direction
            if self._in_bounds(r, nc) and board[r][nc] == '':
                candidate_destinations.append((r, nc, False))
            
            # Diagonal Capture
            for dr in [-1, 1]:
                nr = r + dr
                nc = c + direction
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target != '' and not self._is_own_piece(target, color):
                        candidate_destinations.append((nr, nc, True))

        # Convert to notation
        from_str = self._pos_to_notation(r, c)
        for tr, tc, is_capture in candidate_destinations:
            to_str = self._pos_to_notation(tr, tc)
            # Notation: P(from)(x?)(to)
            sep = 'x' if is_capture else ''
            moves.append(f"{ptype}{from_str}{sep}{to_str}")

        return moves

    def _is_in_check(self, board, color):
        king_pos = None
        target_k = 'K' if color == 'W' else 'k'
        enemy_color = 'B' if color == 'W' else 'W'
        
        # Find King
        for r in range(2):
            for c in range(8):
                if board[r][c] == target_k:
                    king_pos = (r, c)
                    break
            if king_pos: break
            
        if not king_pos: return True # Should not happen, but assume check if king missing

        # Check if any enemy piece attacks king_pos
        # We can do this by generating all enemy pseudo moves and checking if they hit king
        # OR reverse check (more efficient for specific pieces)
        # Let's simple gen all enemy moves
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    # Get pseudo moves for this piece
                    moves = self._get_pseudo_legal_moves(board, r, c)
                    for m in moves:
                        # Parse destination
                        parsed = self._parse_move_internal(m)
                        if parsed and parsed[2] == king_pos:
                            return True
        return False

    def _is_own_piece(self, piece, color):
        if not piece: return False
        return piece.isupper() if color == 'W' else piece.islower()

    def _in_bounds(self, r, c):
        return 0 <= r < 2 and 0 <= c < 8

    def _pos_to_notation(self, r, c):
        return f"{self.cols_map[c]}{r+1}"

    def _notation_to_pos(self, n):
        c = self.cols_map.index(n[0])
        r = int(n[1]) - 1
        return r, c

    def _parse_move_internal(self, move_str):
        # Format: [Piece][From][x?][To] e.g. Nb2d1 or Ra1xa2
        try:
            piece = move_str[0]
            if 'x' in move_str:
                parts = move_str[1:].split('x')
                from_sq = parts[0]
                to_sq = parts[1]
                is_capture = True
            else:
                from_sq = move_str[1:3]
                to_sq = move_str[3:5]
                is_capture = False
            
            fr, fc = self._notation_to_pos(from_sq)
            tr, tc = self._notation_to_pos(to_sq)
            return piece, (fr, fc), (tr, tc), is_capture
        except:
            return None