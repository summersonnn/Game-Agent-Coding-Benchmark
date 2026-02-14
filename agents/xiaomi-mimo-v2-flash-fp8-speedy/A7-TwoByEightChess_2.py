"""
Agent Code: A7-TwoByEightChess
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 2
Generated: 2026-02-14 14:14:44
"""

import copy

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
        
        # Piece values for evaluation
        self.piece_values = {
            'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1,
            'k': 0, 'q': -9, 'r': -5, 'b': -3, 'n': -3, 'p': -1
        }
        
        # Position bonuses (row, col) - encourage centralization
        self.position_bonus = {
            'K': [[0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0]],
            'N': [[-1, 0, 0, 0, 0, 0, 0, -1],
                  [-1, 0, 0, 0, 0, 0, 0, -1]],
            'R': [[0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0]],
            'P': [[0, 0, 0, 1, 1, 0, 0, 0],
                  [0, 0, 0, 1, 1, 0, 0, 0]]
        }

    def make_move(self, board, move_history):
        """
        Decide the next move based on the current board state.

        Args:
            board: list[list[str]] - 2x8 board (2 rows, 8 columns).
                   board[0] = row 1, board[1] = row 2.
            move_history: list[str] - List of all moves played so far.

        Returns:
            str: Move in notation format.
        """
        # Get all valid moves for current player
        valid_moves = self.get_all_valid_moves(board, self.color)
        
        if not valid_moves:
            # No valid moves - should not happen in normal play
            return "Ka2b2"  # Default move
        
        # Evaluate each move and choose the best one
        best_move = None
        best_score = -float('inf')
        
        for move in valid_moves:
            # Create a copy of the board to simulate the move
            test_board = copy.deepcopy(board)
            success = self.simulate_move(test_board, move, self.color)
            
            if not success:
                continue
                
            # Evaluate the resulting position
            score = self.evaluate_position(test_board, self.color)
            
            # Add bonus for capturing
            if 'x' in move:
                score += 2.0
                
            # Add bonus for checking
            if self.is_check(test_board, self.get_opponent_color(self.color)):
                score += 1.5
                
            # Add small bonus for advancing pawns
            if move[0] == 'P':
                score += 0.1
                
            if score > best_score:
                best_score = score
                best_move = move
        
        # If no good move found, use a fallback strategy
        if best_move is None:
            # Try to capture if possible
            capture_moves = [m for m in valid_moves if 'x' in m]
            if capture_moves:
                best_move = random.choice(capture_moves)
            else:
                # Try to move a pawn forward
                pawn_moves = [m for m in valid_moves if m[0] == 'P']
                if pawn_moves:
                    best_move = random.choice(pawn_moves)
                else:
                    # Fallback to any move
                    best_move = random.choice(valid_moves)
        
        return best_move

    def get_all_valid_moves(self, board, color):
        """Generate all valid moves for the given color."""
        moves = []
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece and self.is_own_piece(piece, color):
                    piece_moves = self.get_moves_for_piece(board, row, col, piece, color)
                    moves.extend(piece_moves)
        return moves

    def get_moves_for_piece(self, board, row, col, piece, color):
        """Get all valid moves for a specific piece."""
        piece_type = piece.upper()
        moves = []
        
        if piece_type == 'K':
            # King moves one square in any direction
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self.is_valid_square(nr, nc):
                        target = board[nr][nc]
                        if not self.is_own_piece(target, color):
                            move = self.format_move('K', row, col, nr, nc, target)
                            moves.append(move)
                            
        elif piece_type == 'N':
            # Knight moves: L-shape and linear 2-square jump
            # L-shape moves
            l_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]
            # Linear 2-square jump
            linear_moves = [(0, -2), (0, 2)]
            
            for dr, dc in l_moves + linear_moves:
                nr, nc = row + dr, col + dc
                if self.is_valid_square(nr, nc):
                    target = board[nr][nc]
                    if not self.is_own_piece(target, color):
                        move = self.format_move('N', row, col, nr, nc, target)
                        moves.append(move)
                        
        elif piece_type == 'R':
            # Rook moves: horizontal and vertical
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while self.is_valid_square(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        move = self.format_move('R', row, col, nr, nc, target)
                        moves.append(move)
                    elif not self.is_own_piece(target, color):
                        move = self.format_move('R', row, col, nr, nc, target)
                        moves.append(move)
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
                    
        elif piece_type == 'P':
            # Pawn moves: forward and diagonal capture
            direction = 1 if color == 'W' else -1
            
            # Forward move
            nc = col + direction
            if self.is_valid_square(row, nc) and board[row][nc] == '':
                move = self.format_move('P', row, col, row, nc, '')
                moves.append(move)
                
            # Diagonal captures
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self.is_valid_square(nr, nc):
                    target = board[nr][nc]
                    if target and not self.is_own_piece(target, color):
                        move = self.format_move('P', row, col, nr, nc, target)
                        moves.append(move)
        
        # Filter moves that would leave own king in check
        valid_moves = []
        for move in moves:
            if not self.would_be_in_check(board, move, color):
                valid_moves.append(move)
                
        return valid_moves

    def is_valid_square(self, row, col):
        """Check if coordinates are within board bounds."""
        return 0 <= row < 2 and 0 <= col < 8

    def is_own_piece(self, piece, color):
        """Check if a piece belongs to the current player."""
        if not piece:
            return False
        if color == 'W':
            return piece.isupper()
        else:
            return piece.islower()

    def get_opponent_color(self, color):
        """Get opponent's color."""
        return 'B' if color == 'W' else 'W'

    def format_move(self, piece_type, from_row, from_col, to_row, to_col, target):
        """Format move in standard notation."""
        from_sq = f"{'abcdefgh'[from_col]}{from_row + 1}"
        to_sq = f"{'abcdefgh'[to_col]}{to_row + 1}"
        
        if target:
            return f"{piece_type}{from_sq}x{to_sq}"
        else:
            return f"{piece_type}{from_sq}{to_sq}"

    def simulate_move(self, board, move, color):
        """Simulate a move on the board (without validation)."""
        # Parse move
        if 'x' in move:
            # Capture move
            piece = move[0]
            from_sq = move[1:3]
            to_sq = move[3:5]
        else:
            # Regular move
            piece = move[0]
            from_sq = move[1:3]
            to_sq = move[3:5]
        
        # Convert squares to coordinates
        from_col = ord(from_sq[0]) - ord('a')
        from_row = int(from_sq[1]) - 1
        to_col = ord(to_sq[0]) - ord('a')
        to_row = int(to_sq[1]) - 1
        
        # Move the piece
        board[to_row][to_col] = board[from_row][from_col]
        board[from_row][from_col] = ''
        
        # Handle pawn promotion
        if piece == 'P':
            if (color == 'W' and to_col == 7) or (color == 'B' and to_col == 0):
                board[to_row][to_col] = 'R' if color == 'W' else 'r'
        
        return True

    def would_be_in_check(self, board, move, color):
        """Check if making this move would leave own king in check."""
        # Create a copy and simulate
        test_board = copy.deepcopy(board)
        self.simulate_move(test_board, move, color)
        return self.is_in_check(test_board, color)

    def is_in_check(self, board, color):
        """Check if the given color's king is in check."""
        king_pos = self.find_king(board, color)
        if not king_pos:
            return False
            
        opponent_color = self.get_opponent_color(color)
        
        # Check if any opponent piece attacks the king
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece and self.is_own_piece(piece, opponent_color):
                    # Get attacks from this piece
                    attacks = self.get_attacks_from_square(board, row, col, piece, opponent_color)
                    if king_pos in attacks:
                        return True
        return False

    def is_check(self, board, color):
        """Alias for is_in_check."""
        return self.is_in_check(board, color)

    def find_king(self, board, color):
        """Find the position of the king for the given color."""
        king = 'K' if color == 'W' else 'k'
        for row in range(2):
            for col in range(8):
                if board[row][col] == king:
                    return (row, col)
        return None

    def get_attacks_from_square(self, board, row, col, piece, color):
        """Get all squares attacked by a piece (without checking for check)."""
        piece_type = piece.upper()
        attacks = set()
        
        if piece_type == 'K':
            # King attacks one square in any direction
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self.is_valid_square(nr, nc):
                        attacks.add((nr, nc))
                        
        elif piece_type == 'N':
            # Knight attacks
            l_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]
            linear_moves = [(0, -2), (0, 2)]
            
            for dr, dc in l_moves + linear_moves:
                nr, nc = row + dr, col + dc
                if self.is_valid_square(nr, nc):
                    attacks.add((nr, nc))
                    
        elif piece_type == 'R':
            # Rook attacks
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while self.is_valid_square(nr, nc):
                    attacks.add((nr, nc))
                    if board[nr][nc] != '':
                        break
                    nr += dr
                    nc += dc
                    
        elif piece_type == 'P':
            # Pawn attacks (diagonal)
            direction = 1 if color == 'W' else -1
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self.is_valid_square(nr, nc):
                    attacks.add((nr, nc))
        
        return attacks

    def evaluate_position(self, board, color):
        """Evaluate the position from the perspective of the given color."""
        score = 0.0
        
        # Material count
        material = 0
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece:
                    value = self.piece_values.get(piece, 0)
                    if color == 'W':
                        material += value
                    else:
                        material -= value
        score += material * 10.0
        
        # Positional bonuses
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece:
                    piece_type = piece.upper()
                    if piece_type in self.position_bonus:
                        bonus = self.position_bonus[piece_type][row][col]
                        if piece.isupper() == (color == 'W'):
                            score += bonus * 0.1
                        else:
                            score -= bonus * 0.1
        
        # King safety
        king_pos = self.find_king(board, color)
        if king_pos:
            # Bonus for king being in center
            if 2 <= king_pos[1] <= 5:
                score += 0.2
            else:
                score -= 0.1
        
        # Mobility (number of legal moves)
        mobility = len(self.get_all_valid_moves(board, color))
        score += mobility * 0.05
        
        # Check bonus/penalty
        if self.is_in_check(board, color):
            score -= 2.0
        if self.is_in_check(board, self.get_opponent_color(color)):
            score += 1.5
        
        return score
