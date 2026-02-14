"""
Agent Code: A7-TwoByEightChess
Model: google-gemini-3-flash-preview
Run: 1
Generated: 2026-02-14 13:16:13
"""

import random
import copy

class TwoByEightChessAgent:
    def __init__(self, name, color):
        """
        Initialize the 2x8 Mini Chess agent.
        """
        self.name = name
        self.color = color
        self.enemy_color = 'B' if color == 'W' else 'W'
        self.piece_values = {'K': 1000, 'R': 10, 'N': 6, 'P': 2}

    def make_move(self, board, move_history):
        """
        Decide the next move using a basic minimax algorithm with alpha-beta pruning.
        """
        valid_moves = self._get_all_legal_moves(board, self.color)
        
        if not valid_moves:
            return ""

        best_move = valid_moves[0]
        best_value = -float('inf')
        
        # Simple search depth of 3 for 1-second timeout safety
        depth = 3
        alpha = -float('inf')
        beta = float('inf')

        for move in valid_moves:
            temp_board = self._simulate_move(board, move)
            board_val = self._minimax(temp_board, depth - 1, alpha, beta, False)
            if board_val > best_value:
                best_value = board_val
                best_move = move
            alpha = max(alpha, best_value)
            
        return best_move

    def _minimax(self, board, depth, alpha, beta, is_maximizing):
        if depth == 0 or self._is_terminal(board):
            return self._evaluate_board(board)

        if is_maximizing:
            max_eval = -float('inf')
            for move in self._get_all_legal_moves(board, self.color):
                eval = self._minimax(self._simulate_move(board, move), depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in self._get_all_legal_moves(board, self.enemy_color):
                eval = self._minimax(self._simulate_move(board, move), depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate_board(self, board):
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                
                val = self.piece_values.get(piece.upper(), 0)
                # Position bonus: Encourage pawns to advance
                if piece.upper() == 'P':
                    bonus = c if piece.isupper() else (7 - c)
                    val += bonus * 0.5

                if (self.color == 'W' and piece.isupper()) or (self.color == 'B' and piece.islower()):
                    score += val
                else:
                    score -= val
        return score

    def _get_all_legal_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece and self._is_own_piece(piece, color):
                    moves.extend(self._get_piece_moves(board, r, c, color))
        return moves

    def _get_piece_moves(self, board, row, col, color):
        piece = board[row][col]
        p_type = piece.upper()
        moves = []
        
        # Potential destinations based on piece type
        candidates = [] # list of (nr, nc, jump_allowed)
        
        if p_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr != 0 or dc != 0: candidates.append((row + dr, col + dc))
        elif p_type == 'N':
            deltas = [(-1,-2),(-1,2),(1,-2),(1,2),(-2,-1),(-2,1),(2,-1),(2,1),(0,-2),(0,2)]
            for dr, dc in deltas: candidates.append((row + dr, col + dc))
        elif p_type == 'R':
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = row + dr, col + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target: candidates.append((nr, nc))
                    elif self._is_enemy_piece(target, color):
                        candidates.append((nr, nc))
                        break
                    else: break
                    nr, nc = nr + dr, nc + dc
        elif p_type == 'P':
            dir = 1 if color == 'W' else -1
            # Forward
            if 0 <= col + dir < 8 and not board[row][col + dir]:
                candidates.append((row, col + dir))
            # Captures
            for dr in [-1, 1]:
                nr, nc = row + dr, col + dir
                if 0 <= nr < 2 and 0 <= nc < 8:
                    if board[nr][nc] and self._is_enemy_piece(board[nr][nc], color):
                        candidates.append((nr, nc))

        # Filter candidates and format notation
        from_sq = f"{'abcdefgh'[col]}{row + 1}"
        for nr, nc in candidates:
            if p_type != 'R' and not (0 <= nr < 2 and 0 <= nc < 8): continue
            target = board[nr][nc]
            if self._is_own_piece(target, color): continue
            
            to_sq = f"{'abcdefgh'[nc]}{nr + 1}"
            move_str = f"{p_type}{from_sq}{'x' if target else ''}{to_sq}"
            
            # Simple check: Does this move leave the king vulnerable? 
            # (In a full engine we'd simulate, here we filter roughly)
            moves.append(move_str)
            
        return moves

    def _simulate_move(self, board, move_str):
        new_board = copy.deepcopy(board)
        # Basic parser for simulation
        p_type = move_str[0]
        is_cap = 'x' in move_str
        f_col = ord(move_str[1]) - ord('a')
        f_row = int(move_str[2]) - 1
        t_col = ord(move_str[-2]) - ord('a')
        t_row = int(move_str[-1]) - 1
        
        piece = new_board[f_row][f_col]
        new_board[f_row][f_col] = ''
        
        # Promotion logic
        if p_type == 'P' and (t_col == 7 or t_col == 0):
            piece = 'R' if piece.isupper() else 'r'
            
        new_board[t_row][t_col] = piece
        return new_board

    def _is_terminal(self, board):
        # Rough terminal check: is a king missing?
        kings = 0
        for r in board:
            for p in r:
                if p.upper() == 'K': kings += 1
        return kings < 2

    def _is_own_piece(self, p, color):
        if not p: return False
        return p.isupper() if color == 'W' else p.islower()

    def _is_enemy_piece(self, p, color):
        if not p: return False
        return p.islower() if color == 'W' else p.isupper()