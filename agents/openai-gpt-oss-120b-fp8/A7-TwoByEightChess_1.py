"""
Agent Code: A7-TwoByEightChess
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-14 13:17:43
"""

import copy
import math

import random
import copy
import math

class TwoByEightChessAgent:
    """
    Simple Mini‑Chess agent for the 2×8 variant.
    It uses a shallow minimax search (depth 4 plies) with a basic
    material‑based evaluation and a few heuristics (checks, captures,
    promotions).  All move generation, legality checking and check detection
    are performed locally from the supplied board representation.
    """

    # piece values for the static evaluation
    _VALUE = {
        'P': 1,
        'N': 3,
        'R': 5,
        'K': 0,          # king value is handled separately (loss = huge negative)
    }

    _COLS = 'abcdefgh'

    def __init__(self, name, color):
        """
        Args:
            name (str): agent name – not used by the logic.
            color (str): 'W' for White or 'B' for Black.
        """
        self.name = name
        self.my_color = color.upper()          # 'W' or 'B'
        self.opponent = 'B' if self.my_color == 'W' else 'W'

    # ------------------------------------------------------------------ #
    #  Helper conversion utilities
    # ------------------------------------------------------------------ #
    @staticmethod
    def _in_bounds(r, c):
        return 0 <= r < 2 and 0 <= c < 8

    @classmethod
    def _pos_to_notation(cls, r, c):
        return f"{cls._COLS[c]}{r + 1}"

    @staticmethod
    def _piece_color(piece):
        return 'W' if piece.isupper() else 'B'

    @staticmethod
    def _piece_type(piece):
        return piece.upper()

    # ------------------------------------------------------------------ #
    #  Move generation
    # ------------------------------------------------------------------ #
    def _generate_piece_moves(self, board, r, c, ignore_king_safety=False):
        """
        Returns a list of possible moves for the piece on (r,c).
        Each move is a tuple (to_r, to_c, is_capture).
        If ignore_king_safety is True the move is not checked for leaving the
        own king in check – this is used when we only need attack squares.
        """
        piece = board[r][c]
        if not piece:
            return []

        color = self._piece_color(piece)
        ptype = self._piece_type(piece)
        moves = []

        # ---------- King ----------
        if ptype == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not target or self._piece_color(target) != color:
                            moves.append((nr, nc, bool(target)))

        # ---------- Knight ----------
        elif ptype == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear:
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not target or self._piece_color(target) != color:
                        moves.append((nr, nc, bool(target)))

        # ---------- Rook ----------
        elif ptype == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not target:
                        moves.append((nr, nc, False))
                    elif self._piece_color(target) != color:
                        moves.append((nr, nc, True))
                        break
                    else:          # own piece blocks
                        break
                    nr += dr
                    nc += dc

        # ---------- Pawn ----------
        elif ptype == 'P':
            direction = 1 if color == 'W' else -1
            # forward
            nc = c + direction
            if self._in_bounds(r, nc) and board[r][nc] == '':
                moves.append((r, nc, False))
            # captures
            for dr in (-1, 1):
                nr = r + dr
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target and self._piece_color(target) != color:
                        moves.append((nr, nc, True))

        # filter moves that leave own king in check (unless ignored)
        if ignore_king_safety:
            return moves

        legal = []
        for nr, nc, cap in moves:
            if self._move_keeps_king_safe(board, (r, c), (nr, nc), color):
                legal.append((nr, nc, cap))
        return legal

    # ------------------------------------------------------------------ #
    #  Safety / Check utilities
    # ------------------------------------------------------------------ #
    def _simulate_move(self, board, from_sq, to_sq):
        """Return a new board after moving piece from from_sq to to_sq,
        handling promotion."""
        new_board = [row[:] for row in board]
        fr, fc = from_sq
        tr, tc = to_sq
        piece = new_board[fr][fc]
        new_board[fr][fc] = ''
        # promotion
        if piece.upper() == 'P':
            if (piece.isupper() and tc == 7) or (piece.islower() and tc == 0):
                piece = 'R' if piece.isupper() else 'r'
        new_board[tr][tc] = piece
        return new_board

    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None   # should never happen in a legal position

    def _is_square_attacked(self, board, sq, attacker_color):
        """True if any piece of attacker_color attacks sq."""
        ar, ac = sq
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._piece_color(piece) == attacker_color:
                    for tr, tc, _ in self._generate_piece_moves(board, r, c,
                                                                ignore_king_safety=True):
                        if (tr, tc) == (ar, ac):
                            return True
        return False

    def _king_in_check(self, board, color):
        king_sq = self._find_king(board, color)
        if not king_sq:
            return True                     # no king = treated as check
        return self._is_square_attacked(board, king_sq,
                                        'B' if color == 'W' else 'W')

    def _move_keeps_king_safe(self, board, from_sq, to_sq, color):
        """Simulate the move and verify the own king is not left in check."""
        new_board = self._simulate_move(board, from_sq, to_sq)
        return not self._king_in_check(new_board, color)

    # ------------------------------------------------------------------ #
    #  Full move list for a side
    # ------------------------------------------------------------------ #
    def _all_legal_moves(self, board, color):
        """Return a list of tuples (move_str, new_board)."""
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or self._piece_color(piece) != color:
                    continue
                piece_type = self._piece_type(piece)
                from_sq = (r, c)
                from_not = self._pos_to_notation(r, c)
                for tr, tc, is_cap in self._generate_piece_moves(board, r, c):
                    to_not = self._pos_to_notation(tr, tc)
                    move_str = (f"{piece_type}{from_not}x{to_not}"
                                if is_cap else f"{piece_type}{from_not}{to_not}")
                    new_board = self._simulate_move(board, from_sq, (tr, tc))
                    moves.append((move_str, new_board))
        return moves

    # ------------------------------------------------------------------ #
    #  Evaluation
    # ------------------------------------------------------------------ #
    def _evaluate(self, board):
        """Simple material evaluation from the point of view of self.my_color."""
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                val = self._VALUE[self._piece_type(piece)]
                if self._piece_color(piece) == self.my_color:
                    score += val
                else:
                    score -= val
        # huge bonus/punishment for checkmate/draw will be handled in minimax
        return score

    # ------------------------------------------------------------------ #
    #  Minimax search
    # ------------------------------------------------------------------ #
    def _minimax(self, board, depth, maximizing, alpha=-math.inf, beta=math.inf):
        """
        Returns (score, best_move_str).  best_move_str is only meaningful at
        the root call (depth == original depth).
        """
        # terminal detection
        if self._king_in_check(board, self.my_color) and not self._all_legal_moves(board, self.my_color):
            # my king is checkmated
            return (-10000 if maximizing else 10000), None
        if self._king_in_check(board, self.opponent) and not self._all_legal_moves(board, self.opponent):
            # opponent is checkmated
            return (10000 if maximizing else -10000), None
        if depth == 0:
            return self._evaluate(board), None

        color_to_move = self.my_color if maximizing else self.opponent
        legal = self._all_legal_moves(board, color_to_move)

        if not legal:                     # stalemate
            return 0, None

        best_move = None

        if maximizing:
            max_eval = -math.inf
            for move_str, new_board in legal:
                eval_score, _ = self._minimax(new_board, depth - 1, False,
                                              alpha, beta)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move_str
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = math.inf
            for move_str, new_board in legal:
                eval_score, _ = self._minimax(new_board, depth - 1, True,
                                              alpha, beta)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move_str
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # ------------------------------------------------------------------ #
    #  Public interface
    # ------------------------------------------------------------------ #
    def make_move(self, board, move_history):
        """
        Decide on a move.
        Parameters
        ----------
        board : list[list[str]]
            Current board (2 rows × 8 columns).  Empty squares are ''.
        move_history : list[str]
            List of SAN‑like strings already played (unused here).

        Returns
        -------
        str
            Move in the required notation, e.g. "Nb2c4" or "Ra1xa5".
        """
        # Generate all legal moves for the side to play (which is always our color)
        legal_moves = self._all_legal_moves(board, self.my_color)

        if not legal_moves:
            # No legal move – should never happen because the engine will
            # declare stalemate/checkmate, but we must return something.
            return "Kd1d2"  # dummy (engine will replace with a random legal move)

        # Try a shallow minimax search (depth 4 plies = 2 full moves)
        _, best = self._minimax(board, depth=4, maximizing=True)

        if best and best in [m for m, _ in legal_moves]:
            return best

        # Fallback: choose the move with the highest static evaluation
        best_score = -math.inf
        best_move = None
        for move_str, new_board in legal_moves:
            score = self._evaluate(new_board)
            if score > best_score:
                best_score = score
                best_move = move_str
        if best_move:
            return best_move

        # Final fallback – random legal move
        return random.choice([m for m, _ in legal_moves])
