"""
Agent Code: A7-1D_Chess
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-13 14:10:12
"""



import random

class OneDChessAgent:
    # Piece values for evaluation
    PIECE_VALUES = {
        'R': 5, 'r': 5,
        'N': 3, 'n': 3,
        'K': 100, 'k': 100  # High value for king (winning condition)
    }
    
    def __init__(self, name, color):
        """
        Initialize the agent.
        
        Args:
            name: str - The agent's name (e.g., "Agent-1")
            color: str - 'W' for White or 'B' for Black
        """
        self.name = name
        self.color = color
    
    def make_move(self, board, move_history):
        """
        Decide the next move based on the current board state.
        
        Args:
            board: list[str] - 8-element list representing the board.
                   Index 0 = Square 1, Index 7 = Square 8.
                   Pieces: 'K','N','R' (White), 'k','n','r' (Black), '' (empty)
                   
            move_history: list[str] - List of all moves played so far.
                   Example: ["N24", "n75", "R36", "rx63"]
                   
        Returns:
            str: Move in notation format.
                 Regular move: "[Piece][From][To]" e.g., "N24"
                 Capture: "[Piece][From]x[To]" e.g., "R3x6"
        """
        # Find all legal moves
        legal_moves = self._get_all_legal_moves(board)
        
        if not legal_moves:
            # Should not happen, but return a placeholder if no moves
            return "K12"
        
        # Evaluate each move and choose the best
        best_move = None
        best_score = float('-inf')
        
        for move in legal_moves:
            score = self._evaluate_move(board, move)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move else legal_moves[0]
    
    def _get_all_legal_moves(self, board):
        """Get all legal moves for the agent's color."""
        moves = []
        my_pieces = []
        
        # Find my pieces
        for i, piece in enumerate(board):
            if piece and self._is_my_piece(piece):
                my_pieces.append((i, piece))
        
        # Get legal moves for each piece
        for pos, piece in my_pieces:
            piece_moves = self._get_piece_legal_moves(board, pos, piece)
            moves.extend(piece_moves)
        
        return moves
    
    def _is_my_piece(self, piece):
        """Check if piece belongs to this agent."""
        if self.color == 'W':
            return piece in ('K', 'N', 'R')
        else:
            return piece in ('k', 'n', 'r')
    
    def _is_enemy_piece(self, piece):
        """Check if piece belongs to opponent."""
        if not piece:
            return False
        if self.color == 'W':
            return piece in ('k', 'n', 'r')
        else:
            return piece in ('K', 'N', 'R')
    
    def _get_piece_legal_moves(self, board, from_pos, piece):
        """Get legal moves for a piece at given position."""
        piece_type = piece.upper()
        moves = []
        
        if piece_type == 'K':
            moves = self._get_king_moves(board, from_pos, piece)
        elif piece_type == 'N':
            moves = self._get_knight_moves(board, from_pos, piece)
        elif piece_type == 'R':
            moves = self._get_rook_moves(board, from_pos, piece)
        
        # Filter moves that would leave king in check
        legal_moves = []
        for move in moves:
            if self._is_safe_after_move(board, from_pos, move['to'], piece):
                legal_moves.append(move)
        
        return legal_moves
    
    def _get_king_moves(self, board, from_pos, piece):
        """Get King moves (1 square left or right)."""
        moves = []
        color = self.color
        
        for delta in [-1, 1]:
            to_pos = from_pos + delta
            if 0 <= to_pos < 8:
                target = board[to_pos]
                if not self._is_my_piece(target):
                    is_capture = self._is_enemy_piece(target)
                    move_str = self._format_move(piece, from_pos, to_pos, is_capture)
                    moves.append({
                        'from': from_pos,
                        'to': to_pos,
                        'piece': piece,
                        'capture': is_capture,
                        'notation': move_str
                    })
        
        return moves
    
    def _get_knight_moves(self, board, from_pos, piece):
        """Get Knight moves (exactly 2 squares, jumps over pieces)."""
        moves = []
        
        for delta in [-2, 2]:
            to_pos = from_pos + delta
            if 0 <= to_pos < 8:
                target = board[to_pos]
                if not self._is_my_piece(target):
                    is_capture = self._is_enemy_piece(target)
                    move_str = self._format_move(piece, from_pos, to_pos, is_capture)
                    moves.append({
                        'from': from_pos,
                        'to': to_pos,
                        'piece': piece,
                        'capture': is_capture,
                        'notation': move_str
                    })
        
        return moves
    
    def _get_rook_moves(self, board, from_pos, piece):
        """Get Rook moves (any distance, blocked by pieces)."""
        moves = []
        
        for direction in [-1, 1]:
            to_pos = from_pos + direction
            while 0 <= to_pos < 8:
                target = board[to_pos]
                if target == '':
                    move_str = self._format_move(piece, from_pos, to_pos, False)
                    moves.append({
                        'from': from_pos,
                        'to': to_pos,
                        'piece': piece,
                        'capture': False,
                        'notation': move_str
                    })
                elif self._is_enemy_piece(target):
                    move_str = self._format_move(piece, from_pos, to_pos, True)
                    moves.append({
                        'from': from_pos,
                        'to': to_pos,
                        'piece': piece,
                        'capture': True,
                        'notation': move_str
                    })
                    break  # Can capture but not go further
                else:
                    break  # Blocked by own piece
                to_pos += direction
        
        return moves
    
    def _format_move(self, piece, from_pos, to_pos, is_capture):
        """Format move in notation."""
        from_sq = from_pos + 1
        to_sq = to_pos + 1
        
        if is_capture:
            return f"{piece}{from_sq}x{to_sq}"
        else:
            return f"{piece}{from_sq}{to_sq}"
    
    def _is_safe_after_move(self, board, from_pos, to_pos, piece):
        """Check if move leaves own king safe."""
        # Simulate move
        saved_from = board[from_pos]
        saved_to = board[to_pos]
        board[to_pos] = board[from_pos]
        board[from_pos] = ''
        
        # Find king position
        king_pos = self._find_king(board, self.color)
        
        # Check if king is under attack
        safe = not self._is_king_under_attack(board, king_pos, self.color)
        
        # Undo move
        board[from_pos] = saved_from
        board[to_pos] = saved_to
        
        return safe
    
    def _find_king(self, board, color):
        """Find the king's position."""
        target = 'K' if color == 'W' else 'k'
        for i, piece in enumerate(board):
            if piece == target:
                return i
        return -1
    
    def _is_king_under_attack(self, board, king_pos, color):
        """Check if the king is under attack by any enemy piece."""
        if king_pos == -1:
            return True
        
        enemy_color = 'B' if color == 'W' else 'W'
        
        # Check all enemy pieces
        for pos in range(8):
            piece = board[pos]
            if piece and self._is_enemy_of(piece, color):
                # Check if this piece can attack king_pos
                if self._can_attack(board, pos, king_pos, piece):
                    return True
        
        return False
    
    def _is_enemy_of(self, piece, my_color):
        """Check if piece belongs to enemy."""
        if my_color == 'W':
            return piece in ('k', 'n', 'r')
        else:
            return piece in ('K', 'N', 'R')
    
    def _can_attack(self, board, from_pos, to_pos, piece):
        """Check if piece at from_pos can attack to_pos."""
        piece_type = piece.upper()
        
        if piece_type == 'K':
            return abs(from_pos - to_pos) == 1
        elif piece_type == 'N':
            return abs(from_pos - to_pos) == 2
        elif piece_type == 'R':
            # Check if rook can see to_pos (straight line, no blocking)
            direction = 1 if to_pos > from_pos else -1
            pos = from_pos + direction
            while pos != to_pos:
                if board[pos]:
                    return False
                pos += direction
            return True
        
        return False
    
    def _evaluate_move(self, board, move):
        """Evaluate a move and return a score."""
        score = 0
        
        # Make temporary move
        saved_from = board[move['from']]
        saved_to = board[move['to']]
        board[move['to']] = board[move['from']]
        board[move['from']] = ''
        
        # Check if this move results in checkmate
        if self._is_checkmate(board):
            score += 1000
        # Check if this move puts opponent in check
        elif self._is_opponent_in_check(board):
            score += 50
        
        # Evaluate capture
        if move['capture']:
            captured_piece = saved_to
            score += self.PIECE_VALUES.get(captured_piece, 0) * 10
        
        # Undo move
        board[move['from']] = saved_from
        board[move['to']] = saved_to
        
        # Positional bonus: advance pieces (push toward opponent's king)
        piece = move['piece']
        direction = 1 if self.color == 'W' else -1  # White advances right, Black advances left
        if piece.upper() != 'K':  # Don't push king too far
            advancement = (move['to'] - move['from']) * direction
            if advancement > 0:
                score += advancement * 2
        
        # Bonus for moving knight toward center or attacking
        if piece.upper() == 'N':
            score += 1
        
        # Small random factor to add variety
        score += random.random() * 0.5
    
    def _is_checkmate(self, board):
        """Check if the opponent is in checkmate."""
        opponent_color = 'B' if self.color == 'W' else 'W'
        return self._is_king_under_attack(board, self._find_king(board, opponent_color), opponent_color) and not self._has_legal_moves(board, opponent_color)
    
    def _is_opponent_in_check(self, board):
        """Check if opponent's king is in check."""
        opponent_color = 'B' if self.color == 'W' else 'W'
        return self._is_king_under_attack(board, self._find_king(board, opponent_color), opponent_color)
    
    def _has_legal_moves(self, board, color):
        """Check if color has any legal moves."""
        for pos in range(8):
            piece = board[pos]
            if piece and ((color == 'W' and piece in ('K', 'N', 'R')) or (color == 'B' and piece in ('k', 'n', 'r'))):
                moves = self._get_piece_legal_moves(board, pos, piece)
                if moves:
                    return True
        return False
