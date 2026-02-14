"""
Agent Code: A7-TwoByEightChess
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-14 13:30:59
"""



class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.opp_color = 'B' if color == 'W' else 'W'
        self.COLS = 'abcdefgh'
        self.piece_values = {
            'P': 1, 'N': 3, 'R': 5, 'K': 0,
            'p': -1, 'n': -3, 'r': -5, 'k': 0
        }

    def _pos_to_notation(self, row, col):
        return self.COLS[col] + str(row + 1)

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _is_white(self, piece):
        return piece.isupper() and piece != ''

    def _is_black(self, piece):
        return piece.islower() and piece != ''

    def _is_own(self, piece, color):
        return (color == 'W' and self._is_white(piece)) or (color == 'B' and self._is_black(piece))

    def _is_enemy(self, piece, color):
        return piece != '' and not self._is_own(piece, color)

    def _piece_type(self, piece):
        return piece.upper()

    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _get_moves_for_piece(self, board, row, col, color, ignore_check=False):
        piece = board[row][col]
        if not piece or not self._is_own(piece, color):
            return []
        pt = self._piece_type(piece)
        moves = []
        if pt == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc) and not self._is_own(board[nr][nc], color):
                        is_cap = self._is_enemy(board[nr][nc], color)
                        moves.append(((nr, nc), is_cap))
        elif pt == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]
            lin_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + lin_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc) and not self._is_own(board[nr][nc], color):
                    is_cap = self._is_enemy(board[nr][nc], color)
                    moves.append(((nr, nc), is_cap))
        elif pt == 'R':
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    t = board[nr][nc]
                    if t == '':
                        moves.append(((nr, nc), False))
                        nr += dr
                        nc += dc
                        continue
                    if self._is_enemy(t, color):
                        moves.append(((nr, nc), True))
                    break
        elif pt == 'P':
            dir_ = 1 if color == 'W' else -1
            nc = col + dir_
            if self._in_bounds(row, nc) and board[row][nc] == '':
                moves.append(((row, nc), False))
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + dir_
                if self._in_bounds(nr, nc) and self._is_enemy(board[nr][nc], color):
                    moves.append(((nr, nc), True))
        if ignore_check:
            return moves
        valid = []
        for to_pos, is_cap in moves:
            if self._is_safe(board, (row, col), to_pos, color):
                valid.append((to_pos, is_cap))
        return valid

    def _is_safe(self, board, from_pos, to_pos, color):
        b = [row[:] for row in board]
        r, c = from_pos
        tr, tc = to_pos
        piece = b[r][c]
        pt = self._piece_type(piece)
        if pt == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                piece = 'R' if color == 'W' else 'r'
        b[tr][tc] = piece
        b[r][c] = ''
        return not self._is_in_check(b, color)

    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if not king_pos:
            return True
        opp = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                if self._is_own(board[r][c], opp):
                    att_moves = self._get_moves_for_piece(board, r, c, opp, ignore_check=True)
                    for to_pos, _ in att_moves:
                        if to_pos == king_pos:
                            return True
        return False

    def _has_legal_moves(self, board, color):
        for r in range(2):
            for c in range(8):
                if self._is_own(board[r][c], color):
                    if self._get_moves_for_piece(board, r, c, color):
                        return True
        return False

    def _is_insufficient(self, board):
        for r in range(2):
            for c in range(8):
                if board[r][c] and self._piece_type(board[r][c]) != 'K':
                    return False
        return True

    def _evaluate(self, board):
        score = 0
        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if p:
                    score += self.piece_values[p]
        pawn_advance = 0
        for r in range(2):
            for c in range(8):
                p = board[r][c]
                if p == 'P':
                    pawn_advance += c
                elif p == 'p':
                    pawn_advance -= (7 - c)
        score += pawn_advance * 0.3
        if self.color == 'B':
            return -score
        return score

    def _get_all_actions(self, board, color):
        actions = []
        for r in range(2):
            for c in range(8):
                if self._is_own(board[r][c], color):
                    for to_pos, is_cap in self._get_moves_for_piece(board, r, c, color):
                        actions.append(((r, c), to_pos, is_cap))
        return actions

    def _minimax(self, board, depth, alpha, beta, is_self_turn):
        if depth == 0:
            return self._evaluate(board)
        if self._is_insufficient(board):
            return 0
        current_color = self.color if is_self_turn else self.opp_color
        in_check = self._is_in_check(board, current_color)
        actions = self._get_all_actions(board, current_color)
        if not actions:
            if in_check:
                return -100000 if is_self_turn else 100000
            else:
                return 0
        actions.sort(key=lambda x: x[2], reverse=True)
        if is_self_turn:
            max_eval = -float('inf')
            for action in actions:
                from_pos, to_pos, _ = action
                b_copy = [row[:] for row in board]
                r, c = from_pos
                tr, tc = to_pos
                piece = b_copy[r][c]
                if self._piece_type(piece) == 'P':
                    if (current_color == 'W' and tc == 7) or (current_color == 'B' and tc == 0):
                        piece = 'R' if current_color == 'W' else 'r'
                b_copy[tr][tc] = piece
                b_copy[r][c] = ''
                eval_ = self._minimax(b_copy, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_)
                alpha = max(alpha, eval_)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for action in actions:
                from_pos, to_pos, _ = action
                b_copy = [row[:] for row in board]
                r, c = from_pos
                tr, tc = to_pos
                piece = b_copy[r][c]
                if self._piece_type(piece) == 'P':
                    if (current_color == 'W' and tc == 7) or (current_color == 'B' and tc == 0):
                        piece = 'R' if current_color == 'W' else 'r'
                b_copy[tr][tc] = piece
                b_copy[r][c] = ''
                eval_ = self._minimax(b_copy, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_)
                beta = min(beta, eval_)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, board, move_history):
        depth = 5
        actions = self._get_all_actions(board, self.color)
        if not actions:
            return ""
        actions.sort(key=lambda x: x[2], reverse=True)
        best_score = -float('inf')
        best_move = None
        for action in actions:
            from_pos, to_pos, is_cap = action
            b_copy = [row[:] for row in board]
            r, c = from_pos
            tr, tc = to_pos
            piece = b_copy[r][c]
            pt = self._piece_type(piece)
            if pt == 'P':
                if (self.color == 'W' and tc == 7) or (self.color == 'B' and tc == 0):
                    piece = 'R' if self.color == 'W' else 'r'
            b_copy[tr][tc] = piece
            b_copy[r][c] = ''
            score = self._minimax(b_copy, depth - 1, -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                from_sq = self._pos_to_notation(r, c)
                to_sq = self._pos_to_notation(tr, tc)
                move_str = f"{pt}{from_sq}{'x' if is_cap else ''}{to_sq}"
                best_move = move_str
        return best_move
