"""
Agent Code: A7-TwoByEightChess
Model: qwen/qwen3-coder-next@preset/fp8
Run: 2
Generated: 2026-02-14 14:25:17
"""

import copy

import random
import copy

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, board, move_history):
        # Create a temporary game instance to compute valid moves

        game = TwoByEightChess()
        game.board = copy.deepcopy(board)
        game.current_turn = self.color
        game.move_history = move_history.copy()
        game.position_history = []
        game._record_position()
        
        # Get all valid moves for current player
        valid_moves = game.get_all_valid_moves(self.color)
        
        if not valid_moves:
            # No moves available - forfeit or stalemate
            return ""
        
        # Simple evaluation function to choose best move
        best_move = None
        best_score = float('-inf')
        
        for move in valid_moves:
            # Simulate the move
            temp_game = TwoByEightChess()
            temp_game.board = copy.deepcopy(board)
            temp_game.current_turn = self.color
            temp_game.move_history = move_history.copy()
            temp_game.position_history = []
            temp_game._record_position()
            
            # Make the move in simulation
            temp_game.make_move(move, self.color)
            
            # Evaluate the resulting position
            score = self.evaluate_position(temp_game.board, self.color)
            
            # Add small random component to avoid deterministic loops
            score += random.uniform(0, 0.01)
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move else random.choice(valid_moves)
            
    
    def evaluate_position(self, board, color):
        # Material values
        piece_values = {'K': 1000, 'N': 300, 'R': 500, 'P': 100,
                       'k': -1000, 'n': -300, 'r': -500, 'p': -100}
        
        # Position bonuses
        center_bonus = 10  # Columns c,d,e,f are more central
        advancement_bonus = 5  # Pawns get bonus for advancing
        king_safety_bonus = 20  # King closer to center is safer
        
        total_score = 0
        
        for row in range(2):
            for col in range(8):
                piece = board[row][col]
                if piece:
                    # Material value
                    total_score += piece_values.get(piece, 0)
                    
                    # Position bonuses
                    piece_type = piece.upper()
                    is_white = piece.isupper()
                    
                    # Center bonus (columns c,d,e,f = indices 2,3,4,5)
                    if col in [2, 3, 4, 5]:
                        total_score += center_bonus if is_white else -center_bonus
                    
                    # Pawn advancement bonus
                    if piece_type == 'P':
                        if is_white:
                            total_score += advancement_bonus * col  # White pawns move right
                        else:
                            total_score -= advancement_bonus * (7 - col)  # Black pawns move left
                    
                    # King safety - prefer kings to be on edge or not too central
                    if piece_type == 'K':
                        if is_white:
                            # White king safer on edges (a or h) or at least not too central
                            if col in [0, 7]:
                                total_score += king_safety_bonus
                            elif col not in [2, 3, 4, 5]:
                                total_score += 5
                        else:
                            if col in [0, 7]:
                                total_score -= king_safety_bonus
                            elif col not in [2, 3, 4, 5]:
                                total_score -= 5
        
        return total_score if color == 'W' else -total_score


# Include minimal TwoByEightChess implementation for simulation
# This is a stripped-down version just for move evaluation
class TwoByEightChess:
    WHITE = 'W'
    BLACK = 'B'
    COLS = 'abcdefgh'

    def __init__(self):
        self.board = [
            ['R', 'N', 'P', '', '', 'p', 'n', 'r'],
            ['K', 'N', 'P', '', '', 'p', 'n', 'k'],
        ]
        self.current_turn = self.WHITE
        self.move_history = []
        self.position_history = []
        self._record_position()

    def _record_position(self):
        pos = (tuple(tuple(row) for row in self.board), self.current_turn)
        self.position_history.append(pos)

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

    def _find_king(self, color):
        target = 'K' if color == self.WHITE else 'k'
        for r in range(2):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None

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

    def _has_legal_moves(self, color):
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, color):
                    if self._get_valid_moves_for_piece(r, c):
                        return True
        return False

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

    def make_move(self, move_str, color):
        parsed = self.parse_move(move_str)
        if not parsed:
            return False, "Invalid move"

        _, from_pos, to_pos, _ = parsed
        fr, fc = from_pos
        tr, tc = to_pos

        self.board[tr][tc] = self.board[fr][fc]
        self.board[fr][fc] = ''

        piece = self.board[tr][tc]
        if piece.upper() == 'P':
            if (self._is_white_piece(piece) and tc == 7) or \
               (self._is_black_piece(piece) and tc == 0):
                self.board[tr][tc] = 'R' if self._is_white_piece(piece) else 'r'

        self.move_history.append(move_str)
        self._record_position()
        self.current_turn = self.BLACK if self.current_turn == self.WHITE else self.WHITE

        return True, ""
