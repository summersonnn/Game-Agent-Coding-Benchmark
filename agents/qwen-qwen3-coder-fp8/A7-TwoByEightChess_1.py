"""
Agent Code: A7-TwoByEightChess
Model: qwen/qwen3-coder@preset/fp8
Run: 1
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
        # Convert board to internal representation for easier handling
        game_engine_board = [row[:] for row in board]  # Deep copy
        
        # Determine current turn based on move history length
        current_turn = 'W' if len(move_history) % 2 == 0 else 'B'
        
        # Generate all valid moves for the current player
        valid_moves = self._get_all_valid_moves(game_engine_board, current_turn)
        
        if not valid_moves:
            # Should not happen in a normal game state, but just in case
            return "Ka1a2"  # Fallback move
        
        # Simple strategy:
        # 1. Try to find a winning move (checkmate)
        # 2. Try to find a capturing move
        # 3. Make a random safe move
        
        # Prioritize captures
        capture_moves = [move for move in valid_moves if 'x' in move]
        
        if capture_moves:
            # Prefer captures, especially pawn captures or those that promote
            return random.choice(capture_moves)
        else:
            # Otherwise, pick any valid move
            return random.choice(valid_moves)

    def _get_all_valid_moves(self, board, color):
        """Generate all valid moves for the given color."""
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_type = piece.upper()
                    from_sq = self._pos_to_notation(r, c)
                    for to_pos, is_capture in self._get_valid_moves_for_piece(board, r, c, color):
                        to_sq = self._pos_to_notation(to_pos[0], to_pos[1])
                        if is_capture:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        moves.append(move_str)
        return moves

    def _is_white_piece(self, piece):
        return piece in ('K', 'N', 'R', 'P')

    def _is_black_piece(self, piece):
        return piece in ('k', 'n', 'r', 'p')

    def _is_own_piece(self, piece, color):
        if color == 'W':
            return self._is_white_piece(piece)
        return self._is_black_piece(piece)

    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self._is_own_piece(piece, color)

    def _pos_to_notation(self, row, col):
        """Convert (row, col) to algebraic notation like 'a1'."""
        cols = 'abcdefgh'
        return f"{cols[col]}{row + 1}"

    def _notation_to_pos(self, notation):
        """Convert algebraic notation like 'a1' to (row, col)."""
        cols = 'abcdefgh'
        col_char = notation[0].lower()
        row = int(notation[1]) - 1
        col = cols.index(col_char)
        return (row, col)

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _get_piece_type(self, piece):
        """Return piece type in uppercase."""
        return piece.upper() if piece else ''

    def _find_king(self, board, color):
        """Find the position of the King for the given color."""
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _get_valid_moves_for_piece(self, board, row, col, color):
        """
        Get all valid destination squares for the piece at (row, col).
        Returns list of ((to_row, to_col), is_capture) tuples.
        """
        piece = board[row][col]
        if not piece:
            return []

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
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            moves.append(((nr, nc), is_capture))

        elif piece_type == 'N':
            # Knight: L-shape + linear 2-square jump
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))

        elif piece_type == 'R':
            # Rook: slide in 4 cardinal directions
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
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
            direction = 1 if color == 'W' else -1
            # Forward move
            nc = col + direction
            if self._in_bounds(row, nc) and board[row][nc] == '':
                moves.append(((row, nc), False))
            # Diagonal captures
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))

        # Filter moves that would leave own King in check (simplified simulation)
        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe(board, (row, col), to_pos, color):
                valid_moves.append((to_pos, is_capture))

        return valid_moves

    def _is_move_safe(self, board, from_pos, to_pos, color):
        """Check if making this move would leave the King in check."""
        fr, fc = from_pos
        tr, tc = to_pos
        original_from = board[fr][fc]
        original_to = board[tr][tc]

        # Simulate move with promotion
        moving_piece = original_from
        if moving_piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'
        board[tr][tc] = moving_piece
        board[fr][fc] = ''

        in_check = self._is_in_check(board, color)

        # Undo move
        board[fr][fc] = original_from
        board[tr][tc] = original_to

        return not in_check

    def _is_in_check(self, board, color):
        """Check if the given color's King is under attack."""
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True  # Should not happen

        enemy_color = 'B' if color == 'W' else 'W'

        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    enemy_moves = self._get_valid_moves_for_piece(board, r, c, enemy_color)
                    for to_pos, _ in enemy_moves:
                        if to_pos == king_pos:
                            return True
        return False
