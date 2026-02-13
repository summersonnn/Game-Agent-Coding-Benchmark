"""
Agent Code: A2-TicTacToe
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        self.winning_lines = self._precompute_winning_lines()
        
    def _precompute_winning_lines(self):
        """Precompute all possible winning lines (3 in a row) on 5x5 board"""
        lines = []
        # Rows (5 rows, each with 3 possible 3-in-a-row segments)
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))
        # Columns (5 columns, each with 3 possible 3-in-a-row segments)
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))
        return lines
    
    def _evaluate_board(self, board, player):
        """Evaluate board state for given player"""
        score = 0
        
        # Check for immediate win
        for line in self.winning_lines:
            cells = [board[i] for i in line]
            if cells.count(player) == 3:
                return 1000  # Winning move
            if cells.count(player) == 2 and cells.count(' ') == 1:
                score += 10  # Two in a row with open end
            if cells.count(self.opponent_symbol) == 2 and cells.count(' ') == 1:
                score -= 15  # Opponent threat - block is important
        
        # Center control (positions 6,7,8,11,12,13,16,17,18)
        center_positions = [6,7,8,11,12,13,16,17,18]
        for pos in center_positions:
            if board[pos] == player:
                score += 1
            elif board[pos] == self.opponent_symbol:
                score -= 1
        
        # Corner control (positions 0,4,20,24)
        corners = [0,4,20,24]
        for pos in corners:
            if board[pos] == player:
                score += 1
            elif board[pos] == self.opponent_symbol:
                score -= 1
        
        return score
    
    def _get_available_moves(self, board):
        """Return list of available moves"""
        return [i for i, cell in enumerate(board) if cell == ' ']
    
    def _check_immediate_win(self, board, player):
        """Check if there's a winning move for player"""
        for move in self._get_available_moves(board):
            new_board = board.copy()
            new_board[move] = player
            for line in self.winning_lines:
                cells = [new_board[i] for i in line]
                if cells.count(player) == 3:
                    return move
        return None
    
    def _check_opponent_threat(self, board):
        """Check if opponent can win next move and block it"""
        for move in self._get_available_moves(board):
            new_board = board.copy()
            new_board[move] = self.opponent_symbol
            for line in self.winning_lines:
                cells = [new_board[i] for i in line]
                if cells.count(self.opponent_symbol) == 3:
                    return move
        return None
    
    def _find_best_move_minimax(self, board, depth=2):
        """Use minimax with limited depth to find best move"""
        best_score = float('-inf')
        best_move = None
        available_moves = self._get_available_moves(board)
        
        # If few moves left, increase depth
        if len(available_moves) <= 6:
            depth = min(4, len(available_moves))
        
        for move in available_moves:
            new_board = board.copy()
            new_board[move] = self.symbol
            score = self._minimax(new_board, depth - 1, float('-inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move is not None else random.choice(available_moves)
    
    def _minimax(self, board, depth, alpha, beta, is_maximizing):
        """Minimax algorithm with alpha-beta pruning"""
        # Check terminal states
        if depth == 0:
            return self._evaluate_board(board, self.symbol)
        
        # Check for win/loss
        for line in self.winning_lines:
            cells = [board[i] for i in line]
            if cells.count(self.symbol) == 3:
                return 1000 + depth  # Prefer faster wins
            if cells.count(self.opponent_symbol) == 3:
                return -1000 - depth  # Prefer slower losses
        
        available_moves = self._get_available_moves(board)
        if not available_moves:
            return 0  # Draw
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in available_moves:
                new_board = board.copy()
                new_board[move] = self.symbol
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available_moves:
                new_board = board.copy()
                new_board[move] = self.opponent_symbol
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def make_move(self, board: list[str]) -> int:
        """Make a move on the board"""
        available_moves = self._get_available_moves(board)
        
        if not available_moves:
            return None
        
        # 1. Check for immediate win
        win_move = self._check_immediate_win(board, self.symbol)
        if win_move is not None:
            return win_move
        
        # 2. Block opponent's immediate win
        block_move = self._check_opponent_threat(board)
        if block_move is not None:
            return block_move
        
        # 3. Use minimax for deeper strategy
        if len(available_moves) > 15:  # Early game - use heuristic
            # Try to control center and create opportunities
            best_score = float('-inf')
            best_move = None
            for move in available_moves:
                score = self._evaluate_board(board, self.symbol)
                # Prefer moves that create two in a row
                test_board = board.copy()
                test_board[move] = self.symbol
                for line in self.winning_lines:
                    if move in line:
                        cells = [test_board[i] for i in line]
                        if cells.count(self.symbol) == 2:
                            score += 5
                if score > best_score:
                    best_score = score
                    best_move = move
            return best_move if best_move is not None else random.choice(available_moves)
        else:  # Late game - use minimax
            return self._find_best_move_minimax(board, depth=2)
