"""
Agent Code: A5-Connect4RandomStart
Model: z-ai/glm-5@preset/fp8-speedy
Run: 2
Generated: 2026-02-12 14:50:42
"""

import math
import time

import math
import time

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
        self.rows = 6
        self.cols = 7
        # Order columns center-out to improve alpha-beta pruning efficiency
        self.column_order = [3, 2, 4, 1, 5, 0, 6]

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        Uses Minimax with Alpha-Beta pruning and Iterative Deepening.
        """
        start_time = time.time()
        
        # 1. Check for immediate winning move
        for col in self.column_order:
            if self._is_valid_location(board, col):
                row = self._get_next_open_row(board, col)
                board[row][col] = self.symbol
                if self._is_winning_move(board, row, col, self.symbol):
                    return col
                board[row][col] = ' ' # Undo

        # 2. Check for immediate blocking move (opponent wins next)
        for col in self.column_order:
            if self._is_valid_location(board, col):
                row = self._get_next_open_row(board, col)
                board[row][col] = self.opponent_symbol
                if self._is_winning_move(board, row, col, self.opponent_symbol):
                    return col
                board[row][col] = ' ' # Undo

        # 3. Iterative Deepening Minimax
        best_col = self._get_valid_moves(board)[0] # Fallback
        best_score = -math.inf
        
        # Iterate depth from 1 to a safe maximum (e.g., 12)
        # The time limit is 1s, so we break early if time runs out.
        for depth in range(1, 12):
            current_time = time.time()
            if current_time - start_time > 0.75: # Safety margin
                break
            
            score, col = self._minimax(board, depth, -math.inf, math.inf, True, start_time)
            
            if col is not None:
                best_col = col
                best_score = score
            
            # If we found a forced win, no need to search deeper
            if best_score > 9000:
                break
                
        return best_col

    def _minimax(self, board, depth, alpha, beta, maximizingPlayer, start_time):
        valid_moves = self._get_valid_moves(board)
        
        # Time check or Terminal state checks
        if time.time() - start_time > 0.80:
            return (self._score_position(board), None)
            
        if not valid_moves:
            return (0, None) # Draw
            
        if depth == 0:
            return (self._score_position(board), None)

        # Check for terminal node (win/loss) immediately
        # We check if the *last* move (simulated in previous recursion) won.
        # Since we don't track last move here, we scan. 
        # Optimization: This is covered by the immediate checks in make_move and recursion logic.
        # But let's check if current board is won.
        if self._is_board_won(board, self.symbol):
            return (100000 + depth, None)
        if self._is_board_won(board, self.opponent_symbol):
            return (-100000 - depth, None)

        best_col = valid_moves[0]

        if maximizingPlayer:
            value = -math.inf
            for col in valid_moves:
                row = self._get_next_open_row(board, col)
                board[row][col] = self.symbol
                # Check if this specific move wins
                if self._is_winning_move(board, row, col, self.symbol):
                    new_score = 100000 + depth
                else:
                    new_score, _ = self._minimax(board, depth - 1, alpha, beta, False, start_time)
                
                board[row][col] = ' ' # Undo
                
                if new_score > value:
                    value = new_score
                    best_col = col
                    
                alpha = max(alpha, value)
                if alpha >= beta:
                    break # Beta cutoff
            return value, best_col

        else: # Minimizing Player
            value = math.inf
            for col in valid_moves:
                row = self._get_next_open_row(board, col)
                board[row][col] = self.opponent_symbol
                # Check if this specific move loses for us
                if self._is_winning_move(board, row, col, self.opponent_symbol):
                    new_score = -100000 - depth
                else:
                    new_score, _ = self._minimax(board, depth - 1, alpha, beta, True, start_time)
                
                board[row][col] = ' ' # Undo
                
                if new_score < value:
                    value = new_score
                    best_col = col
                    
                beta = min(beta, value)
                if alpha >= beta:
                    break # Alpha cutoff
            return value, best_col

    # --- Helper Methods ---

    def _is_valid_location(self, board, col):
        return board[0][col] == ' '

    def _get_next_open_row(self, board, col):
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return -1

    def _get_valid_moves(self, board):
        valid = []
        for col in self.column_order:
            if self._is_valid_location(board, col):
                valid.append(col)
        return valid

    def _is_winning_move(self, board, row, col, symbol):
        """Checks if the piece at (row, col) creates a win."""
        # Check Horizontal
        count = 0
        for c in range(max(0, col-3), min(self.cols, col+4)):
            if board[row][c] == symbol:
                count += 1
                if count == 4: return True
            else:
                count = 0
        
        # Check Vertical
        count = 0
        for r in range(max(0, row-3), min(self.rows, row+4)):
            if board[r][col] == symbol:
                count += 1
                if count == 4: return True
            else:
                count = 0

        # Check Diagonal /
        count = 0
        # Shift logic: we traverse the diagonal passing through (row, col)
        # Bounds: row-3 <= r <= row+3, col-3 <= c <= col+3, r + c = row + col
        # r = row + i, c = col - i
        for i in range(-3, 4):
            r, c = row + i, col - i
            if 0 <= r < self.rows and 0 <= c < self.cols:
                if board[r][c] == symbol:
                    count += 1
                    if count == 4: return True
                else:
                    count = 0
            else:
                count = 0 # Reset if hitting wall? No, sequence broken.
                # Actually, just resetting count is fine.

        # Check Diagonal \
        count = 0
        for i in range(-3, 4):
            r, c = row + i, col + i
            if 0 <= r < self.rows and 0 <= c < self.cols:
                if board[r][c] == symbol:
                    count += 1
                    if count == 4: return True
                else:
                    count = 0
                    
        return False

    def _is_board_won(self, board, symbol):
        """Scans whole board for a win (slower, used for leaf checks)."""
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == symbol and board[r][c+1] == symbol and board[r][c+2] == symbol and board[r][c+3] == symbol:
                    return True
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] == symbol and board[r+1][c] == symbol and board[r+2][c] == symbol and board[r+3][c] == symbol:
                    return True
        # Diagonals
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] == symbol and board[r+1][c+1] == symbol and board[r+2][c+2] == symbol and board[r+3][c+3] == symbol:
                    return True
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == symbol and board[r-1][c+1] == symbol and board[r-2][c+2] == symbol and board[r-3][c+3] == symbol:
                    return True
        return False

    def _score_position(self, board):
        """Heuristic evaluation of the board."""
        score = 0

        # Score Center column (preference for center)
        center_array = [row[3] for row in board]
        center_count = center_array.count(self.symbol)
        score += center_count * 6

        # Score Horizontal
        for r in range(self.rows):
            row_array = board[r]
            for c in range(self.cols - 3):
                window = row_array[c:c+4]
                score += self._evaluate_window(window)

        # Score Vertical
        for c in range(self.cols):
            col_array = [board[r][c] for r in range(self.rows)]
            for r in range(self.rows - 3):
                window = col_array[r:r+4]
                score += self._evaluate_window(window)

        # Score Positive Diagonal
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window)

        # Score Negative Diagonal
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window)

        return score

    def _evaluate_window(self, window):
        score = 0
        my_piece = self.symbol
        opp_piece = self.opponent_symbol
        empty = ' '

        if window.count(my_piece) == 4:
            score += 100
        elif window.count(my_piece) == 3 and window.count(empty) == 1:
            score += 10
        elif window.count(my_piece) == 2 and window.count(empty) == 2:
            score += 4

        if window.count(opp_piece) == 3 and window.count(empty) == 1:
            score -= 80 # Block opponent threat

        return score
