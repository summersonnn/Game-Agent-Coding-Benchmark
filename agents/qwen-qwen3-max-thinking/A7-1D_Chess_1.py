"""
Agent Code: A7-1D_Chess
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-13 14:10:12
"""



class OneDChessAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color  # 'W' for White, 'B' for Black

    def make_move(self, board, move_history):
        # Generate all legal moves for my color
        legal_moves = self._get_legal_moves(board, self.color)
        
        # Safety check: if no legal moves (shouldn't occur in valid engine state)
        if not legal_moves:
            # Fallback: attempt any pseudo-legal move
            for pos in range(8):
                piece = board[pos]
                if not piece:
                    continue
                if (self.color == 'W' and self._is_white_piece(piece)) or (self.color == 'B' and self._is_black_piece(piece)):
                    piece_moves = self._get_moves_for_piece(board, pos)
                    if piece_moves:
                        to_pos, is_capture = piece_moves[0]
                        return self._move_to_notation(piece, pos, to_pos, is_capture)
            return "K12"  # Ultimate fallback (will be replaced by randomized move)
        
        # Immediate checkmate check: if any move checkmates opponent, take it
        for move in legal_moves:
            new_board = self._simulate_move(board, move[0], move[1])
            next_color = 'B' if self.color == 'W' else 'W'
            if self._is_checkmate(new_board, next_color):
                return self._move_to_notation_from_move(board, move)
        
        # Search for move using minimax with alpha-beta pruning (depth=2)
        best_score = -10**9
        best_move = legal_moves[0]
        alpha = -10**9
        beta = 10**9
        search_depth = 2  # Search 1 full move (2 plies)
        
        for move in legal_moves:
            new_board = self._simulate_move(board, move[0], move[1])
            next_color = 'B' if self.color == 'W' else 'W'
            score = self._minimax(new_board, search_depth, alpha, beta, next_color)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break
        
        return self._move_to_notation_from_move(board, best_move)
    
    def _is_white_piece(self, piece):
        return piece in ['K', 'N', 'R']
    
    def _is_black_piece(self, piece):
        return piece in ['k', 'n', 'r']
    
    def _get_piece_type(self, piece):
        return piece.upper() if piece else ''
    
    def _find_king(self, board, color):
        target = 'K' if color == 'W' else 'k'
        for i, p in enumerate(board):
            if p == target:
                return i
        return -1
    
    def _get_moves_for_piece(self, board, pos):
        piece = board[pos]
        if not piece:
            return []
        color = 'W' if self._is_white_piece(piece) else 'B'
        piece_type = self._get_piece_type(piece)
        moves = []
        
        if piece_type == 'K':
            for delta in (-1, 1):
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    target = board[to_pos]
                    if not target or (color == 'W' and self._is_black_piece(target)) or (color == 'B' and self._is_white_piece(target)):
                        is_capture = (target != '')
                        moves.append((to_pos, is_capture))
        
        elif piece_type == 'N':
            for delta in (-2, 2):
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    target = board[to_pos]
                    if not target or (color == 'W' and self._is_black_piece(target)) or (color == 'B' and self._is_white_piece(target)):
                        is_capture = (target != '')
                        moves.append((to_pos, is_capture))
        
        elif piece_type == 'R':
            for direction in (-1, 1):
                to_pos = pos + direction
                while 0 <= to_pos < 8:
                    target = board[to_pos]
                    if not target:
                        moves.append((to_pos, False))
                    elif (color == 'W' and self._is_black_piece(target)) or (color == 'B' and self._is_white_piece(target)):
                        moves.append((to_pos, True))
                        break
                    else:
                        break
                    to_pos += direction
        return moves
    
    def _is_in_check(self, board, color):
        king_pos = self._find_king(board, color)
        if king_pos == -1:
            return True
        opponent_color = 'B' if color == 'W' else 'W'
        for pos in range(8):
            piece = board[pos]
            if not piece:
                continue
            piece_color = 'W' if self._is_white_piece(piece) else 'B'
            if piece_color == opponent_color:
                moves = self._get_moves_for_piece(board, pos)
                for to_pos, _ in moves:
                    if to_pos == king_pos:
                        return True
        return False
    
    def _is_move_safe(self, board, from_pos, to_pos, color):
        new_board = board.copy()
        piece = new_board[from_pos]
        new_board[to_pos] = piece
        new_board[from_pos] = ''
        return not self._is_in_check(new_board, color)
    
    def _get_legal_moves(self, board, color):
        moves = []
        for pos in range(8):
            piece = board[pos]
            if not piece:
                continue
            if (color == 'W' and self._is_white_piece(piece)) or (color == 'B' and self._is_black_piece(piece)):
                piece_moves = self._get_moves_for_piece(board, pos)
                for to_pos, is_capture in piece_moves:
                    if self._is_move_safe(board, pos, to_pos, color):
                        moves.append((pos, to_pos, is_capture))
        return moves
    
    def _simulate_move(self, board, from_pos, to_pos):
        new_board = board.copy()
        piece = new_board[from_pos]
        new_board[to_pos] = piece
        new_board[from_pos] = ''
        return new_board
    
    def _is_checkmate(self, board, color):
        if not self._is_in_check(board, color):
            return False
        return len(self._get_legal_moves(board, color)) == 0
    
    def _is_stalemate(self, board, color):
        if self._is_in_check(board, color):
            return False
        return len(self._get_legal_moves(board, color)) == 0
    
    def _is_insufficient_material(self, board):
        for piece in board:
            if piece and self._get_piece_type(piece) != 'K':
                return False
        return True
    
    def _evaluate_board(self, board):
        piece_vals = {'R': 5, 'N': 3, 'r': 5, 'n': 3, 'K': 0, 'k': 0}
        agent_score = 0
        
        # Material count from agent's perspective
        if self.color == 'W':
            for p in board:
                if not p:
                    continue
                if self._is_white_piece(p):
                    agent_score += piece_vals[p]
                else:
                    agent_score -= piece_vals[p]
        else:
            for p in board:
                if not p:
                    continue
                if self._is_black_piece(p):
                    agent_score += piece_vals[p]
                else:
                    agent_score -= piece_vals[p]
        
        # Positional bonuses
        opponent_color = 'B' if self.color == 'W' else 'W'
        if self._is_in_check(board, opponent_color):
            agent_score += 1.5  # Opponent king under attack
        if self._is_in_check(board, self.color):
            agent_score -= 1.5  # Our king in danger
        
        return agent_score
    
    def _minimax(self, board, depth, alpha, beta, color_to_move):
        # Check immediate terminal states
        if self._is_checkmate(board, color_to_move):
            return 20000 if color_to_move != self.color else -20000
        if self._is_stalemate(board, color_to_move) or self._is_insufficient_material(board):
            return 0
        
        if depth == 0:
            return self._evaluate_board(board)
        
        moves = self._get_legal_moves(board, color_to_move)
        if not moves:
            return 0  # Stalemate or no moves (should be caught above, but defensive)
        
        if color_to_move == self.color:  # Maximizing player
            value = -10**9
            for move in moves:
                new_board = self._simulate_move(board, move[0], move[1])
                next_color = 'B' if color_to_move == 'W' else 'W'
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, next_color)
                value = max(value, eval_score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:  # Minimizing player
            value = 10**9
            for move in moves:
                new_board = self._simulate_move(board, move[0], move[1])
                next_color = 'B' if color_to_move == 'W' else 'W'
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, next_color)
                value = min(value, eval_score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value
    
    def _move_to_notation_from_move(self, board, move):
        from_pos, to_pos, is_capture = move
        piece = board[from_pos]
        piece_char = self._get_piece_type(piece)
        from_sq = from_pos + 1
        to_sq = to_pos + 1
        if is_capture:
            return f"{piece_char}{from_sq}x{to_sq}"
        return f"{piece_char}{from_sq}{to_sq}"
    
    def _move_to_notation(self, piece, from_pos, to_pos, is_capture):
        piece_char = self._get_piece_type(piece)
        from_sq = from_pos + 1
        to_sq = to_pos + 1
        if is_capture:
            return f"{piece_char}{from_sq}x{to_sq}"
        return f"{piece_char}{from_sq}{to_sq}"
