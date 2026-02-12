"""
Agent Code: A5-Connect4RandomStart
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-12 14:50:42
"""

import time

import random
import time

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.max_depth = 5  # Adjust based on performance needs
        self.time_limit = 0.9  # Use 0.9s to stay within 1s limit
        self.start_time = None
        
        # Precompute all winning window positions for efficiency
        self.win_patterns = self._precompute_win_patterns()
        
        # Column weights (center columns are more valuable)
        self.column_weights = [1, 2, 3, 4, 3, 2, 1]
    
    def _precompute_win_patterns(self):
        """Precompute all possible 4-in-a-row patterns."""
        patterns = []
        
        # Horizontal
        for r in range(6):
            for c in range(4):
                patterns.append([(r, c+i) for i in range(4)])
        
        # Vertical
        for r in range(3):
            for c in range(7):
                patterns.append([(r+i, c) for i in range(4)])
        
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                patterns.append([(r-i, c+i) for i in range(4)])
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                patterns.append([(r+i, c+i) for i in range(4)])
        
        return patterns
    
    def make_move(self, board):
        """Main entry point for the agent."""
        self.start_time = time.time()
        valid_moves = self._get_valid_moves(board)
        
        if not valid_moves:
            return random.randint(0, 6)  # Shouldn't happen but just in case
        
        # Quick win/loss detection
        for move in valid_moves:
            if self._is_winning_move(board, move, self.symbol):
                return move
        
        for move in valid_moves:
            if self._is_winning_move(board, move, self.opponent):
                return move
        
        # Use minimax with iterative deepening if time permits
        best_move = valid_moves[0]
        best_score = -float('inf')
        
        for depth in range(1, self.max_depth + 1):
            current_best = None
            current_best_score = -float('inf')
            
            for move in valid_moves:
                if time.time() - self.start_time > self.time_limit:
                    break
                    
                new_board = self._simulate_move(board, move, self.symbol)
                score = self._minimax(new_board, depth-1, -float('inf'), 
                                     float('inf'), False, self.opponent)
                
                if score > current_best_score:
                    current_best_score = score
                    current_best = move
            
            if current_best is not None:
                best_move = current_best
                best_score = current_best_score
            
            if time.time() - self.start_time > self.time_limit:
                break
        
        return best_move
    
    def _minimax(self, board, depth, alpha, beta, maximizing, current_player):
        """Minimax with alpha-beta pruning."""
        # Check time limit
        if time.time() - self.start_time > self.time_limit:
            return 0
        
        # Terminal checks
        if self._check_winner(board, current_player):
            return 1000 if maximizing else -1000
        
        if self._is_board_full(board):
            return 0
        
        if depth == 0:
            return self._evaluate_board(board, self.symbol)
        
        valid_moves = self._get_valid_moves(board)
        if not valid_moves:
            return 0
        
        if maximizing:
            max_eval = -float('inf')
            for move in valid_moves:
                new_board = self._simulate_move(board, move, current_player)
                eval_score = self._minimax(new_board, depth-1, alpha, beta, 
                                          False, self.opponent)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid_moves:
                new_board = self._simulate_move(board, move, current_player)
                eval_score = self._minimax(new_board, depth-1, alpha, beta, 
                                          True, self.symbol)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def _evaluate_board(self, board, player):
        """Evaluate board state for given player."""
        opponent = self.opponent if player == self.symbol else self.symbol
        score = 0
        
        # Evaluate all winning patterns
        for pattern in self.win_patterns:
            player_count = 0
            opponent_count = 0
            empty_count = 0
            
            for r, c in pattern:
                cell = board[r][c]
                if cell == player:
                    player_count += 1
                elif cell == opponent:
                    opponent_count += 1
                else:
                    empty_count += 1
            
            # Only evaluate non-blocked patterns
            if player_count > 0 and opponent_count > 0:
                continue
            
            # Score based on potential
            if player_count == 3 and empty_count == 1:
                score += 100  # Immediate threat
            elif player_count == 2 and empty_count == 2:
                score += 10   # Potential threat
            elif player_count == 1 and empty_count == 3:
                score += 1    # Development
            
            if opponent_count == 3 and empty_count == 1:
                score -= 120  # Opponent threat (higher priority to block)
            elif opponent_count == 2 and empty_count == 2:
                score -= 15   # Opponent potential
            elif opponent_count == 1 and empty_count == 3:
                score -= 2    # Opponent development
        
        # Center column preference
        center_col = 3
        for r in range(6):
            if board[r][center_col] == player:
                score += 2
            elif board[r][center_col] == opponent:
                score -= 2
        
        # Bonus for occupying bottom rows (more stable)
        for c in range(7):
            for r in range(5, 2, -1):  # Bottom 3 rows
                if board[r][c] == player:
                    score += 1
                elif board[r][c] == opponent:
                    score -= 1
        
        return score
    
    def _get_valid_moves(self, board):
        """Get list of valid columns (not full)."""
        return [c for c in range(7) if board[0][c] == ' ']
    
    def _simulate_move(self, board, col, player):
        """Simulate a move and return new board state."""
        new_board = [row[:] for row in board]
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = player
                break
        return new_board
    
    def _check_winner(self, board, player):
        """Check if player has won on the board."""
        for pattern in self.win_patterns:
            if all(board[r][c] == player for r, c in pattern):
                return True
        return False
    
    def _is_board_full(self, board):
        """Check if board is full."""
        return all(board[0][c] != ' ' for c in range(7))
    
    def _is_winning_move(self, board, col, player):
        """Check if move in column results in immediate win."""
        if board[0][col] != ' ':
            return False
        
        # Find the row where disc would land
        for row in range(5, -1, -1):
            if board[row][col] == ' ':
                # Simulate move
                test_board = [r[:] for r in board]
                test_board[row][col] = player
                return self._check_winner(test_board, player)
        return False
