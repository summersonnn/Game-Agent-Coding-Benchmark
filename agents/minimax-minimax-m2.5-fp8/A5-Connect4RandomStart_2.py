"""
Agent Code: A5-Connect4RandomStart
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-13 14:10:12
"""



import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.ROWS = 6
        self.COLS = 7

    def make_move(self, board):
        # Get valid columns (not full)
        valid_locations = [c for c in range(self.COLS) if board[0][c] == ' ']
        
        if not valid_locations:
            return 0
            
        # 1. Check for immediate winning move
        for col in valid_locations:
            b_copy = [row[:] for row in board]
            row = self.get_next_open_row(b_copy, col)
            self.drop_piece(b_copy, row, col, self.symbol)
            if self.check_winner(b_copy, self.symbol):
                return col

        # 2. Check for move to block opponent's immediate win
        for col in valid_locations:
            b_copy = [row[:] for row in board]
            row = self.get_next_open_row(b_copy, col)
            self.drop_piece(b_copy, row, col, self.opponent_symbol)
            if self.check_winner(b_copy, self.opponent_symbol):
                return col
        
        # 3. Use Minimax with Alpha-Beta Pruning
        # Shuffle valid moves to add randomness to equal-score decisions
        random.shuffle(valid_locations)
        
        best_score = float('-inf')
        best_col = random.choice(valid_locations)
        
        # Depth 5 provides good balance of speed and strength
        depth = 5
        alpha = float('-inf')
        beta = float('inf')
        
        for col in valid_locations:
            b_copy = [row[:] for row in board]
            row = self.get_next_open_row(b_copy, col)
            self.drop_piece(b_copy, row, col, self.symbol)
            
            # Minimax call (minimizing for opponent next)
            new_score = self.minimax(b_copy, depth - 1, alpha, beta, False)
            
            if new_score > best_score:
                best_score = new_score
                best_col = col
                
            alpha = max(alpha, best_score)
            
        return best_col

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        valid_locations = [c for c in range(self.COLS) if board[0][c] == ' ']
        is_terminal = self.is_terminal_node(board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if self.check_winner(board, self.symbol):
                    return 10000000
                elif self.check_winner(board, self.opponent_symbol):
                    return -10000000
                else:
                    return 0
            else:
                # Depth 0 static evaluation
                return self.score_position(board, self.symbol)
        
        if maximizing_player:
            value = float('-inf')
            for col in valid_locations:
                b_copy = [row[:] for row in board]
                row = self.get_next_open_row(b_copy, col)
                self.drop_piece(b_copy, row, col, self.symbol)
                score = self.minimax(b_copy, depth - 1, alpha, beta, False)
                value = max(value, score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for col in valid_locations:
                b_copy = [row[:] for row in board]
                row = self.get_next_open_row(b_copy, col)
                self.drop_piece(b_copy, row, col, self.opponent_symbol)
                score = self.minimax(b_copy, depth - 1, alpha, beta, True)
                value = min(value, score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def get_next_open_row(self, board, col):
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return -1

    def drop_piece(self, board, row, col, piece):
        board[row][col] = piece

    def is_terminal_node(self, board):
        return self.check_winner(board, self.symbol) or \
               self.check_winner(board, self.opponent_symbol) or \
               len([c for c in range(self.COLS) if board[0][c] == ' ']) == 0

    def check_winner(self, board, piece):
        # Horizontal
        for c in range(self.COLS - 3):
            for r in range(self.ROWS):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        # Vertical
        for c in range(self.COLS):
            for r in range(self.ROWS - 3):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
        # Diagonal /
        for c in range(self.COLS - 3):
            for r in range(3, self.ROWS):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        # Diagonal \
        for c in range(self.COLS - 3):
            for r in range(self.ROWS - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        return False

    def score_position(self, board, piece):
        score = 0
        
        # Center column preference (more control)
        center_array = [board[r][self.COLS // 2] for r in range(self.ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 5
        
        # Horizontal
        for r in range(self.ROWS):
            row_array = board[r]
            for c in range(self.COLS - 3):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, piece)
                
        # Vertical
        for c in range(self.COLS):
            col_array = [board[r][c] for r in range(self.ROWS)]
            for r in range(self.ROWS - 3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, piece)
                
        # Diagonal /
        for c in range(self.COLS - 3):
            for r in range(3, self.ROWS):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)
                
        # Diagonal \
        for c in range(self.COLS - 3):
            for r in range(self.ROWS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)
                
        return score

    def evaluate_window(self, window, piece):
        score = 0
        opp_piece = self.opponent_symbol
        
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(' ') == 1:
            score += 10
        elif window.count(piece) == 2 and window.count(' ') == 2:
            score += 2
            
        if window.count(opp_piece) == 3 and window.count(' ') == 1:
            score -= 10 # Strongly discourage allowing opponent 3-in-row
            
        return score
