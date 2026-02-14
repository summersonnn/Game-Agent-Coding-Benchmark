"""
Agent Code: A7-TwoByEightChess
Model: z-ai-glm-5-fp8-speedy
Run: 2
Generated: 2026-02-14 13:30:59
"""

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.COLS = 'abcdefgh'
        self.piece_values = {'K': 10000, 'R': 500, 'N': 320, 'P': 100}
        self.search_depth = 5

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

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _pos_to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"

    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def _get_raw_moves(self, board, row, col):
        piece = board[row][col]
        if not piece:
            return []

        color = 'W' if self._is_white_piece(piece) else 'B'
        piece_type = piece.upper()
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
                            moves.append((row, col, nr, nc, piece_type, self._is_enemy_piece(target, color)))

        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        moves.append((row, col, nr, nc, piece_type, self._is_enemy_piece(target, color)))

        elif piece_type == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        moves.append((row, col, nr, nc, piece_type, False))
                    elif self._is_enemy_piece(target, color):
                        moves.append((row, col, nr, nc, piece_type, True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            nc = col + direction
            if self._in_bounds(row, nc) and board[row][nc] == '':
                moves.append((row, col, row, nc, piece_type, False))
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append((row, col, nr, nc, piece_type, True))

        return moves

    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if king_pos is None:
            return True
        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    for move in self._get_raw_moves(board, r, c):
                        if (move[2], move[3]) == king_pos:
                            return True
        return False

    def _make_move(self, board, move):
        fr, fc, tr, tc, piece_type, is_capture = move
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        if piece.upper() == 'P':
            color = 'W' if self._is_white_piece(piece) else 'B'
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                piece = 'R' if color == 'W' else 'r'
        new_board[tr][tc] = piece
        new_board[fr][fc] = ''
        return new_board

    def _is_legal_move(self, board, move, color):
        new_board = self._make_move(board, move)
        return not self._is_in_check(new_board, color)

    def _get_all_legal_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    for move in self._get_raw_moves(board, r, c):
                        if self._is_legal_move(board, move, color):
                            moves.append(move)
        return moves

    def evaluate(self, board, color):
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    piece_type = piece.upper()
                    value = self.piece_values[piece_type]
                    if piece_type == 'P':
                        value += c * 25 if self._is_white_piece(piece) else (7 - c) * 25
                    if piece_type == 'N':
                        if 2 <= c <= 5:
                            value += 15
                    if piece_type == 'R':
                        if self._is_white_piece(piece) and c >= 4:
                            value += 20
                        elif self._is_black_piece(piece) and c <= 3:
                            value += 20
                    score += value if self._is_white_piece(piece) else -value
        return score if color == 'W' else -score

    def minimax(self, board, depth, alpha, beta, color):
        if depth == 0:
            return self.evaluate(board, self.color)

        moves = self._get_all_legal_moves(board, color)

        if not moves:
            if self._is_in_check(board, color):
                return -100000 if color == self.color else 100000
            return 0

        enemy_color = 'B' if color == 'W' else 'W'
        moves.sort(key=lambda m: -int(m[5]))

        if color == self.color:
            max_eval = float('-inf')
            for move in moves:
                new_board = self._make_move(board, move)
                eval_score = self.minimax(new_board, depth - 1, alpha, beta, enemy_color)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = self._make_move(board, move)
                eval_score = self.minimax(new_board, depth - 1, alpha, beta, enemy_color)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def _move_to_notation(self, move):
        fr, fc, tr, tc, piece_type, is_capture = move
        from_sq = self._pos_to_notation(fr, fc)
        to_sq = self._pos_to_notation(tr, tc)
        return f"{piece_type}{from_sq}x{to_sq}" if is_capture else f"{piece_type}{from_sq}{to_sq}"

    def make_move(self, board, move_history):
        moves = self._get_all_legal_moves(board, self.color)
        if not moves:
            return None

        best_move = moves[0]
        best_score = float('-inf')
        enemy_color = 'B' if self.color == 'W' else 'W'

        for move in moves:
            new_board = self._make_move(board, move)
            score = self.minimax(new_board, self.search_depth, float('-inf'), float('inf'), enemy_color)
            if score > best_score:
                best_score = score
                best_move = move

        return self._move_to_notation(best_move)