"""
Agent Code: A7-1D_Chess
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:10:12
"""

import copy

import random
import copy

class OneDChessAgent:
    """
    1D Chess Agent using minimax with alpha-beta pruning and piece-square tables.
    """
    
    # Piece values
    PIECE_VALUES = {
        'K': 1000,  # King - essential but high value for terminal states
        'k': 1000,
        'N': 30,    # Knight
        'n': 30,
        'R': 50,    # Rook
        'r': 50
    }
    
    # Position bonus tables (favor controlling the center and advancing)
    KING_POSITION_BONUS = {
        'W': [0, 1, 2, 3, 3, 2, 1, 0],  # White king prefers center-right
        'B': [0, 1, 2, 3, 3, 2, 1, 0]   # Black king prefers center-left
    }
    
    KNIGHT_POSITION_BONUS = {
        'W': [0, 2, 4, 5, 5, 4, 2, 0],  # Knights prefer center
        'B': [0, 2, 4, 5, 5, 4, 2, 0]
    }
    
    ROOK_POSITION_BONUS = {
        'W': [0, 1, 2, 3, 3, 2, 1, 0],  # Rooks prefer being advanced
        'B': [0, 1, 2, 3, 3, 2, 1, 0]
    }
    
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.opponent_color = 'B' if color == 'W' else 'W'
        
    def make_move(self, board, move_history):
        """
        Decide the next move using minimax search.
        """
        # Find all legal moves
        legal_moves = self._get_all_legal_moves(board, self.color)
        
        if not legal_moves:
            # Should not happen in normal play, but return something
            return "K12" if self.color == 'W' else "k78"
        
        # Use minimax with alpha-beta pruning
        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        # Search depth based on game phase
        depth = 3
        
        for move in legal_moves:
            # Apply move
            new_board = self._apply_move(board, move)
            
            # Check if this move is checkmate
            if self._is_checkmate(new_board, self.opponent_color):
                return move  # Take the checkmate!
            
            # Evaluate using minimax
            score = self._minimax(new_board, depth - 1, alpha, beta, False)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, best_score)
        
        # If no good move found, pick randomly from legal moves
        if best_move is None:
            best_move = random.choice(legal_moves)
        
        return best_move
    
    def _minimax(self, board, depth, alpha, beta, is_maximizing):
        """
        Minimax algorithm with alpha-beta pruning.
        """
        # Terminal conditions
        if depth == 0:
            return self._evaluate_board(board)
        
        if is_maximizing:
            # Maximizing player (our color)
            legal_moves = self._get_all_legal_moves(board, self.color)
            
            if not legal_moves:
                if self._is_in_check(board, self.color):
                    return -10000  # Checkmate - losing
                return 0  # Stalemate
            
            max_score = float('-inf')
            for move in legal_moves:
                new_board = self._apply_move(board, move)
                score = self._minimax(new_board, depth - 1, alpha, beta, False)
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score
        else:
            # Minimizing player (opponent)
            legal_moves = self._get_all_legal_moves(board, self.opponent_color)
            
            if not legal_moves:
                if self._is_in_check(board, self.opponent_color):
                    return 10000  # Checkmate - winning
                return 0  # Stalemate
            
            min_score = float('inf')
            for move in legal_moves:
                new_board = self._apply_move(board, move)
                score = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score
    
    def _evaluate_board(self, board):
        """
        Evaluate the board position from the perspective of our color.
        Higher score is better for us.
        """
        score = 0
        
        for pos, piece in enumerate(board):
            if not piece:
                continue
            
            # Material evaluation
            if self._is_our_piece(piece):
                score += self.PIECE_VALUES.get(piece, 0)
            else:
                score -= self.PIECE_VALUES.get(piece, 0)
            
            # Position evaluation
            piece_type = piece.upper()
            color = 'W' if piece.isupper() else 'B'
            
            if piece_type == 'K':
                score += self.KING_POSITION_BONUS[color][pos] * (1 if color == self.color else -1)
            elif piece_type == 'N':
                score += self.KNIGHT_POSITION_BONUS[color][pos] * (1 if color == self.color else -1)
            elif piece_type == 'R':
                score += self.ROOK_POSITION_BONUS[color][pos] * (1 if color == self.color else -1)
        
        # Bonus for having more pieces
        our_pieces = sum(1 for p in board if p and self._is_our_piece(p))
        opp_pieces = sum(1 for p in board if p and not self._is_our_piece(p))
        score += (our_pieces - opp_pieces) * 5
        
        # Bonus for being in check (negative for opponent)
        if self._is_in_check(board, self.color):
            score -= 50
        if self._is_in_check(board, self.opponent_color):
            score += 50
        
        return score
    
    def _get_all_legal_moves(self, board, color):
        """
        Get all legal moves for the given color.
        """
        moves = []
        
        for from_pos in range(8):
            piece = board[from_pos]
            if not piece:
                continue
            
            if not self._is_our_piece(piece) if color == self.color else self._is_our_piece(piece):
                continue
            
            # Get valid moves for this piece
            piece_moves = self._get_valid_moves_for_piece(board, from_pos, color)
            
            for to_pos, is_capture in piece_moves:
                # Verify the move doesn't leave king in check
                if self._is_move_safe(board, from_pos, to_pos, color):
                    move_str = self._format_move(piece, from_pos, to_pos, is_capture)
                    moves.append(move_str)
        
        return moves
    
    def _get_valid_moves_for_piece(self, board, pos, color):
        """
        Get valid destination squares for piece at pos.
        """
        piece = board[pos]
        if not piece:
            return []
        
        piece_type = piece.upper()
        moves = []
        
        if piece_type == 'K':
            for delta in [-1, 1]:
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    if not self._is_our_piece_at(board, to_pos, color):
                        is_capture = self._is_enemy_piece_at(board, to_pos, color)
                        moves.append((to_pos, is_capture))
        
        elif piece_type == 'N':
            for delta in [-2, 2]:
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    if not self._is_our_piece_at(board, to_pos, color):
                        is_capture = self._is_enemy_piece_at(board, to_pos, color)
                        moves.append((to_pos, is_capture))
        
        elif piece_type == 'R':
            for direction in [-1, 1]:
                to_pos = pos + direction
                while 0 <= to_pos < 8:
                    target = board[to_pos]
                    if target == '':
                        moves.append((to_pos, False))
                    elif self._is_enemy_piece_at(board, to_pos, color):
                        moves.append((to_pos, True))
                        break
                    else:
                        break
                    to_pos += direction
        
        return moves
    
    def _is_move_safe(self, board, from_pos, to_pos, color):
        """
        Check if making this move would leave the King in check.
        """
        # Simulate the move
        new_board = board[:]
        new_board[to_pos] = new_board[from_pos]
        new_board[from_pos] = ''
        
        # Check if King is in check after move
        return not self._is_in_check(new_board, color)
    
    def _is_in_check(self, board, color):
        """
        Check if the given color's King is under attack.
        """
        king_pos = self._find_king(board, color)
        if king_pos == -1:
            return True
        
        enemy_color = 'B' if color == 'W' else 'W'
        
        # Check all enemy pieces for attacks on the King
        for pos in range(8):
            piece = board[pos]
            if piece and not self._is_our_piece_at(board, pos, color):
                # Get moves ignoring check
                enemy_moves = self._get_valid_moves_for_piece(board, pos, enemy_color)
                for to_pos, _ in enemy_moves:
                    if to_pos == king_pos:
                        return True
        return False
    
    def _is_checkmate(self, board, color):
        """
        Check if the given color is in checkmate.
        """
        if not self._is_in_check(board, color):
            return False
        
        # Check if any move can escape check
        legal_moves = self._get_all_legal_moves(board, color)
        return len(legal_moves) == 0
    
    def _find_king(self, board, color):
        """Find the position of the King for the given color."""
        target = 'K' if color == 'W' else 'k'
        for i, piece in enumerate(board):
            if piece == target:
                return i
        return -1
    
    def _is_our_piece(self, piece):
        """Check if piece belongs to our color."""
        if not piece:
            return False
        if self.color == 'W':
            return piece.isupper()
        else:
            return piece.islower()
    
    def _is_our_piece_at(self, board, pos, color):
        """Check if piece at position belongs to given color."""
        piece = board[pos]
        if not piece:
            return False
        if color == 'W':
            return piece.isupper()
        else:
            return piece.islower()
    
    def _is_enemy_piece_at(self, board, pos, color):
        """Check if piece at position belongs to opponent of given color."""
        piece = board[pos]
        if not piece:
            return False
        if color == 'W':
            return piece.islower()
        else:
            return piece.isupper()
    
    def _apply_move(self, board, move_str):
        """
        Apply a move and return the new board.
        """
        new_board = board[:]
        parsed = self._parse_move(move_str)
        if parsed:
            piece_type, from_pos, to_pos, _ = parsed
            new_board[to_pos] = new_board[from_pos]
            new_board[from_pos] = ''
        return new_board
    
    def _parse_move(self, move_str):
        """
        Parse move notation into (piece_type, from_pos, to_pos, is_capture).
        """
        move_str = move_str.strip()
        if len(move_str) < 3:
            return None
        
        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R'):
            return None
        
        if 'x' in move_str.lower():
            parts = move_str[1:].lower().split('x')
            if len(parts) != 2:
                return None
            try:
                from_sq = int(parts[0])
                to_sq = int(parts[1])
                is_capture = True
            except ValueError:
                return None
        else:
            if len(move_str) != 3:
                return None
            try:
                from_sq = int(move_str[1])
                to_sq = int(move_str[2])
                is_capture = False
            except ValueError:
                return None
        
        from_pos = from_sq - 1
        to_pos = to_sq - 1
        
        if not (0 <= from_pos < 8 and 0 <= to_pos < 8):
            return None
        
        return (piece, from_pos, to_pos, is_capture)
    
    def _format_move(self, piece, from_pos, to_pos, is_capture):
        """
        Format a move into notation.
        """
        from_sq = from_pos + 1
        to_sq = to_pos + 1
        
        if is_capture:
            return f"{piece}{from_sq}x{to_sq}"
        else:
            return f"{piece}{from_sq}{to_sq}"
