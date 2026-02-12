"""
Agent Code: A5-Connect4RandomStart
Model: z-ai/glm-4.7@preset/fp8-speedy
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
        self.rows = 6
        self.cols = 7
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        Uses a heuristic-based minimax algorithm with alpha-beta pruning.
        """
        # 1. Identify all valid moves (columns that are not full)
        # Board is 6x7, Row 0 is top.
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        
        # If no valid moves, return 0 (should not happen in normal play before draw)
        if not valid_moves:
            return 0

        # 2. Check for immediate winning moves
        for col in valid_moves:
            if self.is_winning_move(board, col, self.symbol):
                return col
        
        # 3. Check for immediate blocking moves (opponent winning next)
        for col in valid_moves:
            if self.is_winning_move(board, col, self.opponent_symbol):
                return col

        # 4. Run Minimax with Alpha-Beta Pruning to find the best strategic move
        # Depth 4 provides a good balance of lookahead and performance within the 1s limit
        best_score = -math.inf
        best_col = random.choice(valid_moves)
        
        # Move ordering: prioritize center columns (3, 2, 4, 1, 5, 0, 6)
        # This significantly improves alpha-beta pruning efficiency
        center_cols = [3, 2, 4, 1, 5, 0, 6]
        valid_moves_sorted = [c for c in center_cols if c in valid_moves]

        for col in valid_moves_sorted:
            # Create a deep copy of the board for simulation
            board_copy = [row[:] for row in board]
            self.simulate_drop(board_copy, col, self.symbol)
            
            # Call minimax for the next turn (minimizing player's turn)
            score = self.minimax(board_copy, 4, -math.inf, math.inf, False)
            
            if score > best_score:
                best_score = score
                best_col = col
                
        return best_col

    def is_winning_move(self, board, col, piece):
        """
        Simulates dropping a piece and checks if it results in a win.
        Modifies the board temporarily but reverts the change.
        """
        # Find the lowest empty row in the specified column
        row = -1
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                row = r
                break
        
        # If column is full (should be filtered by valid_moves), return False
        if row == -1:
            return False
            
        # Temporarily place the piece
        board[row][col] = piece
        win = self.check_winner(board, piece)
        # Revert the change
        board[row][col] = ' '
        return win

    def simulate_drop(self, board, col, piece):
        """
        Drops a piece into the board (in-place modification for simulation).
        Assumes the column is not full.
        """
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = piece
                return

    def check_winner(self, board, piece):
        """
        Checks the board for 4 connected pieces of the given type.
        """
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == piece and board[r][c+1] == piece and \
                   board[r][c+2] == piece and board[r][c+3] == piece:
                    return True

        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] == piece and board[r+1][c] == piece and \
                   board[r+2][c] == piece and board[r+3][c] == piece:
                    return True

        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == piece and board[r-1][c+1] == piece and \
                   board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True

        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and \
                   board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        return False

    def minimax(self, board, depth, alpha, beta, maximizingPlayer):
        """
        Minimax algorithm with alpha-beta pruning.
        maximizingPlayer: True if it's the agent's turn, False if opponent's.
        """
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        
        # Terminal conditions
        if self.check_winner(board, self.symbol):
            # Win: Higher score for winning faster (lower depth)
            return 1000000 - depth
        if self.check_winner(board, self.opponent_symbol):
            # Loss: Lower score for losing slower (higher depth)
            return -1000000 + depth
        if len(valid_moves) == 0:
            return 0 # Draw
        if depth == 0:
            return self.score_position(board, self.symbol)

        # Move ordering for pruning efficiency
        center_cols = [3, 2, 4, 1, 5, 0, 6]
        valid_moves_sorted = [c for c in center_cols if c in valid_moves]

        if maximizingPlayer:
            max_eval = -math.inf
            for col in valid_moves_sorted:
                board_copy = [row[:] for row in board]
                self.simulate_drop(board_copy, col, self.symbol)
                eval = self.minimax(board_copy, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for col in valid_moves_sorted:
                board_copy = [row[:] for row in board]
                self.simulate_drop(board_copy, col, self.opponent_symbol)
                eval = self.minimax(board_copy, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def score_position(self, board, piece):
        """
        Heuristic evaluation of the board state.
        """
        score = 0
        opp_piece = self.opponent_symbol
        
        # Center column preference
        center_array = [board[r][3] for r in range(self.rows)]
        center_count = center_array.count(piece)
        score += center_count * 3
        
        # Horizontal
        for r in range(self.rows):
            row_array = board[r]
            for c in range(self.cols - 3):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, piece, opp_piece)
        
        # Vertical
        for c in range(self.cols):
            col_array = [board[r][c] for r in range(self.rows)]
            for r in range(self.rows - 3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, piece, opp_piece)
        
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece, opp_piece)
        
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece, opp_piece)
                
        return score

    def evaluate_window(self, window, piece, opp_piece):
        """
        Evaluates a 4-cell window.
        """
        score = 0
        piece_count = window.count(piece)
        empty_count = window.count(' ')
        opp_count = window.count(opp_piece)
        
        if piece_count == 4:
            score += 100
        elif piece_count == 3 and empty_count == 1:
            score += 5
        elif piece_count == 2 and empty_count == 2:
            score += 2
            
        if opp_count == 3 and empty_count == 1:
            score -= 4
            
        return score
