"""
Agent Code: A7-TwoByEightChess
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-14 13:17:43
"""

import copy

import random
import copy

class TwoByEightChessAgent:
    COLS = "abcdefgh"
    ROWS = [1, 2]

    # piece values for simple evaluation
    PIECE_VALUE = {
        'P': 1,
        'N': 3,
        'R': 5,
        'K': 0,
    }

    def __init__(self, name, color):
        """
        Args:
            name (str): Agent name.
            color (str): 'W' for White, 'B' for Black.
        """
        self.name = name
        self.color = color.upper()          # 'W' or 'B'
        self.max_depth = 4                  # ply depth for minimax

    # --------------------------------------------------------------------- #
    #  Public API
    # --------------------------------------------------------------------- #
    def make_move(self, board, move_history):
        """
        Choose the best legal move using a shallow minimax search.

        Args:
            board (list[list[str]]): 2x8 board (row 0 = rank 1, row 1 = rank 2).
            move_history (list[str]): List of previous moves (unused).

        Returns:
            str: Move in the required notation.
        """
        legal_moves = self._all_legal_moves(board, self.color)
        if not legal_moves:
            # No legal moves – should be game over, but return a dummy move.
            return "Kd1d2"  # never reached by the engine

        best_score = -float('inf')
        best_moves = []

        for mv in legal_moves:
            new_board = self._apply_move(board, mv)
            score = self._minimax(new_board, self._opp(self.color), self.max_depth - 1, -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_moves = [mv]
            elif score == best_score:
                best_moves.append(mv)

        chosen = random.choice(best_moves)
        return self._move_to_notation(chosen)

    # --------------------------------------------------------------------- #
    #  Minimax search
    # --------------------------------------------------------------------- #
    def _minimax(self, board, color, depth, alpha, beta, maximizing):
        """
        Return static evaluation for the position from the perspective of the
        original agent (self.color).  Positive values are good for self.color.
        """
        # terminal test
        if self._is_checkmate(board, color):
            return -1000 if color == self.color else 1000
        if self._is_stalemate(board, color):
            return 0
        if depth == 0:
            return self._evaluate(board)

        moves = self._all_legal_moves(board, color)
        if not moves:                     # no moves -> stalemate or checkmate handled above
            return 0

        if maximizing:
            max_eval = -float('inf')
            for mv in moves:
                child = self._apply_move(board, mv)
                eval_ = self._minimax(child, self._opp(color), depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_)
                alpha = max(alpha, eval_)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for mv in moves:
                child = self._apply_move(board, mv)
                eval_ = self._minimax(child, self._opp(color), depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_)
                beta = min(beta, eval_)
                if beta <= alpha:
                    break
            return min_eval

    # --------------------------------------------------------------------- #
    #  Evaluation
    # --------------------------------------------------------------------- #
    def _evaluate(self, board):
        """Simple material + check bonus."""
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                val = self.PIECE_VALUE.get(piece.upper(), 0)
                if piece.isupper():
                    score += val
                else:
                    score -= val

        # small bonuses for delivering/receiving check
        if self._is_in_check(board, self._opp(self.color)):
            score += 0.5
        if self._is_in_check(board, self.color):
            score -= 0.5
        return score

    # --------------------------------------------------------------------- #
    #  Move generation & legality
    # --------------------------------------------------------------------- #
    def _all_legal_moves(self, board, color):
        """Return a list of Move tuples that are legal for `color`."""
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                if (color == 'W' and piece.isupper()) or (color == 'B' and piece.islower()):
                    moves.extend(self._piece_moves(board, r, c, piece))
        # filter out moves that leave own king in check
        legal = []
        for mv in moves:
            new_board = self._apply_move(board, mv)
            if not self._is_in_check(new_board, color):
                legal.append(mv)
        return legal

    def _piece_moves(self, board, r, c, piece):
        """Generate pseudo‑legal moves for a piece at (r,c)."""
        moves = []
        ptype = piece.upper()
        color = 'W' if piece.isupper() else 'B'
        dir_forward = 1 if color == 'W' else -1

        if ptype == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if self._in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not target or self._is_enemy(target, color):
                            moves.append((r, c, nr, nc, bool(target)))
        elif ptype == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear:
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not target or self._is_enemy(target, color):
                        moves.append((r, c, nr, nc, bool(target)))
        elif ptype == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not target:
                        moves.append((r, c, nr, nc, False))
                    elif self._is_enemy(target, color):
                        moves.append((r, c, nr, nc, True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        elif ptype == 'P':
            # forward move
            nc = c + dir_forward
            if self._in_bounds(r, nc) and board[r][nc] == '':
                moves.append((r, c, r, nc, False))
            # captures
            for dr in (-1, 1):
                nr = r + dr
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target and self._is_enemy(target, color):
                        moves.append((r, c, nr, nc, True))
        return moves

    # --------------------------------------------------------------------- #
    #  Board utilities
    # --------------------------------------------------------------------- #
    def _apply_move(self, board, move):
        """Return a new board after applying `move`."""
        fr, fc, tr, tc, _ = move
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]

        # move piece
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''

        # promotion
        if piece.upper() == 'P':
            if (piece.isupper() and tc == 7) or (piece.islower() and tc == 0):
                new_board[tr][tc] = 'R' if piece.isupper() else 'r'

        return new_board

    def _is_in_check(self, board, color):
        """True if `color`'s king is attacked."""
        king = 'K' if color == 'W' else 'k'
        king_pos = None
        for r in range(2):
            for c in range(8):
                if board[r][c] == king:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        if not king_pos:
            return True   # king missing -> treat as check

        opp = self._opp(color)
        # generate all opponent attacks (ignore own king safety)
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                if (opp == 'W' and piece.isupper()) or (opp == 'B' and piece.islower()):
                    for mv in self._piece_moves(board, r, c, piece):
                        _, _, tr, tc, _ = mv
                        if (tr, tc) == king_pos:
                            return True
        return False

    def _is_checkmate(self, board, color):
        """True if `color` is checkmated."""
        if not self._is_in_check(board, color):
            return False
        if self._all_legal_moves(board, color):
            return False
        return True

    def _is_stalemate(self, board, color):
        """True if `color` has no legal moves and is not in check."""
        if self._is_in_check(board, color):
            return False
        return not self._all_legal_moves(board, color)

    # --------------------------------------------------------------------- #
    #  Helpers
    # --------------------------------------------------------------------- #
    def _opp(self, color):
        return 'B' if color == 'W' else 'W'

    def _is_enemy(self, piece, color):
        return (color == 'W' and piece.islower()) or (color == 'B' and piece.isupper())

    def _in_bounds(self, r, c):
        return 0 <= r < 2 and 0 <= c < 8

    def _move_to_notation(self, move):
        """Convert internal move tuple to required algebraic notation."""
        fr, fc, tr, tc, is_capture = move
        piece = self.board_piece_at(fr, fc)   # temporary board reference not needed; we can infer from original board later
        # Since we don't have the original board here, we reconstruct piece type from move generation:
        # The calling code always supplies move generated from the current board, so we can
        # retrieve the piece type from the board passed to make_move via closure.
        # We'll therefore store the current board as an attribute before calling this method.
        piece_type = self._last_board[fr][fc].upper()
        from_sq = f"{self.COLS[fc]}{self.ROWS[fr]}"
        to_sq = f"{self.COLS[tc]}{self.ROWS[tr]}"
        if is_capture:
            return f"{piece_type}{from_sq}x{to_sq}"
        else:
            return f"{piece_type}{from_sq}{to_sq}"

    # The engine calls make_move with a fresh board each turn. To avoid passing the board
    # into _move_to_notation each time, we store it temporarily.
    def make_move(self, board, move_history):
        self._last_board = board  # store for notation helper
        # (rest of the method unchanged – see earlier definition)
        legal_moves = self._all_legal_moves(board, self.color)
        if not legal_moves:
            return "Kd1d2"

        best_score = -float('inf')
        best_moves = []

        for mv in legal_moves:
            new_board = self._apply_move(board, mv)
            score = self._minimax(new_board, self._opp(self.color), self.max_depth - 1,
                                  -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_moves = [mv]
            elif score == best_score:
                best_moves.append(mv)

        chosen = random.choice(best_moves)
        return self._move_to_notation(chosen)
