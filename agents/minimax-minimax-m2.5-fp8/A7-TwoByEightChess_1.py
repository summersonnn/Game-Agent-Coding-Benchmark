"""
Agent Code: A7-TwoByEightChess
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-14 13:30:59
"""



import random

class TwoByEightChessAgent:
    """
    Simple AI for 2×8 Mini Chess.
    Uses minimax (depth 2) with basic piece‑value evaluation,
    pawn‑promotion handling and check‑/checkmate detection.
    """

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color          # 'W' or 'B'
        # piece values (king is not given a value – it is handled by checkmate)
        self.piece_vals = {'K': 0, 'N': 3, 'R': 5, 'P': 1}

    # ----------------------------------------------------------------------
    # Board utilities
    # ----------------------------------------------------------------------
    @staticmethod
    def _notation(r: int, c: int) -> str:
        """Convert (row, col) into algebraic notation (e.g. 'a1')."""
        return chr(ord('a') + c) + str(r + 1)

    @staticmethod
    def _notation_to_pos(notation: str):
        """Convert algebraic notation into (row, col)."""
        if len(notation) != 2:
            return None
        col = ord(notation[0].lower()) - ord('a')
        if col < 0 or col > 7:
            return None
        try:
            row = int(notation[1]) - 1
        except ValueError:
            return None
        if row < 0 or row > 1:
            return None
        return (row, col)

    @staticmethod
    def _is_own_piece(piece: str, color: str) -> bool:
        """True if piece belongs to the given colour."""
        if not piece:
            return False
        return (color == 'W' and piece.isupper()) or (color == 'B' and piece.islower())

    # ----------------------------------------------------------------------
    # Move generation (pseudo‑legal, then filtered by legality)
    # ----------------------------------------------------------------------
    @staticmethod
    def _pseudo_moves(board, r: int, c: int):
        """
        Return a list of (to_row, to_col) squares that the piece at (r,c)
        can *pseudo*‑legally move to (ignoring king safety).
        """
        piece = board[r][c]
        if not piece:
            return []
        ptype = piece.upper()
        moves = []

        if ptype == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        moves.append((nr, nc))

        elif ptype == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    moves.append((nr, nc))

        elif ptype == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    moves.append((nr, nc))
                    if board[nr][nc]:
                        break
                    nr += dr
                    nc += dc

        elif ptype == 'P':
            direction = 1 if piece.isupper() else -1
            # forward (horizontal) move
            nc = c + direction
            if 0 <= nc < 8:
                if board[r][nc] == '':
                    moves.append((r, nc))
            # diagonal captures
            for dr in (-1, 1):
                nr = r + dr
                nc = c + direction
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target and ((piece.isupper() and target.islower()) or
                                   (piece.islower() and target.isupper())):
                        moves.append((nr, nc))
        return moves

    def _generate_all_legal_moves(self, board, color: str):
        """Return list of legal move strings for the given side."""
        legal_moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not self._is_own_piece(piece, color):
                    continue

                from_sq = self._notation(r, c)
                for tr, tc in self._pseudo_moves(board, r, c):
                    target = board[tr][tc]
                    if self._is_own_piece(target, color):
                        continue

                    # simulate the move
                    new_board = [row[:] for row in board]
                    new_board[tr][tc] = piece
                    new_board[r][c] = ''

                    # auto‑promotion
                    if piece.upper() == 'P':
                        if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                            new_board[tr][tc] = 'R' if color == 'W' else 'r'

                    # ensure own king is not left in check
                    if not self._is_check(new_board, color):
                        to_sq = self._notation(tr, tc)
                        is_capture = (target != '')
                        move_str = piece.upper() + from_sq + ('x' if is_capture else '') + to_sq
                        legal_moves.append(move_str)
        return legal_moves

    # ----------------------------------------------------------------------
    # Check / checkmate helpers
    # ----------------------------------------------------------------------
    def _find_king(self, board, color: str):
        """Return (row,col) of the king of the given colour."""
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _is_check(self, board, color: str) -> bool:
        """True if the king of the given colour is under attack."""
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True          # missing king -> in check (should not happen)

        opp_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not self._is_own_piece(piece, opp_color):
                    continue
                for tr, tc in self._pseudo_moves(board, r, c):
                    if (tr, tc) == king_pos:
                        return True
        return False

    def _has_legal_moves(self, board, color: str) -> bool:
        """True if the side has at least one legal move."""
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or not self._is_own_piece(piece, color):
                    continue
                for tr, tc in self._pseudo_moves(board, r, c):
                    target = board[tr][tc]
                    if self._is_own_piece(target, color):
                        continue
                    # simulate move
                    new_board = [row[:] for row in board]
                    new_board[tr][tc] = piece
                    new_board[r][c] = ''
                    if piece.upper() == 'P':
                        if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                            new_board[tr][tc] = 'R' if color == 'W' else 'r'
                    if not self._is_check(new_board, color):
                        return True
        return False

    # ----------------------------------------------------------------------
    # Move simulation (for minimax)
    # ----------------------------------------------------------------------
    def _simulate_move(self, board, move_str: str, color: str):
        """Return a new board after applying the move (including promotion)."""
        # parse move
        if 'x' in move_str.lower():
            idx = move_str.lower().index('x')
            from_sq = move_str[1:idx]
            to_sq = move_str[idx + 1:]
        else:
            from_sq = move_str[1:3]
            to_sq = move_str[3:5]

        fr, fc = self._notation_to_pos(from_sq)
        tr, tc = self._notation_to_pos(to_sq)
        if fr is None or tr is None:
            return [row[:] for row in board]   # fallback (should not happen)

        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''

        # promotion
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                new_board[tr][tc] = 'R' if color == 'W' else 'r'
        return new_board

    # ----------------------------------------------------------------------
    # Evaluation function
    # ----------------------------------------------------------------------
    def _evaluate(self, board) -> float:
        """Score from the perspective of the agent (positive = good for us)."""
        my_sum = 0
        opp_sum = 0

        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                ptype = piece.upper()
                val = self.piece_vals.get(ptype, 0)

                # promoted pawns become rooks
                if ptype == 'P':
                    if piece.isupper() and c == 7:
                        val = 5
                    elif piece.islower() and c == 0:
                        val = 5

                if self._is_own_piece(piece, self.color):
                    my_sum += val
                else:
                    opp_sum += val

        score = my_sum - opp_sum

        # opponent in check?
        opp_color = 'B' if self.color == 'W' else 'W'
        if self._is_check(board, opp_color):
            if not self._has_legal_moves(board, opp_color):
                score += 10000          # checkmate
            else:
                score += 10              # regular check

        # penalise being in check (should not happen after a legal move)
        if self._is_check(board, self.color):
            score -= 100

        # small bonus for pawns close to promotion
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece or piece.upper() != 'P':
                    continue
                if self._is_own_piece(piece, self.color):
                    distance = (7 - c) if piece.isupper() else c
                    score += (7 - distance) * 0.1

        return score

    # ----------------------------------------------------------------------
    # Minimax search
    # ----------------------------------------------------------------------
    def _minimax(self, board, depth: int, alpha: float, beta: float, maximizing: bool):
        """Recursive minimax. Returns (best_score, best_move)."""
        if depth == 0:
            return self._evaluate(board), None

        colour = self.color if maximizing else ('B' if self.color == 'W' else 'W')
        moves = self._generate_all_legal_moves(board, colour)

        # order moves: captures first, then checks (simple heuristic)
        moves.sort(key=lambda m: ('x' in m), reverse=True)

        if not moves:
            # no legal moves – treat as loss (or stalemate)
            if self._is_check(board, colour):
                return -10000, None
            else:
                return 0, None

        if maximizing:
            best_val = -10**9
            best_move = None
            for move in moves:
                new_board = self._simulate_move(board, move, colour)
                val, _ = self._minimax(new_board, depth - 1, alpha, beta, False)
                if val > best_val:
                    best_val = val
                    best_move = move
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_move
        else:
            best_val = 10**9
            best_move = None
            for move in moves:
                new_board = self._simulate_move(board, move, colour)
                val, _ = self._minimax(new_board, depth - 1, alpha, beta, True)
                if val < best_val:
                    best_val = val
                    best_move = move
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best_val, best_move

    # ----------------------------------------------------------------------
    # Main entry point
    # ----------------------------------------------------------------------
    def make_move(self, board, move_history):
        """
        Choose and return a legal move.
        Depth‑2 minimax with simple evaluation.
        """
        # generate all legal moves for our side
        my_moves = self._generate_all_legal_moves(board, self.color)

        if not my_moves:
            # should not happen (game should be over), but return a dummy move
            return "Ka1b1"

        # run minimax (depth 2 – good enough for the tiny board)
        _, best_move = self._minimax(board, depth=2,
                                      alpha=-10**9, beta=10**9,
                                      maximizing=True)

        if best_move is None:
            best_move = random.choice(my_moves)

        return best_move
