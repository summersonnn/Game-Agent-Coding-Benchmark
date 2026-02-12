"""
Agent Code: A5-Connect4RandomStart
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-12 14:50:42
"""



class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        Strategy: Immediate win > Immediate block > Minimax lookahead
        """
        valid_cols = self.get_valid_columns(board)
        
        if not valid_cols:
            return 3  # Fallback (shouldn't happen)
        
        # Priority 1: Win immediately if possible
        for col in valid_cols:
            board_copy = [row[:] for row in board]
            self.drop_disc(board_copy, col, self.symbol)
            if self.check_winner(board_copy) == self.symbol:
                return col
        
        # Priority 2: Block opponent's immediate win
        for col in valid_cols:
            board_copy = [row[:] for row in board]
            self.drop_disc(board_copy, col, self.opponent_symbol)
            if self.check_winner(board_copy) == self.opponent_symbol:
                return col
        
        # Priority 3: Minimax with alpha-beta pruning
        _, best_col = self.minimax(
            board, depth=6, 
            alpha=float('-inf'), 
            beta=float('inf'), 
            maximizing=True
        )
        
        return best_col if best_col is not None else valid_cols[0]

    def minimax(self, board, depth, alpha, beta, maximizing):
        """
        Minimax algorithm with alpha-beta pruning.
        Returns (evaluation_score, best_column)
        """
        winner = self.check_winner(board)
        
        # Terminal states
        if winner == self.symbol:
            return (10000 + depth, None)  # Prefer faster wins
        elif winner == self.opponent_symbol:
            return (-10000 - depth, None)  # Prefer slower losses
        elif self.is_board_full(board):
            return (0, None)  # Draw
        elif depth == 0:
            return (self.evaluate_board(board), None)  # Heuristic eval
        
        valid_columns = self.get_valid_columns(board)
        if not valid_columns:
            return (0, None)
        
        if maximizing:  # Our turn (maximize score)
            max_eval = float('-inf')
            best_col = valid_columns[0]
            
            for col in valid_columns:
                board_copy = [row[:] for row in board]
                self.drop_disc(board_copy, col, self.symbol)
                eval_score, _ = self.minimax(board_copy, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cut-off
            
            return (max_eval, best_col)
        
        else:  # Opponent's turn (minimize score)
            min_eval = float('inf')
            best_col = valid_columns[0]
            
            for col in valid_columns:
                board_copy = [row[:] for row in board]
                self.drop_disc(board_copy, col, self.opponent_symbol)
                eval_score, _ = self.minimax(board_copy, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cut-off
            
            return (min_eval, best_col)

    def evaluate_board(self, board):
        """
        Heuristic evaluation of board position.
        Scores based on:
        - Threats (3-in-a-row patterns)
        - Center column control (key Connect4 strategy)
        """
        score = 0
        
        # Count threats (3-in-a-row with 1 empty)
        my_threats = self.count_threats(board, self.symbol)
        opp_threats = self.count_threats(board, self.opponent_symbol)
        score += my_threats * 100
        score -= opp_threats * 100
        
        # Center control (pieces in middle columns are more valuable)
        for r in range(len(board)):
            for c in range(len(board[0])):
                if board[r][c] == self.symbol:
                    score += (3 - abs(c - 3)) * 20
                elif board[r][c] == self.opponent_symbol:
                    score -= (3 - abs(c - 3)) * 20
        
        return score

    def count_threats(self, board, symbol):
        """Count 3-in-a-row patterns (immediate winning opportunities)."""
        threats = 0
        ROWS, COLS = len(board), len(board[0])
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [board[r][c+i] for i in range(4)]
                if window.count(symbol) == 3 and window.count(' ') == 1:
                    threats += 1
        
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                window = [board[r+i][c] for i in range(4)]
                if window.count(symbol) == 3 and window.count(' ') == 1:
                    threats += 1
        
        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                if window.count(symbol) == 3 and window.count(' ') == 1:
                    threats += 1
        
        # Diagonal \
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                if window.count(symbol) == 3 and window.count(' ') == 1:
                    threats += 1
        
        return threats

    def check_winner(self, board):
        """Check for 4 in a row."""
        ROWS, COLS = len(board), len(board[0])
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        
        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        
        # Diagonal \
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        
        return None

    def get_valid_columns(self, board):
        """Return valid column indices, ordered by centrality for better pruning."""
        valid = [c for c in range(len(board[0])) if board[0][c] == ' ']
        # Prioritize center columns (statistically better in Connect4)
        valid.sort(key=lambda c: abs(c - 3))
        return valid

    def is_board_full(self, board):
        """Check if board is completely full."""
        return all(board[0][c] != ' ' for c in range(len(board[0])))

    def drop_disc(self, board, col, symbol):
        """Drop a disc in the given column."""
        for r in range(len(board) - 1, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return True
        return False
