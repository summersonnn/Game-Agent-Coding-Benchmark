"""
Agent Code: A5-Connect4RandomStart
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-12 14:50:42
"""

import math

import random
import math

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        Initialize the agent.
        name: str - The name of the agent.
        symbol: str - The character representing the agent's disc ('R' or 'Y').
        """
        self.name = name
        self.symbol = symbol
        self.MAX_DEPTH = 4  # Depth for minimax search; adjust for speed vs. strength

    def make_move(self, board):
        """
        Decide the next move based on the current board state using minimax with alpha-beta pruning.
        
        Args:
            board: A list of lists representing the 6x7 grid.
                   board[row][col] contains 'R', 'Y', or ' ' (empty).
                   Row 0 is the top, Row 5 is the bottom.
                   
        Returns:
            int: The column index (0-6) where the agent wants to drop a disc.
        """
        opp_symbol = 'Y' if self.symbol == 'R' else 'R'
        valid_moves = self.get_valid_moves(board)
        
        if not valid_moves:
            return 0  # Fallback, though this should never happen in a valid game
        
        best_col = random.choice(valid_moves)  # Default to random if something goes wrong
        best_score = -math.inf
        
        for col in valid_moves:
            new_board = self.drop_disc(board, col, self.symbol)
            score = self.minimax(new_board, self.MAX_DEPTH, False, self.symbol, opp_symbol, -math.inf, math.inf)
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col
    
    def get_valid_moves(self, board):
        """Return a list of valid columns (not full)."""
        return [col for col in range(7) if board[5][col] == ' ']  # Bottom row empty means column isn't full
    
    def drop_disc(self, board, col, symbol):
        """Simulate dropping a disc into a column. Returns a new board state."""
        new_board = [row[:] for row in board]
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = symbol
                return new_board
        return None  # Column full (shouldn't happen with valid_moves check)
    
    def minimax(self, board, depth, is_maximizing, symbol, opp_symbol, alpha, beta):
        """Minimax with alpha-beta pruning."""
        winner = self.check_winner(board)
        if winner == symbol:
            return 1000 + depth  # Favor faster wins
        if winner == opp_symbol:
            return -1000 - depth  # Penalize faster losses
        if depth == 0 or not self.get_valid_moves(board):
            return self.evaluate_board(board, symbol, opp_symbol)
        
        valid_moves = self.get_valid_moves(board)
        if is_maximizing:
            max_eval = -math.inf
            for col in valid_moves:
                new_board = self.drop_disc(board, col, symbol)
                eval_score = self.minimax(new_board, depth - 1, False, symbol, opp_symbol, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Prune
            return max_eval
        else:
            min_eval = math.inf
            for col in valid_moves:
                new_board = self.drop_disc(board, col, opp_symbol)
                eval_score = self.minimax(new_board, depth - 1, True, symbol, opp_symbol, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Prune
            return min_eval
    
    def evaluate_board(self, board, symbol, opp_symbol):
        """Heuristic evaluation: Score based on 4-cell windows in all directions."""
        score = 0
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c + i] for i in range(4)]
                score += self.score_window(window, symbol, opp_symbol)
        # Vertical
        for c in range(7):
            for r in range(3):
                window = [board[r + j][c] for j in range(4)]
                score += self.score_window(window, symbol, opp_symbol)
        # Diagonal (\)
        for r in range(3):
            for c in range(4):
                window = [board[r + j][c + j] for j in range(4)]
                score += self.score_window(window, symbol, opp_symbol)
        # Diagonal (/)
        for r in range(3):
            for c in range(4):
                window = [board[r + j][c + 3 - j] for j in range(4)]
                score += self.score_window(window, symbol, opp_symbol)
        return score
    
    def score_window(self, window, symbol, opp_symbol):
        """Score a 4-cell window."""
        my_count = window.count(symbol)
        opp_count = window.count(opp_symbol)
        empty_count = window.count(' ')
        
        if my_count == 4:
            return 100  # Win
        elif my_count == 3 and empty_count == 1:
            return 10  # Strong threat
        elif my_count == 2 and empty_count == 2:
            return 2  # Potential
        elif opp_count == 3 and empty_count == 1:
            return -80  # Block opponent
        return 0
    
    def check_winner(self, board):
        """Check for a winner in the board."""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r][c + i] == board[r][c] for i in range(4)):
                    return board[r][c]
        # Vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and all(board[r + j][c] == board[r][c] for j in range(4)):
                    return board[r][c]
        # Diagonal (\)
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r + j][c + j] == board[r][c] for j in range(4)):
                    return board[r][c]
        # Diagonal (/)
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and all(board[r + j][c + 3 - j] == board[r][c] for j in range(4)):
                    return board[r][c]
        return None
