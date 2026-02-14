"""
Agent Code: A7-TwoByEightChess
Model: mistralai/mistral-large-2512
Run: 2
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
            'K': 0,    # King value is 0 since it can't be captured
            'N': 3,
            'R': 5,
            'P': 1
        }
        self.opponent_color = 'B' if color == 'W' else 'W'
        self.columns = 'abcdefgh'
        self.rows = '12'

    def make_move(self, board, move_history):
        # Get all valid moves
        valid_moves = self.get_all_valid_moves(board)

        if not valid_moves:
            return "Ka2b2"  # Shouldn't happen as game would be over

        # Evaluate all moves and choose the best one
        best_move = self.evaluate_moves(board, valid_moves)

        # If no good move found, choose randomly from valid moves
        if best_move is None:
            return random.choice(valid_moves)

        return best_move

    def get_all_valid_moves(self, board):
        """Get all valid moves for the current player"""
        game = TwoByEightChessSimulator(board, self.color)
        return game.get_all_valid_moves(self.color)

    def evaluate_moves(self, board, moves):
        """Evaluate all possible moves and return the best one"""
        best_score = -float('inf')
        best_moves = []

        # Evaluate each move
        for move in moves:
            score = self.evaluate_move(board, move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # Return a random move from the best options
        return random.choice(best_moves) if best_moves else None

    def evaluate_move(self, board, move):
        """Evaluate a single move using multiple factors"""
        game = TwoByEightChessSimulator(board, self.color)
        parsed = game.parse_move(move)
        if not parsed:
            return -float('inf')

        piece_type, from_pos, to_pos, is_capture = parsed
        fr, fc = from_pos
        tr, tc = to_pos

        # Create a copy of the board to simulate the move
        board_copy = [row.copy() for row in board]
        board_copy[tr][tc] = board_copy[fr][fc]
        board_copy[fr][fc] = ''

        # Check for pawn promotion
        piece = board_copy[tr][tc]
        if piece.upper() == 'P':
            if (self.color == 'W' and tc == 7) or (self.color == 'B' and tc == 0):
                board_copy[tr][tc] = 'R' if self.color == 'W' else 'r'

        # Calculate score based on multiple factors
        score = 0

        # 1. Material advantage
        material_score = self.calculate_material_score(board_copy)
        score += material_score * 10  # High weight for material

        # 2. Piece safety (avoid moving into danger)
        if self.is_square_attacked(board_copy, to_pos, self.color):
            score -= 5  # Penalty for moving into danger

        # 3. King safety
        king_safety = self.evaluate_king_safety(board_copy)
        score += king_safety * 3

        # 4. Control of center (columns d and e)
        center_control = self.evaluate_center_control(board_copy)
        score += center_control

        # 5. Check if this move puts opponent in check
        if self.is_opponent_in_check(board_copy):
            score += 8  # Bonus for checking opponent

        # 6. Check if this move leads to checkmate
        if self.is_opponent_checkmated(board_copy):
            score += 100  # Big bonus for checkmate

        # 7. Capture bonus
        if is_capture:
            captured_piece = board[tr][tc].lower()
            score += self.piece_values.get(captured_piece.upper(), 0) * 2

        # 8. Pawn advancement
        if piece_type == 'P':
            if self.color == 'W':
                score += (tc - fc) * 0.5  # Reward advancing pawns
            else:
                score += (fc - tc) * 0.5  # Black pawns move left

        # 9. Rook on open file
        if piece_type == 'R':
            if self.is_open_file(board_copy, tc):
                score += 2

        # 10. Knight positioning (prefer center)
        if piece_type == 'N':
            center_distance = min(abs(tc - 3), abs(tc - 4))
            score -= center_distance * 0.5

        return score

    def calculate_material_score(self, board):
        """Calculate material advantage for the current player"""
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    if self._is_own_piece(piece):
                        score += self.piece_values.get(piece.upper(), 0)
                    elif self._is_enemy_piece(piece):
                        score -= self.piece_values.get(piece.upper(), 0)
        return score

    def evaluate_king_safety(self, board):
        """Evaluate king safety for the current player"""
        king_pos = self.find_king(board)
        if not king_pos:
            return -10  # King not found (shouldn't happen)

        kr, kc = king_pos
        safety = 0

        # Check if king is on the edge
        if kc == 0 or kc == 7:
            safety -= 1

        # Check if king is exposed to attacks
        if self.is_square_attacked(board, king_pos, self.color):
            safety -= 3

        # Check adjacent squares
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = kr + dr, kc + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    if self.is_square_attacked(board, (nr, nc), self.color):
                        safety -= 1

        return safety

    def evaluate_center_control(self, board):
        """Evaluate control of center columns (d and e)"""
        center_cols = [3, 4]  # d and e
        score = 0

        for c in center_cols:
            for r in range(2):
                piece = board[r][c]
                if self._is_own_piece(piece):
                    if piece.upper() == 'N':
                        score += 1  # Knights in center are good
                    elif piece.upper() == 'R':
                        score += 0.5
                    elif piece.upper() == 'P':
                        score += 0.3
        return score

    def is_open_file(self, board, col):
        """Check if a file (column) is open (no pawns)"""
        for r in range(2):
            piece = board[r][col]
            if piece.upper() == 'P':
                return False
        return True

    def is_square_attacked(self, board, pos, color):
        """Check if a square is attacked by the opponent"""
        r, c = pos
        opponent_color = 'B' if color == 'W' else 'W'
        simulator = TwoByEightChessSimulator(board, opponent_color)

        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece and simulator._is_own_piece(piece, opponent_color):
                    moves = simulator._get_valid_moves_for_piece(row, col, ignore_check=True)
                    for (tr, tc), _ in moves:
                        if tr == r and tc == c:
                            return True
        return False

    def is_opponent_in_check(self, board):
        """Check if the opponent is in check"""
        opponent_color = 'B' if self.color == 'W' else 'W'
        simulator = TwoByEightChessSimulator(board, opponent_color)
        return simulator._is_in_check(opponent_color)

    def is_opponent_checkmated(self, board):
        """Check if the opponent is checkmated"""
        opponent_color = 'B' if self.color == 'W' else 'W'
        simulator = TwoByEightChessSimulator(board, opponent_color)

        if not simulator._is_in_check(opponent_color):
            return False

        return not simulator._has_legal_moves(opponent_color)

    def _is_own_piece(self, piece):
        """Check if a piece belongs to the current player"""
        if self.color == 'W':
            return piece in ('K', 'N', 'R', 'P')
        return piece in ('k', 'n', 'r', 'p')

    def _is_enemy_piece(self, piece):
        """Check if a piece belongs to the opponent"""
        if self.color == 'W':
            return piece in ('k', 'n', 'r', 'p')
        return piece in ('K', 'N', 'R', 'P')

    def find_king(self, board):
        """Find the position of the current player's king"""
        target = 'K' if self.color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

class TwoByEightChessSimulator:
    """
    Simplified game engine for move evaluation and validation.
    This is a stripped-down version of the full game engine for the agent's internal use.
    """
    WHITE = 'W'
    BLACK = 'B'
    COLS = 'abcdefgh'

    def __init__(self, board, color):
        self.board = [row.copy() for row in board]
        self.current_turn = color

    def _is_white_piece(self, piece):
        return piece in ('K', 'N', 'R', 'P')

    def _is_black_piece(self, piece):
        return piece in ('k', 'n', 'r', 'p')

    def _is_own_piece(self, piece, color):
        if color == self.WHITE:
            return self._is_white_piece(piece)
        return self._is_black_piece(piece)

    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self._is_own_piece(piece, color)

    def _get_piece_type(self, piece):
        return piece.upper() if piece else ''

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _get_valid_moves_for_piece(self, row, col, ignore_check=False):
        piece = self.board[row][col]
        if not piece:
            return []

        color = self.WHITE if self._is_white_piece(piece) else self.BLACK
        piece_type = self._get_piece_type(piece)
        moves = []

        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = self.board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            moves.append(((nr, nc), is_capture))

        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))

        elif piece_type == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if target == '':
                        moves.append(((nr, nc), False))
                    elif self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif piece_type == 'P':
            direction = 1 if color == self.WHITE else -1
            nc = col + direction
            if self._in_bounds(row, nc) and self.board[row][nc] == '':
                moves.append(((row, nc), False))
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))

        if ignore_check:
            return moves

        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe((row, col), to_pos, color):
                valid_moves.append((to_pos, is_capture))

        return valid_moves

    def _is_move_safe(self, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        original_from = self.board[fr][fc]
        original_to = self.board[tr][tc]

        moving_piece = original_from
        if moving_piece.upper() == 'P':
            if (color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0):
                moving_piece = 'R' if color == self.WHITE else 'r'
        self.board[tr][tc] = moving_piece
        self.board[fr][fc] = ''

        in_check = self._is_in_check(color)

        self.board[fr][fc] = original_from
        self.board[tr][tc] = original_to

        return not in_check

    def _is_in_check(self, color):
        king_pos = self._find_king(color)
        if king_pos is None:
            return True

        enemy_color = self.BLACK if color == self.WHITE else self.WHITE

        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    enemy_moves = self._get_valid_moves_for_piece(r, c, ignore_check=True)
                    for to_pos, _ in enemy_moves:
                        if to_pos == king_pos:
                            return True
        return False

    def _find_king(self, color):
        target = 'K' if color == self.WHITE else 'k'
        for r in range(2):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None

    def _has_legal_moves(self, color):
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, color):
                    if self._get_valid_moves_for_piece(r, c):
                        return True
        return False

    def _pos_to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"

    def _notation_to_pos(self, notation):
        if len(notation) != 2:
            return None
        col_char = notation[0].lower()
        if col_char not in self.COLS:
            return None
        try:
            row = int(notation[1]) - 1
        except ValueError:
            return None
        col = self.COLS.index(col_char)
        if not self._in_bounds(row, col):
            return None
        return (row, col)

    def get_all_valid_moves(self, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_type = self._get_piece_type(piece)
                    from_sq = self._pos_to_notation(r, c)
                    for to_pos, is_capture in self._get_valid_moves_for_piece(r, c):
                        to_sq = self._pos_to_notation(to_pos[0], to_pos[1])
                        if is_capture:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        moves.append(move_str)
        return moves

    def parse_move(self, move_str):
        if not isinstance(move_str, str):
            return None
        move_str = move_str.strip()
        if len(move_str) < 5:
            return None

        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R', 'P'):
            return None

        if 'x' in move_str.lower():
            idx = move_str.lower().index('x')
            from_notation = move_str[1:idx]
            to_notation = move_str[idx+1:]
            is_capture = True
        else:
            from_notation = move_str[1:3]
            to_notation = move_str[3:5]
            is_capture = False

        from_pos = self._notation_to_pos(from_notation)
        to_pos = self._notation_to_pos(to_notation)

        if from_pos is None or to_pos is None:
            return None

        return (piece, from_pos, to_pos, is_capture)
