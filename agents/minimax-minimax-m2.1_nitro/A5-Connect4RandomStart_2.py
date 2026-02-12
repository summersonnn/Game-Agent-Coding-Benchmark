"""
Agent Code: A5-Connect4RandomStart
Model: minimax/minimax-m2.1:nitro
Run: 2
Generated: 2026-02-12 13:21:31
"""

from copy import deepcopy

import random
from copy import deepcopy

class Connect4Agent:
    """
    A competitive Connect 4 agent that uses:
    - Immediate win/block detection
    - Minimax search with alpha-beta pruning
    - Positional evaluation based on window patterns
    - Center-weighted strategy
    """
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.ROWS = 6
        self.COLS = 7
        self.EMPTY = ' '
    
    def make_move(self, board):
        """
        Determine the optimal move for the current board state.
        
        Args:
            board: 6x7 grid with 'R', 'Y', or ' ' (empty)
        
        Returns:
            int: Column index (0-6) to drop disc
        """
        valid_moves = self._get_valid_moves(board)
        
        if not valid_moves:
            return random.randint(0, self.COLS - 1)
        
        # 1. Check for immediate winning move
        for col in valid_moves:
            if self._is_winning_move(board, col, self.symbol):
                return col
        
        # 2. Check for opponent's immediate win (must block)
        for col in valid_moves:
            if self._is_winning_move(board, col, self.opponent_symbol):
                return col
        
        # 3. Use minimax with alpha-beta pruning for deeper strategy
        best_col = self._minimax(board, depth=4, alpha=float('-inf'), 
                                  beta=float('inf'), maximizing_player=True)[1]
        
        # Fallback to valid move if minimax returns invalid column
        if best_col not in valid_moves:
            best_col = self._center_heuristic(valid_moves)
        
        return best_col
    
    def _get_valid_moves(self, board):
        """Return list of columns that are not full."""
        valid = []
        for col in range(self.COLS):
            if board[0][col] == self.EMPTY:
                valid.append(col)
        return valid
    
    def _get_next_open_row(self, board, col):
        """Find the lowest empty row in the given column."""
        for row in range(self.ROWS - 1, -1, -1):
            if board[row][col] == self.EMPTY:
                return row
        return None
    
    def _is_winning_move(self, board, col, player_symbol):
        """
        Check if dropping in column 'col' would win for 'player_symbol'.
        """
        row = self._get_next_open_row(board, col)
        if row is None:
            return False
        
        temp_board = deepcopy(board)
        temp_board[row][col] = player_symbol
        
        return self._check_winner_board(temp_board) == player_symbol
    
    def _check_winner_board(self, board):
        """Check if there's a winner on the board (returns 'R', 'Y', or None)."""
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        
        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        
        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        
        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if board[r][c] != self.EMPTY and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        
        return None
    
    def _evaluate_window(self, window, piece):
        """
        Evaluate a window of 4 cells and return a score.
        
        Scoring:
        - 4 of player's pieces: 100 (win)
        - 3 of player's pieces + 1 empty: 5 (strong threat)
        - 2 of player's pieces + 2 empty: 2 (building)
        - 1 of player's pieces + 3 empty: 0.5 (potential)
        - Opponent 3 + 1 empty: -4 (danger - should block)
        - Opponent 4: -100 (loss)
        """
        score = 0
        opp_piece = self.opponent_symbol if piece == self.symbol else self.symbol
        piece_count = window.count(piece)
        opp_count = window.count(opp_piece)
        empty_count = window.count(self.EMPTY)
        
        if piece_count == 4:
            score += 100
        elif piece_count == 3 and empty_count == 1:
            score += 5
        elif piece_count == 2 and empty_count == 2:
            score += 2
        elif piece_count == 1 and empty_count == 3:
            score += 0.5
        
        if opp_count == 3 and empty_count == 1:
            score -= 4
        elif opp_count == 4:
            score -= 100
        
        return score
    
    def _score_position(self, board, piece):
        """Calculate overall positional score for the board."""
        score = 0
        
        # Center column preference
        center_array = [board[r][self.COLS // 2] for r in range(self.ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3
        
        # Horizontal evaluation
        for r in range(self.ROWS):
            row_array = board[r]
            for c in range(self.COLS - 3):
                window = row_array[c:c+4]
                score += self._evaluate_window(window, piece)
        
        # Vertical evaluation
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r+4]
                score += self._evaluate_window(window, piece)
        
        # Diagonal / evaluation
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window, piece)
        
        # Diagonal \ evaluation
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window, piece)
        
        return score
    
    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        """
        Minimax algorithm with alpha-beta pruning.
        
        Returns:
            (score, column) tuple
        """
        valid_moves = self._get_valid_moves(board)
        is_terminal = self._check_winner_board(board) is not None or len(valid_moves) == 0
        
        if depth == 0 or is_terminal:
            if is_terminal:
                winner = self._check_winner_board(board)
                if winner == self.symbol:
                    return (float('inf'), None)
                elif winner == self.opponent_symbol:
                    return (float('-inf'), None)
                else:
                    return (0, None)
            else:
                return (self._score_position(board, self.symbol), None)
        
        if maximizing_player:
            value = float('-inf')
            best_column = random.choice(valid_moves)
            
            for col in valid_moves:
                row = self._get_next_open_row(board, col)
                if row is not None:
                    temp_board = deepcopy(board)
                    temp_board[row][col] = self.symbol
                    
                    new_score = self._minimax(temp_board, depth - 1, alpha, beta, False)[0]
                    
                    if new_score > value:
                        value = new_score
                        best_column = col
                    
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            
            return (value, best_column)
        
        else:
            value = float('inf')
            best_column = random.choice(valid_moves)
            
            for col in valid_moves:
                row = self._get_next_open_row(board, col)
                if row is not None:
                    temp_board = deepcopy(board)
                    temp_board[row][col] = self.opponent_symbol
                    
                    new_score = self._minimax(temp_board, depth - 1, alpha, beta, True)[0]
                    
                    if new_score < value:
                        value = new_score
                        best_column = col
                    
                    beta = min(beta, value)
                    if alpha >= beta:
                        break
            
            return (value, best_column)
    
    def _center_heuristic(self, valid_moves):
        """
        Fallback: prefer center columns when minimax fails.
        Center columns (3, 2, 4, 1, 5, 0, 6) are generally better.
        """
        center_order = [3, 2, 4, 1, 5, 0, 6]
        for col in center_order:
            if col in valid_moves:
                return col
        return valid_moves[0]
