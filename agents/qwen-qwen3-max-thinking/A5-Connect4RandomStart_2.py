"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-max-thinking
Run: 2
Generated: 2026-02-13 14:10:12
"""



import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opp_symbol = 'Y' if symbol == 'R' else 'R'
        # Move ordering: prioritize center, then symmetry
        self.move_order = [3, 2, 4, 1, 5, 0, 6]
    
    def get_valid_moves(self, board):
        """Return list of columns with free space (top row empty)."""
        return [c for c in range(7) if board[0][c] == ' ']
    
    def get_next_open_row(self, board, col):
        """Find the lowest empty row in given column."""
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                return r
        return None  # Should not occur for valid columns
    
    def is_winning_move(self, board, piece):
        """Check if the given piece has a winning position on this board."""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if (board[r][c] == piece and board[r][c+1] == piece and 
                    board[r][c+2] == piece and board[r][c+3] == piece):
                    return True
        
        # Vertical
        for r in range(3):
            for c in range(7):
                if (board[r][c] == piece and board[r+1][c] == piece and 
                    board[r+2][c] == piece and board[r+3][c] == piece):
                    return True
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if (board[r][c] == piece and board[r+1][c+1] == piece and 
                    board[r+2][c+2] == piece and board[r+3][c+3] == piece):
                    return True
        
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if (board[r][c] == piece and board[r-1][c+1] == piece and 
                    board[r-2][c+2] == piece and board[r-3][c+3] == piece):
                    return True
        
        return False
    
    def evaluate_window(self, window):
        """Score a window of 4 positions for strategic value."""
        score = 0
        empty = ' '
        empty_count = window.count(empty)
        
        # Aggressive scoring for agent threats
        if (self.symbol == 'R' and window.count('R') == 3 and empty_count == 1) or \
           (self.symbol == 'Y' and window.count('Y') == 3 and empty_count == 1):
            score += 150
        
        if windows.count(self.symbol) == 2 and empty_count == 2:
            score += 20
        
        # Critical opponent threat blocking
        if opp_count == 3 and empty_count == 1:
            score -= 200  # Prioritize blocking threats
        
        if opp_count == 2 and empty_count == 2:
            score -= 30
        
        return score
    
    def evaluate_board(self, board):
        score = 0
        
        # Center control bonus (most valuable column)
        center_col = [board[r][3] for r in range(6)]
        score += center_col.count(self.symbol) * 5
        
        # Analyze all possible 4-in-a-row windows
        # Horizontal
        for r in range(6):
            row = board[r]
            for c in range(4):
                window = row[c:c+4]
                score += self.evaluate_window(window)
        
        # Vertical
        for c in range(7):
            col_array = [board[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window)
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window)
        
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window)
        
        return score
    
    def minimax(self, board, depth, alpha, beta, is_maximizing):
        """Alpha-beta minimax tree searcher."""
        # Terminal checks
        if self.is_winning_move(board, self.symbol):
            return float('inf')
        if self.is_winning_move(board, self.opp_symbol):
            return float('-inf')
        if all(board[0][c] != ' ' for c in range(7)):  # Draw
            return 0
        if depth == 0:
            return self.evaluate_board(board)
        
        valid_moves = self.get_valid_moves(board)
        moves = [m for m in self.move_order if m in valid_moves]
        
        if is_maximizing:
            value = float('-inf')
            for col in moves:
                row = self.get_next_open_row(board, col)
                board[row][col] = self.symbol
                score = self.minimax(board, depth-1, alpha, beta, False)
                board[row][col] = ' '
                value = max(value, score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for col in moves:
                row = self.get_next_open_row(board, col)
                board[row][col] = self.opp_symbol
                score = self.minimax(board, depth-1, alpha, beta, True)
                board[row][col] = ' '
                value = min(value, score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value
    
    def make_move(self, board):
        """Return optimal column choice with strategic checks."""
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return self.move_order[0]  # Fallback
        
        # Order moves by strategic priority
        moves = [m for m in self.move_order if m in valid_moves]
        
        # ➊ IMMEDIATE WIN CHECK: Check if we can win this turn
        for col in moves:
            row = self.get_next_open_row(board, col)
            board[row][col] = self.symbol
            if self.is_winning_move(board, self.symbol):
                board[row][col] = ' '
                return col
            board[row][col] = ' '
        
        # ❼ OPPONENT WIN BLOCK: Check if any move blocks opponent's win
        for col in moves:
            row = self.get_next_open_row(board, col)
            board[row][col] = self.opp_symbol
            if self.is_winning_move(board, self.opp_symbol):
                board[row][col] = ' '
                return col
            board[row][col] = ' '
        
        # ➌ DEPTH-ADAPTIVE SEARCH: Adjust depth based on game stage
        pieces_on_board = sum(row.count('R') + row.count('Y') for row in board)
        # Early game: depth=4 | Mid game: depth=5 | Late game: depth=6+
        max_depth = 4 + min((pieces_on_board - 1) // 10, 3)  # Max depth 7
        
        # ➍ MINIMAX SEARCH with alpha-beta pruning
        best_score = float('-inf')
        best_col = moves[0]
        alpha = float('-inf')
        beta = float('inf')
        
        for col in moves:
            row = self.get_next_open_row(board, col)
            board[row][col] = self.symbol
            score = self.minimax(board, max_depth - 1, alpha, beta, False)
            board[row][col] = ' '
            
            if score > best_score:
                best_score = score
                best_col = col
                alpha = max(alpha, best_score)
            
            # Alpha-beta pruned search
            if alpha >= beta:
                break
        
        return best_col
