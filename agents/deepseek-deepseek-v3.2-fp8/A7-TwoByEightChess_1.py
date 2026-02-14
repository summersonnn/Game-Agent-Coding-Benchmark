"""
Agent Code: A7-TwoByEightChess
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 1
Generated: 2026-02-14 13:30:59
"""

import time

import random
import time

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color  # 'W' or 'B'
        self.opponent_color = 'B' if color == 'W' else 'W'
        self.max_depth = 5  # Search depth for minimax
        self.time_limit = 0.8  # Seconds per move
        
        # Piece values (based on standard chess, adjusted for 2x8)
        self.piece_values = {
            'K': 10000, 'k': 10000,  # King - very high value
            'R': 5, 'r': 5,           # Rook
            'N': 3, 'n': 3,           # Knight
            'P': 1, 'p': 1            # Pawn
        }
        
        # Positional bonuses for each piece type
        # For White (reverse for Black)
        self.position_bonus = {
            'K': [  # King - stay safe in corners initially
                [-1, -1, -1, -1, -1, -1, -1, -1],
                [ 0,  0,  0,  0,  0,  0,  0,  0]
            ],
            'R': [  # Rook - control center and edges
                [ 1,  0,  0,  0,  0,  0,  0,  1],
                [ 0,  0,  0,  0,  0,  0,  0,  0]
            ],
            'N': [  # Knight - control center
                [ 0,  0,  0,  1,  1,  0,  0,  0],
                [ 0,  0,  1,  2,  2,  1,  0,  0]
            ],
            'P': [  # Pawn - advance toward promotion
                [ 0,  0,  0,  0,  0,  0,  0,  0],
                [ 1,  1,  1,  1,  1,  1,  1,  1]
            ]
        }

    def make_move(self, board, move_history):
        # Start timing
        start_time = time.time()
        
        # Get all legal moves
        legal_moves = self._get_all_legal_moves(board)
        
        if not legal_moves:
            return random.choice(self._generate_random_move(board))
        
        # Sort moves for better alpha-beta pruning
        sorted_moves = self._sort_moves(board, legal_moves)
        
        best_move = None
        best_value = float('-inf')
        
        # Iterative deepening with time limit
        for depth in range(1, self.max_depth + 1):
            if time.time() - start_time > self.time_limit:
                break
                
            current_best = None
            current_value = float('-inf')
            
            for move in sorted_moves:
                # Create new board state
                new_board = self._make_move_on_board(board, move)
                
                # Evaluate with minimax
                value = self._minimax(new_board, depth - 1, float('-inf'), float('inf'), False, start_time)
                
                if value > current_value:
                    current_value = value
                    current_best = move
                    
                # Check time
                if time.time() - start_time > self.time_limit:
                    break
            
            if current_best:
                best_move = current_best
                best_value = current_value
        
        # Fallback if no move found
        if best_move is None:
            best_move = sorted_moves[0] if sorted_moves else random.choice(legal_moves)
        
        return best_move
    
    def _minimax(self, board, depth, alpha, beta, maximizing_player, start_time):
        # Check terminal conditions or depth limit
        if depth == 0 or time.time() - start_time > self.time_limit:
            return self._evaluate_board(board)
        
        # Check game state
        game_state = self._get_game_state(board)
        if game_state != 'ongoing':
            return self._evaluate_terminal(game_state)
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in self._get_all_legal_moves(board):
                new_board = self._make_move_on_board(board, move)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, False, start_time)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in self._get_all_legal_moves(board):
                new_board = self._make_move_on_board(board, move)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True, start_time)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    def _evaluate_board(self, board):
        """Evaluate board position from perspective of our agent."""
        if self.color == 'B':
            # Flip evaluation for black
            return -self._evaluate_board_for_color(board, 'W')
        
        score = 0
        
        # Material score
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece:
                    value = self.piece_values[piece]
                    if piece.isupper():  # White piece
                        score += value
                        # Positional bonus
                        if piece.upper() in self.position_bonus:
                            bonus = self.position_bonus[piece.upper()][row][col]
                            score += bonus * 0.1
                    else:  # Black piece
                        score -= value
                        # Positional bonus (reverse for black)
                        if piece.upper() in self.position_bonus:
                            bonus = self.position_bonus[piece.upper()][1 - row][7 - col]
                            score -= bonus * 0.1
        
        # King safety
        white_king_pos = self._find_king(board, 'W')
        black_king_pos = self._find_king(board, 'B')
        
        if white_king_pos:
            # Penalize white king being in center
            col = white_king_pos[1]
            if 2 <= col <= 5:
                score -= 0.5
        
        if black_king_pos:
            # Bonus for attacking black king
            col = black_king_pos[1]
            if 2 <= col <= 5:
                score += 0.5
        
        # Pawn advancement bonus
        for col in range(8):
            piece = board[0][col]  # Row 1
            if piece == 'P':
                score += col * 0.3  # White pawns advance right
            elif piece == 'p':
                score -= (7 - col) * 0.3  # Black pawns advance left
        
        # Piece activity
        white_moves = self._count_legal_moves(board, 'W')
        black_moves = self._count_legal_moves(board, 'B')
        score += (white_moves - black_moves) * 0.1
        
        return score
    
    def _evaluate_board_for_color(self, board, color):
        """Helper to evaluate board for specific color."""
        score = 0
        
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece:
                    value = self.piece_values[piece]
                    if (color == 'W' and piece.isupper()) or (color == 'B' and piece.islower()):
                        score += value
                    else:
                        score -= value
        
        return score
    
    def _evaluate_terminal(self, game_state):
        """Evaluate terminal game states."""
        if game_state == 'white_wins':
            return 10000 if self.color == 'W' else -10000
        elif game_state == 'black_wins':
            return -10000 if self.color == 'W' else 10000
        else:  # Draw states
            return 0
    
    def _get_game_state(self, board):
        """Check game state without full engine."""
        # Quick checks
        white_king = self._find_king(board, 'W')
        black_king = self._find_king(board, 'B')
        
        if not white_king or not black_king:
            return 'black_wins' if not white_king else 'white_wins'
        
        # Check for insufficient material
        if self._is_insufficient_material(board):
            return 'draw_material'
        
        # For simplicity, assume ongoing
        return 'ongoing'
    
    def _is_insufficient_material(self, board):
        """Check if only kings remain."""
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.upper() != 'K':
                    return False
        return True
    
    def _find_king(self, board, color):
        """Find king position for given color."""
        king = 'K' if color == 'W' else 'k'
        for row in range(2):
            for col in range(8):
                if board[row][col] == king:
                    return (row, col)
        return None
    
    def _get_all_legal_moves(self, board):
        """Generate all legal moves for current player."""
        moves = []
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece and ((self.color == 'W' and piece.isupper()) or 
                             (self.color == 'B' and piece.islower())):
                    moves.extend(self._get_moves_for_piece(board, row, col))
        return moves
    
    def _get_moves_for_piece(self, board, row, col):
        """Get legal moves for a specific piece."""
        piece = board[row][col]
        moves = []
        
        if piece.upper() == 'K':
            # King moves
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if not target or (self.color == 'W' and target.islower()) or \
                           (self.color == 'B' and target.isupper()):
                            moves.append(self._format_move(piece, row, col, nr, nc, bool(target)))
        
        elif piece.upper() == 'N':
            # Knight moves (L-shape + linear jump)
            # L-shape moves
            l_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]
            for dr, dc in l_moves:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target or (self.color == 'W' and target.islower()) or \
                       (self.color == 'B' and target.isupper()):
                        moves.append(self._format_move(piece, row, col, nr, nc, bool(target)))
            
            # Linear jump (2 squares horizontally)
            if col - 2 >= 0:
                target = board[row][col - 2]
                if not target or (self.color == 'W' and target.islower()) or \
                   (self.color == 'B' and target.isupper()):
                    moves.append(self._format_move(piece, row, col, row, col - 2, bool(target)))
            if col + 2 < 8:
                target = board[row][col + 2]
                if not target or (self.color == 'W' and target.islower()) or \
                   (self.color == 'B' and target.isupper()):
                    moves.append(self._format_move(piece, row, col, row, col + 2, bool(target)))
        
        elif piece.upper() == 'R':
            # Rook moves
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target:
                        if (self.color == 'W' and target.islower()) or \
                           (self.color == 'B' and target.isupper()):
                            moves.append(self._format_move(piece, row, col, nr, nc, True))
                        break
                    else:
                        moves.append(self._format_move(piece, row, col, nr, nc, False))
                    nr += dr
                    nc += dc
        
        elif piece.upper() == 'P':
            # Pawn moves
            direction = 1 if piece == 'P' else -1  # White moves right, black moves left
            
            # Forward move
            nc = col + direction
            if 0 <= nc < 8 and not board[row][nc]:
                moves.append(self._format_move(piece, row, col, row, nc, False))
            
            # Diagonal captures
            for dr in [-1, 1]:
                nr = row + dr
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target and ((self.color == 'W' and target.islower()) or 
                                  (self.color == 'B' and target.isupper())):
                        moves.append(self._format_move(piece, row, col, nr, nc, True))
        
        return moves
    
    def _format_move(self, piece, from_row, from_col, to_row, to_col, is_capture):
        """Format move in required notation."""
        cols = 'abcdefgh'
        from_sq = f"{cols[from_col]}{from_row + 1}"
        to_sq = f"{cols[to_col]}{to_row + 1}"
        
        piece_type = piece.upper()
        if is_capture:
            return f"{piece_type}{from_sq}x{to_sq}"
        else:
            return f"{piece_type}{from_sq}{to_sq}"
    
    def _make_move_on_board(self, board, move_str):
        """Make a move on a copy of the board."""
        # Parse move
        if 'x' in move_str:
            piece_type, rest = move_str[0], move_str[1:]
            from_sq, to_sq = rest.split('x')
            is_capture = True
        else:
            piece_type = move_str[0]
            from_sq = move_str[1:3]
            to_sq = move_str[3:5]
            is_capture = False
        
        # Convert squares to coordinates
        cols = 'abcdefgh'
        from_col = cols.index(from_sq[0])
        from_row = int(from_sq[1]) - 1
        to_col = cols.index(to_sq[0])
        to_row = int(to_sq[1]) - 1
        
        # Create board copy
        new_board = [row[:] for row in board]
        
        # Get piece (handle case sensitivity)
        piece = new_board[from_row][from_col]
        if piece.upper() != piece_type:
            # Try to find correct case
            if self.color == 'W':
                piece = piece_type
            else:
                piece = piece_type.lower()
        
        # Make move
        new_board[to_row][to_col] = piece
        new_board[from_row][from_col] = ''
        
        # Handle pawn promotion
        if piece.upper() == 'P':
            if (piece == 'P' and to_col == 7) or (piece == 'p' and to_col == 0):
                new_board[to_row][to_col] = 'R' if piece == 'P' else 'r'
        
        return new_board
    
    def _sort_moves(self, board, moves):
        """Sort moves for better alpha-beta pruning (captures first)."""
        def move_score(move):
            score = 0
            # Prioritize captures
            if 'x' in move:
                # Estimate captured piece value
                to_sq = move.split('x')[1]
                cols = 'abcdefgh'
                to_col = cols.index(to_sq[0])
                to_row = int(to_sq[1]) - 1
                captured = board[to_row][to_col]
                if captured:
                    score += self.piece_values[captured]
            
            # Prioritize checks (simplified)
            if move[0].upper() == 'K':
                score -= 100  # King moves less important initially
            
            # Prioritize pawn advancement
            if move[0].upper() == 'P':
                from_sq = move[1:3]
                to_sq = move[4:6] if 'x' in move else move[3:5]
                from_col = cols.index(from_sq[0])
                to_col = cols.index(to_sq[0])
                if abs(to_col - from_col) > 0:  # Capture or advancement
                    score += 10
            
            return -score  # Negative for descending sort
        
        return sorted(moves, key=move_score)
    
    def _count_legal_moves(self, board, color):
        """Count legal moves for a color (simplified)."""
        count = 0
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece and ((color == 'W' and piece.isupper()) or 
                             (color == 'B' and piece.islower())):
                    count += len(self._get_moves_for_piece_simple(board, row, col, color))
        return count
    
    def _get_moves_for_piece_simple(self, board, row, col, color):
        """Simple move generation for counting."""
        piece = board[row][col]
        moves = []
        
        if piece.upper() == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        moves.append((nr, nc))
        
        elif piece.upper() == 'N':
            l_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]
            for dr, dc in l_moves:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    moves.append((nr, nc))
            
            if col - 2 >= 0:
                moves.append((row, col - 2))
            if col + 2 < 8:
                moves.append((row, col + 2))
        
        elif piece.upper() == 'R':
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    moves.append((nr, nc))
                    if board[nr][nc]:
                        break
                    nr += dr
                    nc += dc
        
        elif piece.upper() == 'P':
            direction = 1 if piece == 'P' else -1
            nc = col + direction
            if 0 <= nc < 8:
                moves.append((row, nc))
                for dr in [-1, 1]:
                    nr = row + dr
                    if 0 <= nr < 2:
                        moves.append((nr, nc))
        
        return moves
    
    def _generate_random_move(self, board):
        """Fallback: generate random valid move."""
        moves = []
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece and ((self.color == 'W' and piece.isupper()) or 
                             (self.color == 'B' and piece.islower())):
                    piece_moves = self._get_moves_for_piece(board, row, col)
                    moves.extend(piece_moves)
        return moves if moves else ["Ka2b2"]  # Default fallback
