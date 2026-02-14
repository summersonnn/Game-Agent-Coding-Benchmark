"""
Agent Code: A7-TwoByEightChess
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-14 13:30:59
"""

from copy import deepcopy

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
        all_moves = self.get_all_valid_moves(board, self.color)
        if not all_moves:
            return "Ka2b2"  # Fallback, though should not happen

        best_move = None
        best_score = -float('inf')
        for move_str, (fr, fc, tr, tc, is_cap) in all_moves:
            # Simulate move
            temp_board = deepcopy(board)
            piece = temp_board[fr][fc]
            temp_board[tr][tc] = piece
            temp_board[fr][fc] = ''
            if piece.upper() == 'P':
                if (self.color == 'W' and tc == 7) or (self.color == 'B' and tc == 0):
                    temp_board[tr][tc] = 'R' if self.color == 'W' else 'r'

            score = self._evaluate_board(temp_board, self.color)
            # Check for checkmate
            opponent_color = 'B' if self.color == 'W' else 'W'
            if self._is_in_check(temp_board, opponent_color) and not self._has_legal_moves(temp_board, opponent_color):
                score += 1000  # Bonus for checkmate

            if score > best_score:
                best_score = score
                best_move = move_str

        return best_move

    def get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if self._is_own_piece(piece, color):
                    piece_type = self._get_piece_type(piece)
                    from_sq = self._pos_to_notation(r, c)
                    valid_moves = self._get_valid_moves_for_piece(board, r, c, color)
                    for nr, nc, is_capture in valid_moves:
                        to_sq = self._pos_to_notation(nr, nc)
                        if is_capture:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        moves.append((move_str, (r, c, nr, nc, is_capture)))
        return moves

    def _pos_to_notation(self, r, c):
        cols = 'abcdefgh'
        return f"{cols[c]}{r + 1}"

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _is_own_piece(self, piece, color):
        if color == 'W':
            return piece in 'KNRP'
        return piece in 'knrp'

    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self._is_own_piece(piece, color)

    def _get_piece_type(self, piece):
        return piece.upper() if piece else ''

    def _get_valid_moves_for_piece(self, board, row, col, color, ignore_check=False):
        piece = board[row][col]
        if not piece:
            return []
        piece_type = self._get_piece_type(piece)
        moves = []

        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            moves.append((nr, nc, is_capture))

        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append((nr, nc, is_capture))

        elif piece_type == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        moves.append((nr, nc, False))
                    elif self._is_enemy_piece(target, color):
                        moves.append((nr, nc, True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            # Forward move
            nc = col + direction
            if self._in_bounds(row, nc) and board[row][nc] == '':
                moves.append((row, nc, False))
            # Diagonal captures
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append((nr, nc, True))

        if ignore_check:
            return moves

        # Filter moves that leave King in check
        valid = []
        for nr, nc, is_cap in moves:
            if self._is_move_safe(board, (row, col), (nr, nc), color):
                valid.append((nr, nc, is_cap))
        return valid

    def _is_move_safe(self, board, from_pos, to_pos, color):
        temp_board = deepcopy(board)
        fr, fc = from_pos
        tr, tc = to_pos
        original_from = temp_board[fr][fc]
        original_to = temp_board[tr][tc]
        piece = original_from
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                piece = 'R' if color == 'W' else 'r'
        temp_board[tr][tc] = piece
        temp_board[fr][fc] = ''
        in_check = self._is_in_check(temp_board, color)
        # Undo is automatic since temp_board is discarded
        return not in_check

    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if not king_pos:
            return True
        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    enemy_moves = self._get_valid_moves_for_piece(board, r, c, enemy_color, ignore_check=True)
                    for nr, nc, _ in enemy_moves:
                        if (nr, nc) == king_pos:
                            return True
        return False

    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _has_legal_moves(self, board, color):
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    if self._get_valid_moves_for_piece(board, r, c, color):
                        return True
        return False

    def _evaluate_board(self, board, color):
        values = {'K': 0, 'N': 2, 'R': 5, 'P': 1, 'k': 0, 'n': -2, 'r': -5, 'p': -1}
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                score += values.get(piece, 0)
        return score if color == 'W' else -score
