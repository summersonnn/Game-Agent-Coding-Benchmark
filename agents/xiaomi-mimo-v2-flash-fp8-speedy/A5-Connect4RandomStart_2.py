"""
Agent Code: A5-Connect4RandomStart
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 2
Generated: 2026-02-14 19:46:39
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
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.EMPTY = ' '
        self.ROWS = 6
        self.COLS = 7
        self.DEPTH = 4  # Search depth for minimax
        
        # Precompute all possible windows of 4 cells for evaluation
        self.windows = self._precompute_windows()
        
        # Evaluation weights
        self.WIN_SCORE = 1000000
        self.THREE_SCORE = 100
        self.TWO_SCORE = 10
        self.ONE_SCORE = 1
        self.CENTER_BONUS = 5

    def _precompute_windows(self):
        """Precompute all possible 4-cell windows (horizontal, vertical, diagonal)"""
        windows = []
        
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                windows.append([(r, c), (r, c+1), (r, c+2), (r, c+3)])
        
        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                windows.append([(r, c), (r+1, c), (r+2, c), (r+3, c)])
        
        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                windows.append([(r, c), (r-1, c+1), (r-2, c+2), (r-3, c+3)])
        
        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                windows.append([(r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)])
        
        return windows

    def _check_win(self, board, player):
        """Check if the given player has 4 in a row"""
        for window in self.windows:
            if all(board[r][c] == player for r, c in window):
                return True
        return False

    def _is_draw(self, board):
        """Check if the board is full (draw)"""
        return all(cell != self.EMPTY for cell in board[0])

    def _is_terminal(self, board):
        """Check if the game is over (win or draw)"""
        return (self._check_win(board, self.symbol) or 
                self._check_win(board, self.opponent_symbol) or 
                self._is_draw(board))

    def _evaluate(self, board):
        """
        Evaluate the board state from the perspective of the agent (maximizing player)
        Returns a score: positive is good for agent, negative is good for opponent
        """
        score = 0
        
        # Center column bonus
        center_column = 3
        for r in range(self.ROWS):
            if board[r][center_column] == self.symbol:
                score += self.CENTER_BONUS
            elif board[r][center_column] == self.opponent_symbol:
                score -= self.CENTER_BONUS
        
        # Evaluate all windows
        for window in self.windows:
            our_count = 0
            opp_count = 0
            empty_count = 0
            
            for r, c in window:
                if board[r][c] == self.symbol:
                    our_count += 1
                elif board[r][c] == self.opponent_symbol:
                    opp_count += 1
                else:
                    empty_count += 1
            
            # Skip windows with both players' pieces (blocked)
            if our_count > 0 and opp_count > 0:
                continue
            
            # Evaluate our opportunities
            if our_count == 4:
                score += self.WIN_SCORE
            elif our_count == 3 and empty_count == 1:
                score += self.THREE_SCORE
            elif our_count == 2 and empty_count == 2:
                score += self.TWO_SCORE
            elif our_count == 1 and empty_count == 3:
                score += self.ONE_SCORE
            
            # Evaluate opponent's threats
            if opp_count == 4:
                score -= self.WIN_SCORE
            elif opp_count == 3 and empty_count == 1:
                score -= self.THREE_SCORE
            elif opp_count == 2 and empty_count == 2:
                score -= self.TWO_SCORE
            elif opp_count == 1 and empty_count == 3:
                score -= self.ONE_SCORE
        
        # Add small random noise to break ties
        score += random.uniform(-0.1, 0.1)
        
        return score

    def _simulate_move(self, board, col, player):
        """Simulate a move and return a new board state"""
        new_board = [row[:] for row in board]
        # Drop disc to lowest empty row in column
        for r in range(self.ROWS - 1, -1, -1):
            if new_board[r][col] == self.EMPTY:
                new_board[r][col] = player
                return new_board
        return None  # Column is full (shouldn't happen with valid moves)

    def _get_valid_columns(self, board):
        """Get list of valid columns (not full)"""
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        """
        Minimax algorithm with alpha-beta pruning
        Returns the evaluation score for the current board state
        """
        # Terminal state or depth limit
        if depth == 0 or self._is_terminal(board):
            return self._evaluate(board)
        
        valid_cols = self._get_valid_columns(board)
        
        if maximizing_player:
            max_eval = -math.inf
            for col in valid_cols:
                new_board = self._simulate_move(board, col, self.symbol)
                if new_board is None:
                    continue
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for col in valid_cols:
                new_board = self._simulate_move(board, col, self.opponent_symbol)
                if new_board is None:
                    continue
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        
        Args:
            board: A list of lists representing the 6x7 grid.
                   board[row][col] contains 'R', 'Y', or ' ' (empty).
                   Row 0 is the top, Row 5 is the bottom.
                   
        Returns:
            int: The column index (0-6) where the agent wants to drop a disc.
        """
        valid_cols = self._get_valid_columns(board)
        
        # If only one valid move, take it
        if len(valid_cols) == 1:
            return valid_cols[0]
        
        # Use minimax to find the best move
        best_score = -math.inf
        best_col = valid_cols[0]
        
        # Sort columns by center proximity for tie-breaking
        center_order = sorted(valid_cols, key=lambda c: abs(c - 3))
        
        for col in center_order:
            new_board = self._simulate_move(board, col, self.symbol)
            if new_board is None:
                continue
            
            # Check if this move wins immediately
            if self._check_win(new_board, self.symbol):
                return col
            
            # Check if opponent has immediate winning move and we need to block
            opponent_wins_next = False
            for opp_col in valid_cols:
                if opp_col == col:
                    continue
                opp_board = self._simulate_move(board, opp_col, self.opponent_symbol)
                if opp_board and self._check_win(opp_board, self.opponent_symbol):
                    opponent_wins_next = True
                    break
            
            if opponent_wins_next:
                # We must block opponent's winning move
                return col
            
            # Evaluate this move with minimax
            score = self._minimax(new_board, self.DEPTH - 1, -math.inf, math.inf, False)
            
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col
