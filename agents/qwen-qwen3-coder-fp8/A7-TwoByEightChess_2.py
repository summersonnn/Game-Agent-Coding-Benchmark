"""
Agent Code: A7-TwoByEightChess
Model: qwen/qwen3-coder@preset/fp8
Run: 2
Generated: 2026-02-14 14:28:38
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

    def make_move(self, board, move_history):
        """
        Decide the next move based on the current board state.

        Args:
            board: list[list[str]] - 2x8 board (2 rows, 8 columns).
                   board[0] = row 1, board[1] = row 2.
                   Each row is an 8-element list.
                   Pieces: 'K','N','R','P' (White), 'k','n','r','p' (Black), '' (empty)
                   Starting position:
                       board[0] = ['R','N','P','','','p','n','r']  (row 1)
                       board[1] = ['K','N','P','','','p','n','k']  (row 2)

            move_history: list[str] - List of all moves played so far.
                   Example: ["Nb2d1", "ng2e1", "Ra1a5", "pf1xe1"]

        Returns:
            str: Move in notation format.
                 Regular move: "[Piece][FromSquare][ToSquare]" e.g., "Nb2d1"
                 Capture: "[Piece][FromSquare]x[ToSquare]" e.g., "Ra1xa5"
        """
        # Reconstruct game state to generate valid moves
        game = TwoByEightChess()
        game.board = [row[:] for row in board]  # Deep copy
        game.current_turn = self.color
        game.move_history = move_history[:]
        
        # Get all valid moves for current player
        valid_moves = game.get_all_valid_moves(self.color)
        
        if not valid_moves:
            # Should not happen in a normal game state, but just in case
            return "Ka1a2"  # Dummy move that will be overridden by engine

        # Simple strategy:
        # 1. Try to find a winning move (checkmate)
        # 2. Try to find a capturing move
        # 3. Make a random safe move

        # Prioritize captures
        capture_moves = [move for move in valid_moves if 'x' in move]
        
        # If there are captures, randomly pick one
        if capture_moves:
            return random.choice(capture_moves)
        
        # Otherwise, pick any valid move
        return random.choice(valid_moves)

# Game engine class for internal use in move generation
class TwoByEightChess:
    """
    2x8 Mini Chess game engine.
    Board: 2 rows x 8 columns (row 0-1, col 0-7)
    Displayed as rows 1-2, columns a-h.
    Pieces: K/N/R/P (White), k/n/r/p (Black), '' (empty)
    """

    WHITE = 'W'
    BLACK = 'B'
    COLS = 'abcdefgh'

    def __init__(self):
        # board[0] = row 1, board[1] = row 2
        self.board = [
            ['R', 'N', 'P', '', '', 'p', 'n', 'r'],
            ['K', 'N', 'P', '', '', 'p', 'n', 'k'],
        ]
        self.current_turn = self.WHITE
        self.move_history = []
        self.position_history = []
        self._record_position()

    def _record_position(self):
        """Record current position for repetition detection."""
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
        """Return piece type in uppercase."""
        return piece.upper() if piece else ''

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _pos_to_notation(self, row, col):
        """Convert (row, col) to algebraic notation like 'a1'."""
        return f"{self.COLS[col]}{row + 1}"

    def _notation_to_pos(self, notation):
        """Convert algebraic notation like 'a1' to (row, col). Returns None if invalid."""
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
        """Find the position of the King for the given color."""
        target = 'K' if color == self.WHITE else 'k'
        for r in range(2):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None

    def _get_valid_moves_for_piece(self, row, col, ignore_check=False):
        """
        Get all valid destination squares for the piece at (row, col).
        Returns list of ((to_row, to_col), is_capture) tuples.
        """
        piece = self.board[row][col]
        if not piece:
            return []

        color = self.WHITE if self._is_white_piece(piece) else self.BLACK
        piece_type = self._get_piece_type(piece)
        moves = []

        if piece_type == 'K':
            # King: 1 square in any direction
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
            # Knight: L-shape + linear 2-square jump, all can jump over pieces
            # L-shape deltas (standard chess knight)
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            # Linear 2-square jump (from 2x8 Mini Chess rules)
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))

        elif piece_type == 'R':
            # Rook: slide in 4 cardinal directions, blocked by pieces
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
            # Pawn: 1 square forward, diagonal capture
            # White moves right (+col), Black moves left (-col)
            direction = 1 if color == self.WHITE else -1
            # Forward move (no capture)
            nc = col + direction
            if self._in_bounds(row, nc) and self.board[row][nc] == '':
                moves.append(((row, nc), False))
            # Diagonal captures (row ±1, col forward)
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))

        if ignore_check:
            return moves

        # Filter moves that would leave own King in check
        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe((row, col), to_pos, color):
                valid_moves.append((to_pos, is_capture))

        return valid_moves

    def _is_move_safe(self, from_pos, to_pos, color):
        """Check if making this move would leave the King in check."""
        fr, fc = from_pos
        tr, tc = to_pos
        original_from = self.board[fr][fc]
        original_to = self.board[tr][tc]

        # Simulate move (with promotion if applicable)
        moving_piece = original_from
        if moving_piece.upper() == 'P':
            if (color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0):
                moving_piece = 'R' if color == self.WHITE else 'r'
        self.board[tr][tc] = moving_piece
        self.board[fr][fc] = ''

        in_check = self._is_in_check(color)

        # Undo
        self.board[fr][fc] = original_from
        self.board[tr][tc] = original_to

        return not in_check

    def _is_in_check(self, color):
        """Check if the given color's King is under attack."""
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
        """Check if the given color has any legal moves."""
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, color):
                    if self._get_valid_moves_for_piece(r, c):
                        return True
        return False

    def _is_insufficient_material(self):
        """Check if only Kings remain (draw by insufficient material)."""
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.upper() != 'K':
                    return False
        return True

    def _is_threefold_repetition(self):
        """Check for threefold repetition."""
        if len(self.position_history) < 3:
            return False
        current_pos = self.position_history[-1]
        count = sum(1 for pos in self.position_history if pos == current_pos)
        return count >= 3

    def get_all_valid_moves(self, color):
        """Get all valid moves for a color. Returns list of move strings."""
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
        """
        Parse move notation into (piece_type, from_pos, to_pos, is_capture).
        Returns None if invalid format.

        Format: [Piece][FromSquare][x?][ToSquare]
        Examples: "Nb2d1", "Ra1xa5", "Pc1d1"
        """
        if not isinstance(move_str, str):
            return None
        move_str = move_str.strip()
        if len(move_str) < 5:
            return None

        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R', 'P'):
            return None

        # Check for capture notation
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

    def is_valid_move(self, move_str, color):
        """Validate a move for the given color."""
        parsed = self.parse_move(move_str)
        if not parsed:
            return False, "Invalid move notation"

        piece_type, from_pos, to_pos, is_capture = parsed
        fr, fc = from_pos

        piece = self.board[fr][fc]
        if not piece:
            return False, f"No piece at {self._pos_to_notation(fr, fc)}"

        if not self._is_own_piece(piece, color):
            return False, "Cannot move opponent's piece"

        if self._get_piece_type(piece) != piece_type:
            return False, f"Piece at {self._pos_to_notation(fr, fc)} is not a {piece_type}"

        # Check if move is in valid moves
        valid_moves = self._get_valid_moves_for_piece(fr, fc)
        for valid_to, valid_capture in valid_moves:
            if valid_to == to_pos:
                if is_capture != valid_capture:
                    if is_capture:
                        return False, "No piece to capture at destination"
                    else:
                        return False, "Must use capture notation (x) when capturing"
                return True, ""

        if self._is_in_check(color):
            return False, "Must escape check"
        return False, "Invalid move for this piece"

    def make_move(self, move_str, color):
        """Execute a move. Returns (success, message)."""
        valid, error = self.is_valid_move(move_str, color)
        if not valid:
            return False, error

        parsed = self.parse_move(move_str)
        _, from_pos, to_pos, _ = parsed
        fr, fc = from_pos
        tr, tc = to_pos

        # Execute move
        self.board[tr][tc] = self.board[fr][fc]
        self.board[fr][fc] = ''

        # Pawn promotion (auto-promote to Rook)
        piece = self.board[tr][tc]
        if piece.upper() == 'P':
            if (self._is_white_piece(piece) and tc == 7) or \
               (self._is_black_piece(piece) and tc == 0):
                self.board[tr][tc] = 'R' if self._is_white_piece(piece) else 'r'

        # Record move and position
        self.move_history.append(move_str)
        self._record_position()

        # Switch turn
        self.current_turn = self.BLACK if self.current_turn == self.WHITE else self.WHITE

        return True, ""

    def get_game_state(self):
        """
        Check the current game state.
        Returns: 'ongoing', 'white_wins', 'black_wins', 'draw_stalemate',
                 'draw_repetition', 'draw_material'
        """
        if self._is_insufficient_material():
            return 'draw_material'

        if self._is_threefold_repetition():
            return 'draw_repetition'

        current = self.current_turn
        in_check = self._is_in_check(current)
        has_moves = self._has_legal_moves(current)

        if not has_moves:
            if in_check:
                return 'white_wins' if current == self.BLACK else 'black_wins'
            else:
                return 'draw_stalemate'

        return 'ongoing'

    def get_board_display(self):
        """Return a string representation of the board."""
        header = "    " + "  ".join(c for c in 'a b c d e f g h'.split())
        row1 = "1 | " + " | ".join(p if p else '.' for p in self.board[0]) + " |"
        row2 = "2 | " + " | ".join(p if p else '.' for p in self.board[1]) + " |"
        return f"{header}\n{row1}\n{row2}"
