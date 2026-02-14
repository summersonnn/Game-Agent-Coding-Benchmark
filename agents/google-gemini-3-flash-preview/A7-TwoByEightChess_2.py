"""
Agent Code: A7-TwoByEightChess
Model: google-gemini-3-flash-preview
Run: 2
Generated: 2026-02-14 13:16:13
"""

import random

class TwoByEightChessAgent:
    def __init__(self, name, color):
        """
        Initialize the agent.
        """
        self.name = name
        self.color = color
        self.piece_values = {
            'K': 1000,
            'R': 5,
            'N': 3,
            'P': 1
        }

    def make_move(self, board, move_history):
        """
        Decide the next move using a basic minimax-style evaluation.
        """
        valid_moves = self._get_all_legal_moves(board, self.color)
        
        if not valid_moves:
            return ""

        # Simple Greedy Strategy: prioritize captures and promotions
        best_move = None
        max_score = -float('inf')

        # Shuffle to ensure variety in non-obvious positions
        random.shuffle(valid_moves)

        for move_str in valid_moves:
            score = self._evaluate_move(board, move_str)
            if score > max_score:
                max_score = score
                best_move = move_str

        return best_move

    def _evaluate_move(self, board, move_str):
        """
        Assigns a score to a move based on captures and tactical positioning.
        """
        score = 0
        parsed = self._parse_move_string(move_str)
        if not parsed:
            return -100
        
        piece_type, (fr, fc), (tr, tc), is_capture = parsed
        
        # 1. Capture Value
        if is_capture:
            target_piece = board[tr][tc].upper()
            score += self.piece_values.get(target_piece, 0) * 10

        # 2. Promotion Value
        if piece_type == 'P':
            if (self.color == 'W' and tc == 7) or (self.color == 'B' and tc == 0):
                score += 8  # Significant bonus for turning Pawn into Rook

        # 3. Position: Favor advancement
        if self.color == 'W':
            score += tc * 0.1
        else:
            score += (7 - tc) * 0.1

        # 4. Check/Checkmate logic
        # Simulate move to see if it puts opponent in check (simple proxy for strength)
        new_board = [row[:] for row in board]
        new_board[tr][tc] = board[fr][fc]
        new_board[fr][fc] = ''
        
        if self._is_in_check(new_board, 'B' if self.color == 'W' else 'W'):
            score += 2

        return score

    def _get_all_legal_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_type = piece.upper()
                    from_sq = self._pos_to_notation(r, c)
                    for to_pos, is_capture in self._get_piece_pseudo_moves(board, r, c):
                        if self._is_move_safe(board, (r, c), to_pos, color):
                            to_sq = self._pos_to_notation(to_pos[0], to_pos[1])
                            notation = f"{piece_type}{from_sq}{'x' if is_capture else ''}{to_sq}"
                            moves.append(notation)
        return moves

    def _get_piece_pseudo_moves(self, board, row, col):
        piece = board[row][col]
        color = 'W' if piece.isupper() else 'B'
        piece_type = piece.upper()
        moves = []

        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 2 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if not self._is_own_piece(target, color):
                            moves.append(((nr, nc), target != ''))

        elif piece_type == 'N':
            deltas = [(-1,-2),(-1,2),(1,-2),(1,2),(-2,-1),(-2,1),(2,-1),(2,1),(0,-2),(0,2)]
            for dr, dc in deltas:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not self._is_own_piece(target, color):
                        moves.append(((nr, nc), target != ''))

        elif piece_type == 'R':
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = row + dr, col + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == '':
                        moves.append(((nr, nc), False))
                    elif not self._is_own_piece(target, color):
                        moves.append(((nr, nc), True))
                        break
                    else: break
                    nr, nc = nr + dr, nc + dc

        elif piece_type == 'P':
            dir = 1 if color == 'W' else -1
            nc = col + dir
            if 0 <= nc < 8 and board[row][nc] == '':
                moves.append(((row, nc), False))
            for dr in [-1, 1]:
                nr, nc = row + dr, col + dir
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target != '' and not self._is_own_piece(target, color):
                        moves.append(((nr, nc), True))
        return moves

    def _is_move_safe(self, board, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        sim_board = [row[:] for row in board]
        piece = sim_board[fr][fc]
        # Auto-promotion in simulation
        if piece.upper() == 'P' and (tc == 7 or tc == 0):
            piece = 'R' if color == 'W' else 'r'
        sim_board[tr][tc] = piece
        sim_board[fr][fc] = ''
        return not self._is_in_check(sim_board, color)

    def _is_in_check(self, board, color):
        king_pos = None
        target_king = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == target_king:
                    king_pos = (r, c)
                    break
        if not king_pos: return True
        
        enemy_color = 'B' if color == 'W' else 'W'
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and not self._is_own_piece(piece, color):
                    # Check if any enemy pseudo-move can hit king_pos
                    for (tr, tc), _ in self._get_piece_pseudo_moves(board, r, c):
                        if (tr, tc) == king_pos:
                            return True
        return False

    def _is_own_piece(self, piece, color):
        if not piece: return False
        return piece.isupper() if color == 'W' else piece.islower()

    def _pos_to_notation(self, row, col):
        return f"{'abcdefgh'[col]}{row + 1}"

    def _parse_move_string(self, move_str):
        try:
            piece = move_str[0]
            is_capture = 'x' in move_str
            if is_capture:
                parts = move_str[1:].split('x')
                fr_sq, tr_sq = parts[0], parts[1]
            else:
                fr_sq, tr_sq = move_str[1:3], move_str[3:5]
            
            f_col, f_row = 'abcdefgh'.index(fr_sq[0]), int(fr_sq[1]) - 1
            t_col, t_row = 'abcdefgh'.index(tr_sq[0]), int(tr_sq[1]) - 1
            return piece, (f_row, f_col), (t_row, t_col), is_capture
        except:
            return None