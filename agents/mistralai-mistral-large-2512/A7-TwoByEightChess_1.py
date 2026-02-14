"""
Agent Code: A7-TwoByEightChess
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-14 13:17:43
"""

from collections import defaultdict

import random
from collections import defaultdict

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.piece_values = {
            'K': 100, 'k': 100,
            'N': 3, 'n': 3,
            'R': 5, 'r': 5,
            'P': 1, 'p': 1
        }
        self.opponent_color = 'B' if color == 'W' else 'W'

        # Directions for piece movement evaluation
        self.directions = {
            'K': [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)],
            'N': [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1), (0,-2), (0,2)],
            'R': [(-1,0), (1,0), (0,-1), (0,1)],
            'P': [(0,1)] if color == 'W' else [(0,-1)]  # Forward direction
        }

    def make_move(self, board, move_history):
        # Get all valid moves
        valid_moves = self._get_all_valid_moves(board)

        if not valid_moves:
            return "Ka2a1"  # Shouldn't happen as game would be over

        # Evaluate all moves and choose the best one
        best_move = self._evaluate_moves(board, valid_moves)

        return best_move

    def _get_all_valid_moves(self, board):
        """Get all valid moves for the current player on the given board."""
        valid_moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue

                # Check if it's our piece
                if (self.color == 'W' and piece.isupper()) or (self.color == 'B' and piece.islower()):
                    piece_type = piece.upper()
                    from_sq = self._pos_to_notation(r, c)

                    # Get possible moves for this piece
                    moves = self._get_piece_moves(board, r, c, piece_type)
                    for (tr, tc), is_capture in moves:
                        to_sq = self._pos_to_notation(tr, tc)
                        if is_capture:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        valid_moves.append(move_str)
        return valid_moves

    def _get_piece_moves(self, board, row, col, piece_type):
        """Get all valid moves for a specific piece at (row, col)."""
        moves = []
        piece = board[row][col]
        color = 'W' if piece.isupper() else 'B'

        if piece_type == 'K':
            # King moves
            for dr, dc in self.directions['K']:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target or (color == 'W' and target.islower()) or (color == 'B' and target.isupper()):
                        is_capture = target != ''
                        moves.append(((nr, nc), is_capture))

        elif piece_type == 'N':
            # Knight moves (L-shape + linear jumps)
            for dr, dc in self.directions['N']:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target or (color == 'W' and target.islower()) or (color == 'B' and target.isupper()):
                        is_capture = target != ''
                        moves.append(((nr, nc), is_capture))

        elif piece_type == 'R':
            # Rook moves
            for dr, dc in self.directions['R']:
                nr, nc = row + dr, col + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target:
                        moves.append(((nr, nc), False))
                    elif (color == 'W' and target.islower()) or (color == 'B' and target.isupper()):
                        moves.append(((nr, nc), True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif piece_type == 'P':
            # Pawn moves
            direction = 1 if color == 'W' else -1
            # Forward move
            nc = col + direction
            if 0 <= nc < 8 and board[row][nc] == '':
                moves.append(((row, nc), False))
                # Check for promotion
                if (color == 'W' and nc == 7) or (color == 'B' and nc == 0):
                    # Promotion to Rook is automatic, so no special handling needed
                    pass
            # Diagonal captures
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target and ((color == 'W' and target.islower()) or (color == 'B' and target.isupper())):
                        moves.append(((nr, nc), True))
                        # Check for promotion
                        if (color == 'W' and nc == 7) or (color == 'B' and nc == 0):
                            pass

        # Filter out moves that would put our own king in check
        safe_moves = []
        for move, is_capture in moves:
            if self._is_move_safe(board, (row, col), move, color):
                safe_moves.append((move, is_capture))

        return safe_moves

    def _is_move_safe(self, board, from_pos, to_pos, color):
        """Check if a move would leave our king in check."""
        fr, fc = from_pos
        tr, tc = to_pos
        original_from = board[fr][fc]
        original_to = board[tr][tc]

        # Simulate the move
        board[tr][tc] = board[fr][fc]
        board[fr][fc] = ''

        # Check if our king is in check after the move
        king_pos = self._find_king(board, color)
        in_check = self._is_square_attacked(board, king_pos, 'B' if color == 'W' else 'W')

        # Undo the move
        board[fr][fc] = original_from
        board[tr][tc] = original_to

        return not in_check

    def _find_king(self, board, color):
        """Find the position of our king on the board."""
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _is_square_attacked(self, board, square, attacker_color):
        """Check if a square is attacked by the opponent."""
        if not square:
            return False
        sr, sc = square

        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                # Check if it's opponent's piece
                if (attacker_color == 'W' and piece.isupper()) or (attacker_color == 'B' and piece.islower()):
                    piece_type = piece.upper()
                    # Check if this piece can attack the square
                    if self._can_attack(board, (r, c), (sr, sc), piece_type, attacker_color):
                        return True
        return False

    def _can_attack(self, board, from_pos, to_pos, piece_type, attacker_color):
        """Check if a piece at from_pos can attack to_pos."""
        fr, fc = from_pos
        tr, tc = to_pos

        if piece_type == 'K':
            # King can attack adjacent squares
            return abs(fr - tr) <= 1 and abs(fc - tc) <= 1

        elif piece_type == 'N':
            # Knight can attack in L-shape or linear jumps
            return ((abs(fr - tr) == 2 and abs(fc - tc) == 1) or
                    (abs(fr - tr) == 1 and abs(fc - tc) == 2) or
                    (fr == tr and abs(fc - tc) == 2))

        elif piece_type == 'R':
            # Rook can attack along rows/columns
            if fr == tr:
                step = 1 if tc > fc else -1
                for col in range(fc + step, tc, step):
                    if board[fr][col] != '':
                        return False
                return True
            elif fc == tc:
                step = 1 if tr > fr else -1
                for row in range(fr + step, tr, step):
                    if board[row][fc] != '':
                        return False
                return True
            return False

        elif piece_type == 'P':
            # Pawn can attack diagonally forward
            direction = 1 if attacker_color == 'W' else -1
            return (fr + 1 == tr or fr - 1 == tr) and fc + direction == tc

        return False

    def _evaluate_moves(self, board, moves):
        """Evaluate all possible moves and return the best one."""
        best_move = None
        best_score = -float('inf')

        # If we can checkmate, do it immediately
        for move in moves:
            if self._is_checkmate_move(board, move):
                return move

        # Evaluate each move
        move_scores = []
        for move in moves:
            score = self._evaluate_move(board, move)
            move_scores.append((score, move))

            # Keep track of the best move
            if score > best_score:
                best_score = score
                best_move = move

        # If multiple moves have the same best score, choose randomly among them
        best_moves = [m for s, m in move_scores if s == best_score]
        if best_moves:
            return random.choice(best_moves)

        return best_move if best_move else random.choice(moves)

    def _is_checkmate_move(self, board, move):
        """Check if a move would result in checkmate."""
        # Parse the move
        parsed = self._parse_move(move)
        if not parsed:
            return False

        piece_type, from_pos, to_pos, is_capture = parsed
        fr, fc = from_pos
        tr, tc = to_pos

        # Create a deep copy of the board
        temp_board = [row[:] for row in board]

        # Make the move on the temporary board
        temp_board[tr][tc] = temp_board[fr][fc]
        temp_board[fr][fc] = ''

        # Check if the opponent is in checkmate
        opponent_color = 'B' if self.color == 'W' else 'W'
        if self._is_in_check(temp_board, opponent_color):
            # Check if opponent has any legal moves
            if not self._has_legal_moves(temp_board, opponent_color):
                return True

        return False

    def _evaluate_move(self, board, move):
        """Evaluate a single move and return its score."""
        parsed = self._parse_move(move)
        if not parsed:
            return -float('inf')

        piece_type, from_pos, to_pos, is_capture = parsed
        fr, fc = from_pos
        tr, tc = to_pos

        # Create a temporary board to simulate the move
        temp_board = [row[:] for row in board]
        moving_piece = temp_board[fr][fc]

        # Make the move
        temp_board[tr][tc] = moving_piece
        temp_board[fr][fc] = ''

        # Check for pawn promotion
        if piece_type == 'P':
            if (self.color == 'W' and tc == 7) or (self.color == 'B' and tc == 0):
                temp_board[tr][tc] = 'R' if self.color == 'W' else 'r'

        # Material evaluation
        material_score = self._evaluate_material(temp_board)

        # Positional evaluation
        positional_score = self._evaluate_position(temp_board)

        # Check if the move puts opponent in check
        opponent_color = 'B' if self.color == 'W' else 'W'
        check_score = 0
        if self._is_in_check(temp_board, opponent_color):
            check_score = 2  # Bonus for checking the opponent

        # Check if the move captures a piece
        capture_score = 0
        if is_capture:
            captured_piece = board[tr][tc]
            capture_score = self.piece_values.get(captured_piece, 0) * 2  # Bonus for capturing

        # Mobility evaluation (number of moves we have after this move)
        mobility_score = len(self._get_all_valid_moves(temp_board)) * 0.1

        # Combine all scores
        total_score = material_score + positional_score + check_score + capture_score + mobility_score

        return total_score

    def _evaluate_material(self, board):
        """Evaluate the material balance on the board."""
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    value = self.piece_values.get(piece, 0)
                    if piece.isupper():  # White piece
                        score += value
                    else:  # Black piece
                        score -= value
        # Return from our perspective
        return score if self.color == 'W' else -score

    def _evaluate_position(self, board):
        """Evaluate the positional strength of the board."""
        score = 0

        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue

                # Piece-square tables (simplified for 2x8 board)
                if piece.upper() == 'K':
                    # Kings are better in the center in endgame, but we don't have endgame detection
                    if self.color == 'W' and piece == 'K':
                        score += (c - 3.5) * 0.1  # Prefer center
                    elif self.color == 'B' and piece == 'k':
                        score += (3.5 - c) * 0.1  # Prefer center

                elif piece.upper() == 'N':
                    # Knights are better near the center
                    if self.color == 'W' and piece == 'N':
                        score += (abs(c - 3.5) * -0.2)
                    elif self.color == 'B' and piece == 'n':
                        score += (abs(c - 3.5) * -0.2)

                elif piece.upper() == 'R':
                    # Rooks are better on open files
                    if self.color == 'W' and piece == 'R':
                        # Check if the file is open
                        open_file = True
                        for row in range(2):
                            if board[row][c] != '' and board[row][c].upper() != 'R':
                                open_file = False
                                break
                        if open_file:
                            score += 0.5
                    elif self.color == 'B' and piece == 'r':
                        # Check if the file is open
                        open_file = True
                        for row in range(2):
                            if board[row][c] != '' and board[row][c].upper() != 'R':
                                open_file = False
                                break
                        if open_file:
                            score += 0.5

                elif piece.upper() == 'P':
                    # Pawns are better advanced
                    if self.color == 'W' and piece == 'P':
                        score += (c - 2) * 0.3  # Starting at c (index 2)
                    elif self.color == 'B' and piece == 'p':
                        score += (5 - c) * 0.3  # Starting at f (index 5)

        return score

    def _is_in_check(self, board, color):
        """Check if the king of the given color is in check."""
        king_pos = self._find_king(board, color)
        if not king_pos:
            return False

        attacker_color = 'B' if color == 'W' else 'W'
        return self._is_square_attacked(board, king_pos, attacker_color)

    def _has_legal_moves(self, board, color):
        """Check if the given color has any legal moves."""
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                if (color == 'W' and piece.isupper()) or (color == 'B' and piece.islower()):
                    piece_type = piece.upper()
                    moves = self._get_piece_moves(board, r, c, piece_type)
                    if moves:
                        return True
        return False

    def _pos_to_notation(self, row, col):
        """Convert (row, col) to algebraic notation like 'a1'."""
        return f"{'abcdefgh'[col]}{row + 1}"

    def _notation_to_pos(self, notation):
        """Convert algebraic notation like 'a1' to (row, col)."""
        if len(notation) != 2:
            return None
        col = notation[0].lower()
        row = int(notation[1]) - 1
        if col not in 'abcdefgh' or row not in (0, 1):
            return None
        return (row, 'abcdefgh'.index(col))

    def _parse_move(self, move_str):
        """
        Parse move notation into (piece_type, from_pos, to_pos, is_capture).
        Returns None if invalid format.
        """
        if len(move_str) < 4:
            return None

        piece_type = move_str[0].upper()
        if piece_type not in ('K', 'N', 'R', 'P'):
            return None

        # Check for capture notation
        if 'x' in move_str:
            x_idx = move_str.index('x')
            from_notation = move_str[1:x_idx]
            to_notation = move_str[x_idx+1:]
            is_capture = True
        else:
            from_notation = move_str[1:3]
            to_notation = move_str[3:5]
            is_capture = False

        from_pos = self._notation_to_pos(from_notation)
        to_pos = self._notation_to_pos(to_notation)

        if not from_pos or not to_pos:
            return None

        return (piece_type, from_pos, to_pos, is_capture)
