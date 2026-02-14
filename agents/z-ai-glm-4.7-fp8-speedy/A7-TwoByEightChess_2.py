"""
Agent Code: A7-TwoByEightChess
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 2
Generated: 2026-02-14 13:30:59
"""

import copy

import random
import copy

class TwoByEightChessAgent:
    def __init__(self, name, color):
        """
        Initialize the agent.

        Args:
            name: str - The agent's name (e.g., "Agent-1")
            color: str - 'W' for White or 'B' for Black
        """
        self.name = name
        self.color = color
        self.COLS = 'abcdefgh'
        self.PIECE_VALUES = {'P': 100, 'N': 320, 'R': 500, 'K': 20000}
        self.SEARCH_DEPTH = 3

    def make_move(self, board, move_history):
        """
        Decide the next move based on the current board state.
        """
        valid_moves = self.get_all_valid_moves(board, self.color)
        
        if not valid_moves:
            return "Ka1a1" # Fallback move if no legal moves (should not happen in ongoing game)

        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        # Sort moves to improve alpha-beta pruning (captures first)
        valid_moves.sort(key=lambda m: self.get_move_order_score(board, m), reverse=True)

        for move in valid_moves:
            # Apply move to a copy of the board
            next_board = self.apply_move(board, move)
            
            # Perform search
            score = self.minimax(next_board, self.SEARCH_DEPTH - 1, alpha, beta, False)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        
        # Format the best move as a string
        return self.format_move(board, best_move)

    def get_move_order_score(self, board, move):
        """Simple heuristic to order moves: captures first."""
        fr, fc, tr, tc, piece = move
        target = board[tr][tc]
        if target:
            return self.PIECE_VALUES.get(target.upper(), 0)
        return 0

    def minimax(self, board, depth, alpha, beta, is_maximizing):
        current_color = self.color if is_maximizing else ('B' if self.color == 'W' else 'W')
        valid_moves = self.get_all_valid_moves(board, current_color)

        # Terminal state checks
        if not valid_moves:
            if self.is_check(board, current_color):
                # Checkmate
                return -100000 + (self.SEARCH_DEPTH - depth) if is_maximizing else 100000 - (self.SEARCH_DEPTH - depth)
            else:
                # Stalemate
                return 0

        if depth == 0:
            return self.evaluate(board)

        valid_moves.sort(key=lambda m: self.get_move_order_score(board, m), reverse=True)

        if is_maximizing:
            max_eval = -float('inf')
            for move in valid_moves:
                next_board = self.apply_move(board, move)
                eval_score = self.minimax(next_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid_moves:
                next_board = self.apply_move(board, move)
                eval_score = self.minimax(next_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate(self, board):
        score = 0
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                
                is_white = piece.isupper()
                piece_type = piece.upper()
                value = self.PIECE_VALUES[piece_type]
                
                # Positional bonuses
                if piece_type == 'P':
                    # Bonus for advanced pawns
                    if is_white:
                        value += c * 10
                    else:
                        value += (7 - c) * 10
                
                if is_white:
                    score += value
                else:
                    score -= value
        return score

    def get_all_valid_moves(self, board, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    if (color == 'W' and piece.isupper()) or (color == 'B' and piece.islower()):
                        moves.extend(self.get_piece_moves(board, r, c, piece))
        
        # Filter moves that leave King in check
        legal_moves = []
        for move in moves:
            fr, fc, tr, tc, piece = move
            
            # Simulate move
            target_piece = board[tr][tc]
            moving_piece = piece
            
            # Handle promotion in simulation
            if piece.upper() == 'P':
                if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                    moving_piece = 'R' if color == 'W' else 'r'
            
            board[tr][tc] = moving_piece
            board[fr][fc] = ''
            
            if not self.is_check(board, color):
                legal_moves.append(move)
            
            # Undo move
            board[fr][fc] = piece
            board[tr][tc] = target_piece
            
        return legal_moves

    def get_piece_moves(self, board, r, c, piece):
        moves = []
        piece_type = piece.upper()
        color = 'W' if piece.isupper() else 'B'
        is_white = (color == 'W')

        if piece_type == 'K':
            deltas = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target or (is_white != target.isupper()):
                        moves.append((r, c, nr, nc, piece))

        elif piece_type == 'N':
            # L-shape
            deltas = [(-1,-2), (-1,2), (1,-2), (1,2), (-2,-1), (-2,1), (2,-1), (2,1)]
            # Linear jump
            deltas.extend([(0,-2), (0,2)])
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target or (is_white != target.isupper()):
                        moves.append((r, c, nr, nc, piece))

        elif piece_type == 'R':
            directions = [(-1,0), (1,0), (0,-1), (0,1)]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 2 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target:
                        moves.append((r, c, nr, nc, piece))
                    else:
                        if is_white != target.isupper():
                            moves.append((r, c, nr, nc, piece))
                        break
                    nr += dr
                    nc += dc

        elif piece_type == 'P':
            direction = 1 if is_white else -1
            nc = c + direction
            if 0 <= nc < 8:
                # Move forward
                if board[r][nc] == '':
                    moves.append((r, c, r, nc, piece))
                # Capture
                for dr in [-1, 1]:
                    nr = r + dr
                    if 0 <= nr < 2:
                        target = board[nr][nc]
                        if target and is_white != target.isupper():
                            moves.append((r, c, nr, nc, piece))
        return moves

    def is_check(self, board, color):
        # Find King
        kr, kc = -1, -1
        king_char = 'K' if color == 'W' else 'k'
        for r in range(2):
            for c in range(8):
                if board[r][c] == king_char:
                    kr, kc = r, c
                    break
        
        if kr == -1: return False # Should not happen

        enemy_color = 'B' if color == 'W' else 'W'
        
        # Check if any enemy piece attacks the King
        for r in range(2):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    is_piece_white = piece.isupper()
                    if (enemy_color == 'W' and is_piece_white) or (enemy_color == 'B' and not is_piece_white):
                        if self.can_attack(board, r, c, kr, kc):
                            return True
        return False

    def can_attack(self, board, fr, fc, tr, tc):
        piece = board[fr][fc]
        piece_type = piece.upper()
        is_white = piece.isupper()
        
        dr = tr - fr
        dc = tc - fc

        if piece_type == 'K':
            return abs(dr) <= 1 and abs(dc) <= 1
        
        elif piece_type == 'N':
            if (abs(dr), abs(dc)) in [(1, 2), (2, 1)]: return True
            if dr == 0 and abs(dc) == 2: return True # Linear jump
            return False
        
        elif piece_type == 'R':
            if dr != 0 and dc != 0: return False
            step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
            step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
            
            curr_r, curr_c = fr + step_r, fc + step_c
            while (curr_r != tr or curr_c != tc):
                if board[curr_r][curr_c] != '': return False # Blocked
                curr_r += step_r
                curr_c += step_c
            return True
            
        elif piece_type == 'P':
            direction = 1 if is_white else -1
            if abs(dr) == 1 and dc == direction: return True
            return False
            
        return False

    def apply_move(self, board, move):
        """Returns a new board with the move applied."""
        new_board = [row[:] for row in board]
        fr, fc, tr, tc, piece = move
        color = 'W' if piece.isupper() else 'B'
        
        new_piece = piece
        # Handle Promotion
        if piece.upper() == 'P':
            if (color == 'W' and tc == 7) or (color == 'B' and tc == 0):
                new_piece = 'R' if color == 'W' else 'r'
                
        new_board[tr][tc] = new_piece
        new_board[fr][fc] = ''
        return new_board

    def format_move(self, board, move):
        """Converts internal move representation to string notation."""
        fr, fc, tr, tc, piece = move
        from_sq = self.COLS[fc] + str(fr + 1)
        to_sq = self.COLS[tc] + str(tc + 1)
        is_capture = board[tr][tc] != ''
        
        if is_capture:
            return f"{piece}{from_sq}x{to_sq}"
        else:
            return f"{piece}{from_sq}{to_sq}"
