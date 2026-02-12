"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-max
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
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.search_depth = 5  # Adjust based on performance needs

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
        # Get valid moves (columns that aren't full)
        valid_moves = self.get_valid_moves(board)
        
        # If no valid moves, return a random column (though game should be over)
        if not valid_moves:
            return random.randint(0, 6)
        
        # If we can win immediately, do it
        for col in valid_moves:
            temp_board = self.copy_board(board)
            self.make_move_on_board(temp_board, col, self.symbol)
            if self.check_winner(temp_board) == self.symbol:
                return col
        
        # If opponent can win next turn, block it
        for col in valid_moves:
            temp_board = self.copy_board(board)
            self.make_move_on_board(temp_board, col, self.opponent_symbol)
            if self.check_winner(temp_board) == self.opponent_symbol:
                return col
        
        # Use minimax with alpha-beta pruning for the best move
        best_score = -math.inf
        best_col = valid_moves[0]
        
        for col in valid_moves:
            temp_board = self.copy_board(board)
            self.make_move_on_board(temp_board, col, self.symbol)
            score = self.minimax(temp_board, self.search_depth - 1, -math.inf, math.inf, False)
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col
    
    def get_valid_moves(self, board):
        """Return a list of valid column indices (not full)."""
        valid_moves = []
        for col in range(7):
            if board[0][col] == ' ':  # If top row is empty, column isn't full
                valid_moves.append(col)
        return valid_moves
    
    def copy_board(self, board):
        """Return a deep copy of the board."""
        return [row[:] for row in board]
    
    def make_move_on_board(self, board, col, symbol):
        """Place a disc in the specified column."""
        for row in range(5, -1, -1):  # Start from bottom row
            if board[row][col] == ' ':
                board[row][col] = symbol
                break
    
    def check_winner(self, board):
        """Check if there's a winner on the board."""
        # Horizontal check
        for r in range(6):
            for c in range(4):
                if (board[r][c] != ' ' and 
                    board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]):
                    return board[r][c]
        
        # Vertical check
        for r in range(3):
            for c in range(7):
                if (board[r][c] != ' ' and 
                    board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]):
                    return board[r][c]
        
        # Diagonal (\) check
        for r in range(3):
            for c in range(4):
                if (board[r][c] != ' ' and 
                    board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]):
                    return board[r][c]
        
        # Diagonal (/) check
        for r in range(3, 6):
            for c in range(4):
                if (board[r][c] != ' ' and 
                    board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]):
                    return board[r][c]
        
        return None
    
    def is_terminal_node(self, board):
        """Check if the game is over (win or draw)."""
        return self.check_winner(board) is not None or len(self.get_valid_moves(board)) == 0
    
    def evaluate_window(self, window, symbol):
        """Evaluate a window of 4 positions for scoring."""
        score = 0
        opponent_symbol = self.opponent_symbol
        
        if window.count(symbol) == 4:
            score += 100
        elif window.count(symbol) == 3 and window.count(' ') == 1:
            score += 10
        elif window.count(symbol) == 2 and window.count(' ') == 2:
            score += 2
        
        if window.count(opponent_symbol) == 3 and window.count(' ') == 1:
            score -= 80  # Priority to block opponent's win
        
        return score
    
    def score_position(self, board, symbol):
        """Score the board position for the given symbol."""
        score = 0
        
        # Score center column (strategic advantage)
        center_array = [board[r][3] for r in range(6)]
        center_count = center_array.count(symbol)
        score += center_count * 3
        
        # Horizontal scoring
        for r in range(6):
            row_array = board[r]
            for c in range(4):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, symbol)
        
        # Vertical scoring
        for c in range(7):
            col_array = [board[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, symbol)
        
        # Diagonal (\) scoring
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, symbol)
        
        # Diagonal (/) scoring
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, symbol)
        
        return score
    
    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning."""
        valid_moves = self.get_valid_moves(board)
        is_terminal = self.is_terminal_node(board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                winner = self.check_winner(board)
                if winner == self.symbol:
                    return 100000000000000
                elif winner == self.opponent_symbol:
                    return -100000000000000
                else:  # Game is over, no more valid moves (draw)
                    return 0
            else:  # Depth is zero
                return self.score_position(board, self.symbol)
        
        if maximizing_player:
            value = -math.inf
            for col in valid_moves:
                temp_board = self.copy_board(board)
                self.make_move_on_board(temp_board, col, self.symbol)
                new_score = self.minimax(temp_board, depth - 1, alpha, beta, False)
                value = max(value, new_score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:  # Minimizing player
            value = math.inf
            for col in valid_moves:
                temp_board = self.copy_board(board)
                self.make_move_on_board(temp_board, col, self.opponent_symbol)
                new_score = self.minimax(temp_board, depth - 1, alpha, beta, True)
                value = min(value, new_score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value
