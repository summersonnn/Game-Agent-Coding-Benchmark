"""
Agent Code: A5-Connect4RandomStart
Model: google-gemini-3-pro-preview
Run: 2
Generated: 2026-02-12 14:51:12
"""


import random
import time
import math

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        Initialize the agent.
        """
        self.name = name
        self.symbol = symbol
        self.opp_symbol = 'Y' if symbol == 'R' else 'R'
        
        # Configuration
        self.ROWS = 6
        self.COLS = 7
        self.EMPTY = ' '
        
        # Scoring Weights
        self.WINDOW_LENGTH = 4
        self.SCORE_CENTER = 3
        self.SCORE_WIN = 1000000000
        self.SCORE_3 = 5
        self.SCORE_2 = 2
        self.SCORE_OPP_3 = -4  # Penalty for letting opponent get 3 (Block imperative)

    def make_move(self, board):
        """
        Decide the next move using Iterative Deepening Minimax.
        """
        start_time = time.time()
        time_limit = 0.90  # Leave a 0.1s buffer to avoid timeouts
        
        valid_locations = self.get_valid_locations(board)
        
        # Fallback: Random move if no strategy is found in time
        best_col = random.choice(valid_locations) if valid_locations else 0
        
        # Iterative Deepening
        depth = 1
        while True:
            try:
                # Check time before starting a new depth
                if time.time() - start_time > time_limit:
                    break
                
                col, score = self.minimax(board, depth, -math.inf, math.inf, True, start_time, time_limit)
                
                # If we found a forced win, take it immediately
                if score == self.SCORE_WIN:
                    return col
                    
                best_col = col
                depth += 1
                
            except TimeoutError:
                # If minimax timed out mid-search, break and use result from previous depth
                break
                
        return best_col

    def minimax(self, board, depth, alpha, beta, maximizingPlayer, start_time, time_limit):
        """
        Minimax algorithm with Alpha-Beta pruning and timeout check.
        """
        # Safety check for timeout inside recursion
        if time.time() - start_time > time_limit:
            raise TimeoutError("Time Limit Exceeded")

        valid_locations = self.get_valid_locations(board)
        is_terminal = self.is_terminal_node(board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if self.winning_move(board, self.symbol):
                    return (None, self.SCORE_WIN)
                elif self.winning_move(board, self.opp_symbol):
                    return (None, -self.SCORE_WIN)
                else: # Game is over, no more valid moves (Draw)
                    return (None, 0)
            else: # Depth is zero
                return (None, self.score_position(board, self.symbol))
        
        # Move Ordering: Search center columns first to maximize pruning
        center = self.COLS // 2
        valid_locations.sort(key=lambda x: abs(x - center))

        if maximizingPlayer:
            value = -math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                
                # Simulate move
                board[row][col] = self.symbol
                new_score = self.minimax(board, depth-1, alpha, beta, False, start_time, time_limit)[1]
                # Backtrack (Undo move)
                board[row][col] = self.EMPTY

                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value

        else: # Minimizing Player
            value = math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                
                # Simulate move
                board[row][col] = self.opp_symbol
                new_score = self.minimax(board, depth-1, alpha, beta, True, start_time, time_limit)[1]
                # Backtrack
                board[row][col] = self.EMPTY

                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    def score_position(self, board, piece):
        """
        Heuristic evaluation of the board state.
        """
        score = 0
        opp_piece = self.opp_symbol

        # Center Column Preference
        center_array = [row[self.COLS // 2] for row in board]
        center_count = center_array.count(piece)
        score += center_count * self.SCORE_CENTER

        # Horizontal
        for r in range(self.ROWS):
            row_array = board[r]
            for c in range(self.COLS - 3):
                window = row_array[c:c+self.WINDOW_LENGTH]
                score += self.evaluate_window(window, piece, opp_piece)

        # Vertical
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r+self.WINDOW_LENGTH]
                score += self.evaluate_window(window, piece, opp_piece)

        # Positive Diagonal
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(self.WINDOW_LENGTH)]
                score += self.evaluate_window(window, piece, opp_piece)

        # Negative Diagonal
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+3-i][c+i] for i in range(self.WINDOW_LENGTH)]
                score += self.evaluate_window(window, piece, opp_piece)

        return score

    def evaluate_window(self, window, piece, opp_piece):
        """
        Score a specific window of 4 cells.
        """
        score = 0
        
        if window.count(piece) == 4:
            score += self.SCORE_WIN
        elif window.count(piece) == 3 and window.count(self.EMPTY) == 1:
            score += self.SCORE_3
        elif window.count(piece) == 2 and window.count(self.EMPTY) == 2:
            score += self.SCORE_2
        
        if window.count(opp_piece) == 3 and window.count(self.EMPTY) == 1:
            score += self.SCORE_OPP_3
            
        return score

    def get_valid_locations(self, board):
        return [c for c in range(self.COLS) if board[0][c] == self.EMPTY]

    def get_next_open_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == self.EMPTY:
                return r
        return None

    def is_terminal_node(self, board):
        return self.winning_move(board, self.symbol) or \
               self.winning_move(board, self.opp_symbol) or \
               len(self.get_valid_locations(board)) == 0

    def winning_move(self, board, piece):
        # Horizontal
        for c in range(self.COLS - 3):
            for r in range(self.ROWS):
                if board[r][c] == piece and board[r][c+1] == piece and \
                   board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        # Vertical
        for c in range(self.COLS):
            for r in range(self.ROWS - 3):
                if board[r][c] == piece and board[r+1][c] == piece and \
                   board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
        # Pos Diag
        for c in range(self.COLS - 3):
            for r in range(self.ROWS - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and \
                   board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        # Neg Diag
        for c in range(self.COLS - 3):
            for r in range(3, self.ROWS):
                if board[r][c] == piece and board[r-1][c+1] == piece and \
                   board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        return False