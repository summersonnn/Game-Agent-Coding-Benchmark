"""
Agent Code: A7-1D_Chess
Model: qwen/qwen3-max-thinking
Run: 2
Generated: 2026-02-13 14:10:12
"""



class OneDChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def opponent_color(self):
        return 'B' if self.color == 'W' else 'W'

    def piece_value(self, piece):
        if piece in ['R', 'r']:
            return 5
        if piece in ['N', 'n']:
            return 3
        return 0

    def is_own_piece(self, piece, color):
        if not piece:
            return False
        if color == 'W':
            return piece in ['K', 'N', 'R']
        else:
            return piece in ['k', 'n', 'r']

    def is_enemy_piece(self, piece, color):
        if not piece:
            return False
        return not self.is_own_piece(piece, color)

    def find_king(self, board, color):
        king = 'K' if color == 'W' else 'k'
        for i, p in enumerate(board):
            if p == king:
                return i
        return -1

    def get_valid_moves_for_piece(self, board, pos, color, ignore_check=False):
        piece = board[pos]
        if not piece or not self.is_own_piece(piece, color):
            return []
        piece_type = piece.upper()
        moves = []
        if piece_type == 'K':
            for delta in [-1, 1]:
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    target = board[to_pos]
                    if not self.is_own_piece(target, color):
                        is_capture = self.is_enemy_piece(target, color)
                        moves.append((to_pos, is_capture))
        elif piece_type == 'N':
            for delta in [-2, 2]:
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    target = board[to_pos]
                    if not self.is_own_piece(target, color):
                        is_capture = self.is_enemy_piece(target, color)
                        moves.append((to_pos, is_capture))
        elif piece_type == 'R':
            for direction in [-1, 1]:
                to_pos = pos + direction
                while 0 <= to_pos < 8:
                    target = board[to_pos]
                    if target == '':
                        moves.append((to_pos, False))
                    elif self.is_enemy_piece(target, color):
                        moves.append((to_pos, True))
                        break
                    else:
                        break
                    to_pos += direction
        if ignore_check:
            return moves
        filtered_moves = []
        for to_pos, is_capture in moves:
            if self.is_move_safe(board, pos, to_pos, color):
                filtered_moves.append((to_pos, is_capture))
        return filtered_moves

    def is_move_safe(self, board, from_pos, to_pos, color):
        new_board = board.copy()
        piece = new_board[from_pos]
        new_board[to_pos] = piece
        new_board[from_pos] = ''
        return not self.is_in_check(new_board, color)

    def is_in_check(self, board, color):
        king_pos = self.find_king(board, color)
        if king_pos == -1:
            return True
        opp_color = self.opponent_color() if color == self.color else ('W' if color == 'B' else 'B')
        for pos in range(8):
            piece = board[pos]
            if piece and self.is_own_piece(piece, opp_color):
                moves = self.get_valid_moves_for_piece(board, pos, opp_color, ignore_check=True)
                for move_pos, _ in moves:
                    if move_pos == king_pos:
                        return True
        return False

    def has_legal_moves(self, board, color):
        for pos in range(8):
            piece = board[pos]
            if piece and self.is_own_piece(piece, color):
                if self.get_valid_moves_for_piece(board, pos, color):
                    return True
        return False

    def generate_all_legal_moves(self, board, color):
        moves = []
        for pos in range(8):
            piece = board[pos]
            if piece and self.is_own_piece(piece, color):
                piece_type = piece.upper()
                valid_moves = self.get_valid_moves_for_piece(board, pos, color)
                for to_pos, is_capture in valid_moves:
                    moves.append((pos, to_pos, piece_type, is_capture))
        return moves

    def simulate_move(self, board, move):
        from_pos, to_pos, _, _ = move
        new_board = board.copy()
        new_board[to_pos] = new_board[from_pos]
        new_board[from_pos] = ''
        return new_board

    def move_to_notation(self, move):
        from_pos, to_pos, piece_type, is_capture = move
        from_sq = from_pos + 1
        to_sq = to_pos + 1
        if is_capture:
            return f"{piece_type}{from_sq}x{to_sq}"
        else:
            return f"{piece_type}{from_sq}{to_sq}"

    def make_move(self, board, move_history):
        moves = self.generate_all_legal_moves(board, self.color)
        if not moves:
            return "K12"  # Fallback (should not occur in valid game states)

        # Check for immediate checkmate
        op_color = self.opponent_color()
        for move in moves:
            new_board = self.simulate_move(board, move)
            if self.is_in_check(new_board, op_color) and not self.has_legal_moves(new_board, op_color):
                return self.move_to_notation(move)

        # Evaluate moves: captures > checks > central control
        best_move = moves[0]
        best_score = -10**9
        for move in moves:
            score = 0
            from_pos, to_pos, piece_type, is_capture = move
            
            # Capture bonus (scaled by piece value)
            if is_capture:
                captured_piece = board[to_pos]
                score += (self.piece_value(captured_piece) + 1) * 1000
            
            # Check bonus
            new_board = self.simulate_move(board, move)
            if self.is_in_check(new_board, op_color):
                score += 2000
            
            # Central control bonus (squares 4 and 5 are most valuable)
            square_num = to_pos + 1
            if piece_type in ['N', 'R']:
                if square_num in [4, 5]:
                    score += 700
                elif square_num in [3, 6]:
                    score += 350
            
            # Prioritize king safety: avoid centralize king
            if piece_type == 'K':
                if square_num in [4, 5]:
                    score -= 1500
                elif square_num in [3, 6]:
                    score -= 500
            
            # Prefer moving from starting positions early
            if len(move_history) < 4:
                if self.color == 'W':
                    if from_pos == 1 and piece_type == 'N':  # White knight move
                        score += 1000
                    if from_pos == 2 and piece_type == 'R':  # White rook move
                        score += 800
                else:
                    if from_pos == 6 and piece_type == 'n':  # Black knight move
                        score += 1000
                    if from_pos == 5 and piece_type == 'r':  # Black rook move
                        score += 800
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return self.move_to_notation(best_move)
