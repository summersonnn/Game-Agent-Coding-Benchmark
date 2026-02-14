"""
Agent Code: A7-TwoByEightChess
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-14 13:30:59
"""



import random

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
        self.cols = 'abcdefgh'
        # Piece values for evaluation
        self.piece_values = {'P': 100, 'N': 320, 'R': 500, 'K': 20000}

    def make_move(self, board, move_history):
        """
        Decide the next move based on the current board state.
        """
        # Get all legal moves for the current player
        legal_moves = self.get_all_legal_moves(board, self.color)
        
        if not legal_moves:
            # No legal moves available (Stalemate or Checkmate)
            return ""

        # Sort moves to prioritize captures (simple move ordering)
        legal_moves.sort(key=lambda m: m[5], reverse=True)

        best_move = None
        best_score = -float('inf')
        
        # Search depth: 3 ply is safe for Python within 1s time limit
        depth = 3
        
        # Iterate through moves to find the best one using Minimax
        for move in legal_moves:
            # move format: (piece, r1, c1, r2, c2, is_capture)
            new_board, _ = self.apply_move(board, move)
            
            # Evaluate the resulting board state
            score = self.minimax(new_board, depth - 1, -float('inf'), float('inf'), False)
            
            if score > best_score:
                best_score = score
                best_move = move
                
        # Return the best move found, or a random one if search failed to find a better one
        if best_move:
            return self.move_to_str(best_move)
        
        return self.move_to_str(random.choice(legal_moves))

    def move_to_str(self, move):
        """Convert internal move representation to string notation."""
        piece, r1, c1, r2, c2, is_capture = move
        from_sq = self.cols[c1] + str(r1 + 1)
        to_sq = self.cols[c2] + str(r2 + 1)
        mid = 'x' if is_capture else ''
        return f"{piece}{from_sq}{mid}{to_sq}"

    def minimax(self, board, depth, alpha, beta, is_maximizing):
        """Minimax algorithm with Alpha-Beta pruning."""
        if depth == 0:
            return self.evaluate(board)

        current_color = self.color if is_maximizing else ('B' if self.color == 'W' else 'W')
        moves = self.get_all_legal_moves(board, current_color)

        if not moves:
            if self.is_check(board, current_color):
                # Checkmate detected
                return -10000 if is_maximizing else 10000
            else:
                # Stalemate detected
                return 0

        if is_maximizing:
            max_eval = -float('inf')
            for move in moves:
                new_board, _ = self.apply_move(board, move)
                eval_val = self.minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_board, _ = self.apply_move(board, move)
                eval_val = self.minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate(self, board):
        """Static evaluation of the board state."""
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece == '':
                    continue
                
                val = self.piece_values.get(piece.upper(), 0)
                
                # Positional adjustments
                if piece.upper() == 'P':
                    # Bonus for pawn advancement
                    if piece.isupper(): # White
                        val += c * 10
                    else: # Black
                        val += (7 - c) * 10
                
                if piece.isupper():
                    score += val
                else:
                    score -= val
                    
        # Return score relative to the agent's color
        return score if self.color == 'W' else -score

    def get_all_legal_moves(self, board, color):
        """Generate all legal moves for a given color, filtering out moves that leave King in check."""
        legal_moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece == '': continue
                
                is_white = piece.isupper()
                if (color == 'W' and is_white) or (color == 'B' and not is_white):
                    pseudo_moves = self.get_pseudo_moves(board, r, c, piece)
                    for (tr, tc) in pseudo_moves:
                        # Simulate move to check for king safety
                        captured = board[tr][tc]
                        board[tr][tc] = piece
                        board[r][c] = ''
                        
                        # Handle promotion in simulation
                        promoted = False
                        if piece.upper() == 'P':
                            if (is_white and tc == 7) or (not is_white and tc == 0):
                                board[tr][tc] = 'R' if is_white else 'r'
                                promoted = True
                        
                        if not self.is_check(board, color):
                            is_capture = (captured != '')
                            legal_moves.append((piece.upper(), r, c, tr, tc, is_capture))
                        
                        # Undo move
                        board[r][c] = piece
                        board[tr][tc] = captured
        return legal_moves

    def get_pseudo_moves(self, board, r, c, piece):
        """Generate pseudo-legal moves (geometry only) for a piece."""
        moves = []
        ptype = piece.upper()
        is_white = piece.isupper()

        if ptype == 'K':
            deltas = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
            for dr, dc in deltas:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '' or (is_white != target.isupper()):
                        moves.append((nr, nc))

        elif ptype == 'N':
            # L-shape
            deltas = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
            # Linear jump
            deltas.extend([(0,-2), (0,2)])
            
            for dr, dc in deltas:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '' or (is_white != target.isupper()):
                        moves.append((nr, nc))

        elif ptype == 'R':
            deltas = [(-1,0), (1,0), (0,-1), (0,1)]
            for dr, dc in deltas:
                nr, nc = r+dr, c+dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '':
                        moves.append((nr, nc))
                    else:
                        if is_white != target.isupper():
                            moves.append((nr, nc))
                        break
                    nr += dr
                    nc += dc

        elif ptype == 'P':
            direction = 1 if is_white else -1
            
            # Move forward
            nc = c + direction
            if 0 <= nc < 8:
                if board[r][nc] == '':
                    moves.append((r, nc))
            
            # Capture
            for dr in [-1, 1]:
                nr = r + dr
                nc = c + direction
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target != '' and (is_white != target.isupper()):
                        moves.append((nr, nc))
        return moves

    def is_check(self, board, color):
        """Check if the King of the given color is under attack."""
        # Find king
        kr, kc = -1, -1
        king_char = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == king_char:
                    kr, kc = r, c
                    break
        
        if kr == -1: return True 

        enemy_color = 'B' if color == 'W' else 'W'
        
        # Check if any enemy piece can attack the King's square
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece == '': continue
                is_white = piece.isupper()
                if (enemy_color == 'W' and is_white) or (enemy_color == 'B' and not is_white):
                    enemy_moves = self.get_pseudo_moves(board, r, c, piece)
                    if (kr, kc) in enemy_moves:
                        return True
        return False

    def apply_move(self, board, move):
        """Apply a move to a copy of the board and return the new board."""
        new_board = [row[:] for row in board]
        p, r1, c1, r2, c2, _ = move
        moving_piece = board[r1][c1]
        captured = new_board[r2][c2]
        
        new_board[r2][c2] = moving_piece
        new_board[r1][c1] = ''
        
        # Handle Promotion
        if moving_piece.upper() == 'P':
            is_white = moving_piece.isupper()
            if (is_white and c2 == 7) or (not is_white and c2 == 0):
                new_board[r2][c2] = 'R' if is_white else 'r'
                
        return new_board, captured
