"""
Agent Code: A7-TwoByEightChess
Model: openai/gpt-5.2-codex
Run: 2
Generated: 2026-02-14 14:17:17
"""



class TwoByEightChessAgent:
    COLS = 'abcdefgh'
    PIECE_VALUES = {'K': 1000, 'R': 5, 'N': 3, 'P': 1}
    MATE_VALUE = 10000

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.tt = {}

    def make_move(self, board, move_history):
        self.tt = {}
        piece_count = sum(1 for row in board for p in row if p)
        if piece_count <= 4:
            depth = 6
        elif piece_count <= 6:
            depth = 5
        else:
            depth = 4

        moves = self.generate_moves(board, self.color)
        if not moves:
            return "Ka2a2"

        opp = self.opponent(self.color)

        # Immediate checkmate
        for move in moves:
            new_board = self.apply_move(board, move, self.color)
            if not self.generate_moves(new_board, opp) and self.is_in_check(new_board, opp):
                return self.move_to_notation(move)

        best_score = -float('inf')
        best_moves = []
        alpha = -float('inf')
        beta = float('inf')

        moves_sorted = sorted(moves, key=lambda m: m[6], reverse=True)
        for move in moves_sorted:
            new_board = self.apply_move(board, move, self.color)
            score = self.minimax(new_board, opp, depth - 1, alpha, beta)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
            if score > alpha:
                alpha = score

        chosen = random.choice(best_moves) if best_moves else moves_sorted[0]
        return self.move_to_notation(chosen)

    def opponent(self, color):
        return 'B' if color == 'W' else 'W'

    def in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def is_own_piece(self, piece, color):
        if not piece:
            return False
        return piece.isupper() if color == 'W' else piece.islower()

    def is_enemy_piece(self, piece, color):
        return piece != '' and not self.is_own_piece(piece, color)

    def find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target:
                    return (r, c)
        return None

    def is_in_check(self, board, color):
        king_pos = self.find_king(board, color)
        if king_pos is None:
            return True
        enemy = self.opponent(color)
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self.is_own_piece(piece, enemy):
                    moves = self.get_piece_moves(board, r, c, enemy, ignore_check=True)
                    for (nr, nc), _ in moves:
                        if (nr, nc) == king_pos:
                            return True
        return False

    def is_move_safe(self, board, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        new_board = [row[:] for row in board]
        piece = new_board[fr][fc]
        moving_piece = piece
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'
        new_board[tr][tc] = moving_piece
        new_board[fr][fc] = ''
        return not self.is_in_check(new_board, color)

    def get_piece_moves(self, board, row, col, color, ignore_check=False):
        piece = board[row][col]
        if not piece:
            return []
        piece_type = piece.upper()
        moves = []

        if piece_type == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self.in_bounds(nr, nc):
                        target = board[nr][nc]
                        if not self.is_own_piece(target, color):
                            moves.append(((nr, nc), self.is_enemy_piece(target, color)))
        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear:
                nr, nc = row + dr, col + dc
                if self.in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not self.is_own_piece(target, color):
                        moves.append(((nr, nc), self.is_enemy_piece(target, color)))
        elif piece_type == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self.in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == '':
                        moves.append(((nr, nc), False))
                    elif self.is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        elif piece_type == 'P':
            direction = 1 if color == 'W' else -1
            nc = col + direction
            if self.in_bounds(row, nc) and board[row][nc] == '':
                moves.append(((row, nc), False))
            for dr in (-1, 1):
                nr = row + dr
                nc = col + direction
                if self.in_bounds(nr, nc):
                    target = board[nr][nc]
                    if self.is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))

        if ignore_check:
            return moves

        valid = []
        for to_pos, is_cap in moves:
            if self.is_move_safe(board, (row, col), to_pos, color):
                valid.append((to_pos, is_cap))
        return valid

    def generate_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self.is_own_piece(piece, color):
                    pmoves = self.get_piece_moves(board, r, c, color, ignore_check=False)
                    for (nr, nc), is_cap in pmoves:
                        order_val = 0
                        if is_cap:
                            target = board[nr][nc]
                            if target:
                                order_val += self.PIECE_VALUES[target.upper()]
                        if piece.upper() == 'P':
                            if (color == 'W' and nc == 7) or (color == 'B' and nc == 0):
                                order_val += self.PIECE_VALUES['R']
                        moves.append((r, c, nr, nc, is_cap, piece, order_val))
        return moves

    def apply_move(self, board, move, color):
        fr, fc, tr, tc, _, piece, _ = move
        new_board = [row[:] for row in board]
        moving_piece = piece
        if moving_piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                moving_piece = 'R' if color == 'W' else 'r'
        new_board[tr][tc] = moving_piece
        new_board[fr][fc] = ''
        return new_board

    def board_key(self, board):
        return tuple(board[0]) + tuple(board[1])

    def minimax(self, board, color, depth, alpha, beta):
        key = (self.board_key(board), color, depth)
        if key in self.tt:
            return self.tt[key]

        legal_moves = self.generate_moves(board, color)
        if depth == 0 or not legal_moves:
            if not legal_moves:
                if self.is_in_check(board, color):
                    val = -self.MATE_VALUE - depth if color == self.color else self.MATE_VALUE + depth
                else:
                    val = 0
            else:
                val = self.evaluate(board)
            self.tt[key] = val
            return val

        if color == self.color:
            value = -float('inf')
            moves_sorted = sorted(legal_moves, key=lambda m: m[6], reverse=True)
            for move in moves_sorted:
                new_board = self.apply_move(board, move, color)
                value = max(value, self.minimax(new_board, self.opponent(color), depth - 1, alpha, beta))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
        else:
            value = float('inf')
            moves_sorted = sorted(legal_moves, key=lambda m: m[6], reverse=True)
            for move in moves_sorted:
                new_board = self.apply_move(board, move, color)
                value = min(value, self.minimax(new_board, self.opponent(color), depth - 1, alpha, beta))
                beta = min(beta, value)
                if beta <= alpha:
                    break

        self.tt[key] = value
        return value

    def evaluate(self, board):
        score = 0.0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                val = self.PIECE_VALUES[piece.upper()]
                if piece.upper() == 'P':
                    adv = c if piece.isupper() else 7 - c
                    val += 0.1 * adv
                elif piece.upper() == 'R':
                    adv = c if piece.isupper() else 7 - c
                    val += 0.05 * adv
                elif piece.upper() == 'N':
                    val += 0.05 * (3.5 - abs(c - 3.5))
                if self.is_own_piece(piece, self.color):
                    score += val
                else:
                    score -= val
        if self.is_in_check(board, self.color):
            score -= 0.2
        if self.is_in_check(board, self.opponent(self.color)):
            score += 0.2
        return score

    def move_to_notation(self, move):
        fr, fc, tr, tc, is_cap, piece, _ = move
        piece_type = piece.upper()
        from_sq = self.COLS[fc] + str(fr + 1)
        to_sq = self.COLS[tc] + str(tr + 1)
        return f"{piece_type}{from_sq}x{to_sq}" if is_cap else f"{piece_type}{from_sq}{to_sq}"
