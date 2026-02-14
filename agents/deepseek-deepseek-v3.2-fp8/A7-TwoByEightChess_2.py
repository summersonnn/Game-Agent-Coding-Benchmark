"""
Agent Code: A7-TwoByEightChess
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-14 14:18:27
"""

from copy import deepcopy

import random
from copy import deepcopy

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
        self.opponent_color = 'B' if color == 'W' else 'W'
        
        # Piece values for evaluation
        self.piece_values = {
            'K': 1000, 'k': 1000,
            'R': 5, 'r': 5,
            'N': 3, 'n': 3,
            'P': 1, 'p': 1
        }
        
        # Positional bonuses for different pieces
        # For this small board, controlling center columns (d,e) is important
        self.position_bonus = {
            'K': [0, 0, 0, 1, 1, 0, 0, 0],  # King safety
            'R': [0, 1, 2, 3, 3, 2, 1, 0],  # Rook mobility
            'N': [0, 2, 3, 4, 4, 3, 2, 0],  # Knight centralization
            'P': [0, 1, 2, 3, 3, 2, 1, 0],  # Pawn advancement
            'k': [0, 0, 0, 1, 1, 0, 0, 0],
            'r': [0, 1, 2, 3, 3, 2, 1, 0],
            'n': [0, 2, 3, 4, 4, 3, 2, 0],
            'p': [0, 1, 2, 3, 3, 2, 1, 0]
        }

    def _in_bounds(self, row, col):
        """Check if position is within board bounds."""
        return 0 <= row < 2 and 0 <= col < 8

    def _is_own_piece(self, piece):
        """Check if piece belongs to the agent."""
        if not piece:
            return False
        if self.color == 'W':
            return piece.isupper()
        else:
            return piece.islower()

    def _is_enemy_piece(self, piece):
        """Check if piece belongs to opponent."""
        if not piece:
            return False
        if self.color == 'W':
            return piece.islower()
        else:
            return piece.isupper()

    def _get_piece_moves(self, board, row, col):
        """Get all possible moves for a piece at (row, col)."""
        piece = board[row][col]
        if not piece or not self._is_own_piece(piece):
            return []
        
        moves = []
        piece_type = piece.upper()
        
        if piece_type == 'K':  # King
            # King moves 1 square in any direction
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not target or self._is_enemy_piece(target):
                            moves.append((nr, nc, bool(target)))
        
        elif piece_type == 'N':  # Knight
            # Standard L-shaped knight moves
            knight_moves = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                           (-2, -1), (-2, 1), (2, -1), (2, 1)]
            for dr, dc in knight_moves:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not target or self._is_enemy_piece(target):
                        moves.append((nr, nc, bool(target)))
            
            # Linear jump (2 squares horizontally)
            for dc in [-2, 2]:
                nc = col + dc
                if 0 <= nc < 8:
                    target = board[row][nc]
                    if not target or self._is_enemy_piece(target):
                        moves.append((row, nc, bool(target)))
        
        elif piece_type == 'R':  # Rook
            # Horizontal moves
            for dc in [-1, 1]:
                nc = col + dc
                while 0 <= nc < 8:
                    target = board[row][nc]
                    if not target:
                        moves.append((row, nc, False))
                    elif self._is_enemy_piece(target):
                        moves.append((row, nc, True))
                        break
                    else:
                        break
                    nc += dc
            
            # Vertical moves (only 1 square up or down)
            for dr in [-1, 1]:
                nr = row + dr
                if self._in_bounds(nr, col):
                    target = board[nr][col]
                    if not target or self._is_enemy_piece(target):
                        moves.append((nr, col, bool(target)))
        
        elif piece_type == 'P':  # Pawn
            direction = 1 if self.color == 'W' else -1
            nc = col + direction
            
            # Forward move
            if 0 <= nc < 8 and not board[row][nc]:
                moves.append((row, nc, False))
            
            # Diagonal captures
            for dr in [-1, 1]:
                nr = row + dr
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target and self._is_enemy_piece(target):
                        moves.append((nr, nc, True))
        
        return moves

    def _is_in_check(self, board, color):
        """Check if king of given color is in check."""
        king_pos = None
        # Find king
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and ((color == 'W' and piece == 'K') or (color == 'B' and piece == 'k')):
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
        
        # Check if any enemy piece attacks the king
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and ((color == 'W' and piece.islower()) or (color == 'B' and piece.isupper())):
                    moves = self._get_piece_moves(board, r, c)
                    for nr, nc, _ in moves:
                        if (nr, nc) == king_pos:
                            return True
        return False

    def _is_move_safe(self, board, from_pos, to_pos):
        """Check if move doesn't leave king in check."""
        r1, c1 = from_pos
        r2, c2 = to_pos
        
        # Make a copy and simulate the move
        new_board = [row[:] for row in board]
        piece = new_board[r1][c1]
        new_board[r2][c2] = piece
        new_board[r1][c1] = ''
        
        # Check for pawn promotion
        if piece.upper() == 'P':
            if (self.color == 'W' and c2 == 7) or (self.color == 'B' and c2 == 0):
                new_board[r2][c2] = 'R' if self.color == 'W' else 'r'
        
        # Check if king is in check after move
        return not self._is_in_check(new_board, self.color)

    def _get_all_valid_moves(self, board):
        """Get all valid moves for current player."""
        moves = []
        
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece):
                    piece_moves = self._get_piece_moves(board, r, c)
                    for nr, nc, is_capture in piece_moves:
                        if self._is_move_safe(board, (r, c), (nr, nc)):
                            from_sq = f"{'abcdefgh'[c]}{r+1}"
                            to_sq = f"{'abcdefgh'[nc]}{nr+1}"
                            piece_type = piece.upper()
                            
                            if is_capture:
                                move_str = f"{piece_type}{from_sq}x{to_sq}"
                            else:
                                move_str = f"{piece_type}{from_sq}{to_sq}"
                            
                            moves.append((move_str, (r, c), (nr, nc), piece, board[nr][nc]))
        
        return moves

    def _evaluate_board(self, board):
        """Evaluate the board position."""
        score = 0
        
        # Material evaluation
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    value = self.piece_values[piece]
                    pos_bonus = self.position_bonus[piece][c]
                    
                    if self._is_own_piece(piece):
                        score += value + pos_bonus * 0.1
                    else:
                        score -= value + pos_bonus * 0.1
        
        # Check bonus/penalty
        if self._is_in_check(board, self.color):
            score -= 5
        if self._is_in_check(board, self.opponent_color):
            score += 5
        
        # Mobility bonus
        my_moves = len(self._get_all_valid_moves(board))
        
        # Temporarily switch perspective to count opponent moves
        temp_color = self.color
        self.color = self.opponent_color
        opp_moves = len(self._get_all_valid_moves(board))
        self.color = temp_color
        
        score += (my_moves - opp_moves) * 0.1
        
        # Pawn advancement bonus (encourage pawns to promote)
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and piece.upper() == 'P':
                    if self._is_own_piece(piece):
                        if self.color == 'W':
                            advancement = c  # columns a=0 to h=7
                        else:
                            advancement = 7 - c  # columns h=7 to a=0
                        score += advancement * 0.2
        
        return score

    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning."""
        if depth == 0:
            return self._evaluate_board(board), None
        
        moves = self._get_all_valid_moves(board)
        
        if not moves:
            # Checkmate or stalemate
            if self._is_in_check(board, self.color):
                return -1000 if maximizing_player else 1000, None
            else:
                return 0, None
        
        best_move = None
        
        if maximizing_player:
            max_eval = float('-inf')
            for move_str, from_pos, to_pos, piece, captured in moves:
                # Make move on copy
                new_board = [row[:] for row in board]
                r1, c1 = from_pos
                r2, c2 = to_pos
                new_board[r2][c2] = piece
                new_board[r1][c1] = ''
                
                # Pawn promotion
                if piece.upper() == 'P':
                    if (self.color == 'W' and c2 == 7) or (self.color == 'B' and c2 == 0):
                        new_board[r2][c2] = 'R' if self.color == 'W' else 'r'
                
                # Switch perspective for next ply
                temp_color = self.color
                self.color = self.opponent_color
                eval_score, _ = self._minimax(new_board, depth-1, alpha, beta, False)
                self.color = temp_color
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move_str
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move_str, from_pos, to_pos, piece, captured in moves:
                new_board = [row[:] for row in board]
                r1, c1 = from_pos
                r2, c2 = to_pos
                new_board[r2][c2] = piece
                new_board[r1][c1] = ''
                
                if piece.upper() == 'P':
                    if (self.color == 'W' and c2 == 7) or (self.color == 'B' and c2 == 0):
                        new_board[r2][c2] = 'R' if self.color == 'W' else 'r'
                
                temp_color = self.color
                self.color = self.opponent_color
                eval_score, _ = self._minimax(new_board, depth-1, alpha, beta, True)
                self.color = temp_color
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move_str
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move

    def make_move(self, board, move_history):
        """
        Decide the next move based on the current board state.
        
        Args:
            board: list[list[str]] - 2x8 board (2 rows, 8 columns).
                   board[0] = row 1, board[1] = row 2.
                   Pieces: 'K','N','R','P' (White), 'k','n','r','p' (Black), '' (empty)
            move_history: list[str] - List of all moves played so far.
            
        Returns:
            str: Move in notation format.
        """
        # Get all valid moves
        all_moves = self._get_all_valid_moves(board)
        
        if not all_moves:
            # No legal moves (shouldn't happen as engine handles this)
            return ""
        
        # Check for immediate wins
        for move_str, from_pos, to_pos, piece, captured in all_moves:
            # Make the move on a copy
            new_board = [row[:] for row in board]
            r1, c1 = from_pos
            r2, c2 = to_pos
            new_board[r2][c2] = piece
            new_board[r1][c1] = ''
            
            # Pawn promotion
            if piece.upper() == 'P':
                if (self.color == 'W' and c2 == 7) or (self.color == 'B' and c2 == 0):
                    new_board[r2][c2] = 'R' if self.color == 'W' else 'r'
            
            # Check if this move gives checkmate
            if self._is_in_check(new_board, self.opponent_color):
                # Check if opponent has any legal moves
                temp_color = self.color
                self.color = self.opponent_color
                opponent_moves = self._get_all_valid_moves(new_board)
                self.color = temp_color
                
                if not opponent_moves:
                    return move_str
        
        # Check for captures, especially valuable pieces
        capture_moves = []
        for move_str, from_pos, to_pos, piece, captured in all_moves:
            if captured:
                # Prioritize capturing higher value pieces
                if captured.upper() in ['R', 'N', 'P']:
                    capture_value = self.piece_values[captured]
                    capture_moves.append((move_str, capture_value))
        
        if capture_moves:
            # Sort by capture value (highest first)
            capture_moves.sort(key=lambda x: x[1], reverse=True)
            # Check if the capture is safe
            for move_str, value in capture_moves:
                # Parse move to get positions
                if 'x' in move_str:
                    parts = move_str.split('x')
                    from_sq = parts[0][1:]
                    to_sq = parts[1]
                else:
                    from_sq = move_str[1:3]
                    to_sq = move_str[3:]
                
                from_col = ord(from_sq[0]) - ord('a')
                from_row = int(from_sq[1]) - 1
                to_col = ord(to_sq[0]) - ord('a')
                to_row = int(to_sq[1]) - 1
                
                if self._is_move_safe(board, (from_row, from_col), (to_row, to_col)):
                    return move_str
        
        # Use minimax for deeper search
        # Adjust depth based on game phase
        if len(move_history) < 4:
            depth = 3  # Opening: shallower search
        elif len(move_history) < 12:
            depth = 4  # Middlegame: medium depth
        else:
            depth = 5  # Endgame: deeper search
        
        _, best_move = self._minimax(board, depth, float('-inf'), float('inf'), True)
        
        if best_move:
            return best_move
        
        # Fallback: return a random safe move
        safe_moves = []
        for move_str, from_pos, to_pos, piece, captured in all_moves:
            if self._is_move_safe(board, from_pos, to_pos):
                safe_moves.append(move_str)
        
        if safe_moves:
            return random.choice(safe_moves)
        
        # Last resort: return first move
        return all_moves[0][0]
