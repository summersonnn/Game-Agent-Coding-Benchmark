"""
Agent Code: A7-TwoByEightChess
Model: x-ai/grok-code-fast-1
Run: 2
Generated: 2026-02-14 13:30:59
"""

import copy

import random
import copy

class TwoByEightChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, board, move_history):
        my_pieces = ('K', 'N', 'R', 'P') if self.color == 'W' else ('k', 'n', 'r', 'p')
        enemy_pieces = ('k', 'n', 'r', 'p') if self.color == 'W' else ('K', 'N', 'R', 'P')
        COLS = 'abcdefgh'

        def in_bounds(r, c):
            return 0 <= r < 2 and 0 <= c < 8

        def pos_to_notation(r, c):
            return f"{COLS[c]}{r + 1}"

        def notation_to_pos(s):
            c = COLS.index(s[0].lower())
            r = int(s[1]) - 1
            return r, c

        def is_my_piece(piece):
            return piece in my_pieces

        def is_enemy_piece(piece):
            return piece != '' and piece in enemy_pieces

        def is_square_attacked(r, c, board_copy):
            for rr in range(2):
                for cc in range(8):
                    p = board_copy[rr][cc]
                    if p in enemy_pieces:
                        pt = p.upper()
                        if pt == 'K':
                            for dr in [-1, 0, 1]:
                                for dc in [-1, 0, 1]:
                                    if dr == 0 and dc == 0:
                                        continue
                                    nr, nc = rr + dr, cc + dc
                                    if nr == r and nc == c:
                                        return True
                        elif pt == 'N':
                            deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1), (0, -2), (0, 2)]
                            for dr, dc in deltas:
                                nr, nc = rr + dr, cc + dc
                                if nr == r and nc == c:
                                    return True
                        elif pt == 'R':
                            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                nr, nc = rr + dr, cc + dc
                                while in_bounds(nr, nc):
                                    if nr == r and nc == c:
                                        return True
                                    if board_copy[nr][nc] != '':
                                        break
                                    nr += dr
                                    nc += dc
                        elif pt == 'P':
                            dir = 1 if p == 'P' else -1
                            for dr in [-1, 1]:
                                nr = rr + dr
                                nc = cc + dir
                                if nr == r and nc == c:
                                    return True
            return False

        def find_king(board_copy):
            king = 'K' if self.color == 'W' else 'k'
            for r in range(2):
                for c in range(8):
                    if board_copy[r][c] == king:
                        return r, c
            return None

        def get_valid_moves_for_piece(r, c, board_copy):
            piece = board_copy[r][c]
            if not piece or not is_my_piece(piece):
                return []
            pt = piece.upper()
            moves = []
            if pt == 'K':
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if in_bounds(nr, nc) and not is_my_piece(board_copy[nr][nc]):
                            is_cap = is_enemy_piece(board_copy[nr][nc])
                            moves.append((nr, nc, is_cap))
            elif pt == 'N':
                deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1), (0, -2), (0, 2)]
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and not is_my_piece(board_copy[nr][nc]):
                        is_cap = is_enemy_piece(board_copy[nr][nc])
                        moves.append((nr, nc, is_cap))
            elif pt == 'R':
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    while in_bounds(nr, nc):
                        if board_copy[nr][nc] == '':
                            moves.append((nr, nc, False))
                        elif is_enemy_piece(board_copy[nr][nc]):
                            moves.append((nr, nc, True))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc
            elif pt == 'P':
                dir = 1 if self.color == 'W' else -1
                nr, nc = r, c + dir
                if in_bounds(r, nc) and board_copy[r][nc] == '':
                    moves.append((r, nc, False))
                for dr in [-1, 1]:
                    nr = r + dr
                    nc = c + dir
                    if in_bounds(nr, nc) and is_enemy_piece(board_copy[nr][nc]):
                        moves.append((nr, nc, True))
            valid = []
            for nr, nc, is_cap in moves:
                # Simulate move
                original_from = board_copy[r][c]
                original_to = board_copy[nr][nc]
                board_copy[nr][nc] = original_from
                board_copy[r][c] = ''
                # Promotion
                if pt == 'P' and ((self.color == 'W' and nc == 7) or (self.color == 'B' and nc == 0)):
                    board_copy[nr][nc] = 'R' if self.color == 'W' else 'r'
                king_pos = find_king(board_copy)
                if king_pos and not is_square_attacked(king_pos[0], king_pos[1], board_copy):
                    valid.append((nr, nc, is_cap))
                # Undo
                board_copy[r][c] = original_from
                board_copy[nr][nc] = original_to
            return valid

        all_moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if is_my_piece(piece):
                    valid_moves = get_valid_moves_for_piece(r, c, copy.deepcopy(board))
                    piece_type = piece.upper()
                    from_sq = pos_to_notation(r, c)
                    for nr, nc, is_cap in valid_moves:
                        to_sq = pos_to_notation(nr, nc)
                        if is_cap:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        all_moves.append(move_str)

        if all_moves:
            return random.choice(all_moves)
        else:
            # Fallback, though shouldn't happen
            return "Ka2b2"  # Example, but adjust if needed
