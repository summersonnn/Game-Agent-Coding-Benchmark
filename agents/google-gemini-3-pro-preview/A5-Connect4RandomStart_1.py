"""
Agent Code: A5-Connect4RandomStart
Model: google-gemini-3-pro-preview
Run: 1
Generated: 2026-02-12 14:51:10
"""

import time
import random

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        Initialize the agent.
        """
        self.name = name
        self.symbol = symbol
        self.opp_symbol = 'R' if symbol == 'Y' else 'Y'
        
        self.ROWS = 6
        self.COLS = 7
        self.EMPTY = ' '
        
        # Time limit settings
        self.TIME_LIMIT = 0.90  # Safety buffer (limit is 1.0s)
        self.start_time = 0

        # Pre-calculate all possible winning windows (indices) to speed up evaluation
        # A window is a list of 4 (row, col) tuples
        self.windows = self._generate_windows()

    def make_move(self, board):
        """
        Decide the next move using Iterative Deepening Minimax.
        """
        self.start_time = time.time()
        
        valid_moves = self._get_valid_locations(board)
        
        # Fallback: simple center preference if we have 0 time or crash
        best_move = self._pick_best_move_simple(board, valid_moves)
        
        # Iterative Deepening
        # We start at depth 1 and go deeper until we run out of time
        try:
            depth = 1
            while True:
                # If we are close to timeout, stop expanding
                if time.time() - self.start_time > self.TIME_LIMIT:
                    break
                
                # Run Minimax for current depth
                move, score = self._minimax(board, depth, -float('inf'), float('inf'), True)
                
                # If we found a forced win, take it immediately
                if score >= 100000:
                    best_move = move
                    break
                
                # If we found a forced loss (score extremely low), we still update 
                # best_move to try and delay the loss, but we might keep searching.
                if move is not None:
                    best_move = move
                
                depth += 1
                
        except TimeoutError:
            pass # Return the best move found so far

        return best_move

    def _minimax(self, board, depth, alpha, beta, maximizingPlayer):
        """
        Minimax algorithm with Alpha-Beta pruning.
        Returns: (best_column, score)
        """
        # Check time constraint periodically
        if (time.time() - self.start_time) > self.TIME_LIMIT:
            raise TimeoutError()

        valid_locations = self._get_valid_locations(board)
        is_terminal = self._is_terminal_node(board, valid_locations)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if self._check_win(board, self.symbol):
                    return (None, 1000000)
                elif self._check_win(board, self.opp_symbol):
                    return (None, -1000000)
                else: # Draw
                    return (None, 0)
            else: # Depth is zero
                return (None, self._score_position(board, self.symbol))

        # Move Ordering: Evaluate center columns first to improve pruning
        center = self.COLS // 2
        valid_locations.sort(key=lambda x: abs(x - center))

        if maximizingPlayer:
            value = -float('inf')
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = self._get_next_open_row(board, col)
                # Create copy of board conceptually (manually reverting is faster than deepcopy)
                board[row][col] = self.symbol
                
                new_score = self._minimax(board, depth - 1, alpha, beta, False)[1]
                
                # Revert move (Backtrack)
                board[row][col] = self.EMPTY

                if new_score > value:
                    value = new_score
                    column = col
                
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value

        else: # Minimizing Player
            value = float('inf')
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = self._get_next_open_row(board, col)
                
                board[row][col] = self.opp_symbol
                
                new_score = self._minimax(board, depth - 1, alpha, beta, True)[1]
                
                board[row][col] = self.EMPTY

                if new_score < value:
                    value = new_score
                    column = col
                
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    def _score_position(self, board, piece):
        """
        Heuristic evaluation of the board.
        """
        score = 0
        
        # Prefer Center Column (Strategy: Control the center)
        center_array = [r[self.COLS // 2] for r in board]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Evaluate all pre-calculated windows
        # Note: This loop is the bottleneck of Python agents. 
        # Optimized to flat lookup.
        for window_indices in self.windows:
            # Extract content of the window
            w_content = [board[r][c] for r, c in window_indices]
            
            score += self._evaluate_window(w_content, piece)

        return score

    def _evaluate_window(self, window, piece):
        """
        Score a specific window of 4 cells.
        """
        score = 0
        opp_piece = self.opp_symbol

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(self.EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(self.EMPTY) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(self.EMPTY) == 1:
            score -= 80 # Heavy penalty for allowing opponent 3-in-a-row

        return score

    def _generate_windows(self):
        """
        Pre-calculates all indices for horizontal, vertical, and diagonal lines.
        Returns a list of lists, where each inner list contains 4 (row, col) tuples.
        """
        windows = []
        
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                windows.append([(r, c+i) for i in range(4)])

        # Vertical
        for c in range(self.COLS):
            for r in range(self.ROWS - 3):
                windows.append([(r+i, c) for i in range(4)])

        # Positive Diagonal
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                windows.append([(r+i, c+i) for i in range(4)])

        # Negative Diagonal
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                windows.append([(r+3-i, c+i) for i in range(4)])
                
        return windows

    def _get_valid_locations(self, board):
        valid_locations = []
        for col in range(self.COLS):
            if board[0][col] == self.EMPTY:
                valid_locations.append(col)
        return valid_locations

    def _pick_best_move_simple(self, board, valid_moves):
        # Quick fallback: pick center if valid, else random
        center = self.COLS // 2
        if center in valid_moves:
            return center
        return random.choice(valid_moves)

    def _get_next_open_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return None

    def _check_win(self, board, piece):
        # Simplified check reusing the pre-calculated windows
        # Note: The game engine does this differently, but this is consistent for our internal logic
        for window_indices in self.windows:
            if all(board[r][c] == piece for r, c in window_indices):
                return True
        return False

    def _is_terminal_node(self, board, valid_locations):
        return len(valid_locations) == 0 or \
               self._check_win(board, self.symbol) or \
               self._check_win(board, self.opp_symbol)