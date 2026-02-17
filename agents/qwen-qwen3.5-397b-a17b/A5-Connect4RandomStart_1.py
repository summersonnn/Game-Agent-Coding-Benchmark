"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3.5-397b-a17b
Run: 1
Generated: 2026-02-16 17:46:27
"""



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

    def make_move(self, board):
        """
        Decide the next move based on the current board state.
        
        Args:
            board: A list of lists representing the 6x7 grid.
                   board[row][col] contains 'R', 'Y', or ' ' (empty).
                   Row 0 is the top, Row 5 is the bottom.
                   
        Returns:
            int: The column index (0-6) where the agent wants to drop a disc.
            
        Note:
            - If your agent crashes, times out, or returns an invalid move, 
              a random valid move will be played instead.
        """
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        if not valid_moves:
            return 0
        
        if len(valid_moves) == 1:
            return valid_moves[0]

        # Move ordering: prefer center columns to improve alpha-beta pruning
        valid_moves.sort(key=lambda c: abs(c - 3))

        best_move = valid_moves[0]
        best_score = -float('inf')
        depth = 5 

        for col in valid_moves:
            row = self._get_next_row(board, col)
            board[row][col] = self.symbol
            
            score = self._minimax(board, depth - 1, -float('inf'), float('inf'), False)
            
            board[row][col] = ' '
            
            if score > best_score:
                best_score = score
                best_move = col
        
        return best_move

    def _get_next_row(self, board, col):
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return -1

    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 100000 + depth
        elif winner == self.opponent_symbol:
            return -100000 - depth
        elif self._is_full(board):
            return 0
        
        if depth == 0:
            return self._evaluate(board)

        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        valid_moves.sort(key=lambda c: abs(c - 3))

        if maximizing_player:
            max_eval = -float('inf')
            for col in valid_moves:
                row = self._get_next_row(board, col)
                board[row][col] = self.symbol
                eval = self._minimax(board, depth - 1, alpha, beta, False)
                board[row][col] = ' '
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                row = self._get_next_row(board, col)
                board[row][col] = self.opponent_symbol
                eval = self._minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = ' '
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _check_winner(self, board):
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        return None

    def _is_full(self, board):
        return all(board[0][c] != ' ' for c in range(self.cols))

    def _evaluate(self, board):
        score = 0
        # Center preference
        center_array = [board[r][3] for r in range(self.rows)]
        center_count = center_array.count(self.symbol)
        score += center_count * 3
        
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                window = [board[r][c+i] for i in range(4)]
                score += self._evaluate_window(window)
        
        # Vertical
        for c in range(self.cols):
            for r in range(self.rows - 3):
                window = [board[r+i][c] for i in range(4)]
                score += self._evaluate_window(window)
        
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window)
        
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window)
                
        return score

    def _evaluate_window(self, window):
        score = 0
        my_count = window.count(self.symbol)
        opp_count = window.count(self.opponent_symbol)
        empty_count = window.count(' ')
        
        if my_count == 4:
            score += 100
        elif my_count == 3 and empty_count == 1:
            score += 5
        elif my_count == 2 and empty_count == 2:
            score += 2
            
        if opp_count == 3 and empty_count == 1:
            score -= 4
        if opp_count == 2 and empty_count == 2:
            score -= 1
            
        return score
