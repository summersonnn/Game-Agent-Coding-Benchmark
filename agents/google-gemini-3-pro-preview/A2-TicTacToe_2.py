"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-pro-preview
Run: 2
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    """
    An unbeatable Tic Tac Toe agent using the Minimax algorithm with Alpha-Beta pruning.
    It prioritizes winning, then winning quickly, then drawing, and finally prolonging a loss.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        self.cache = {}

    def make_move(self, board):
        """
        Calculates the best move given the current board state.
        """
        # Identify all valid empty cells
        valid_moves = [i for i, cell in enumerate(board) if cell == ' ']
        
        # If no moves available, return a sentinel (though game loop shouldn't call this)
        if not valid_moves:
            return -1

        # Optimization: If it's the very first move of the game (X starts), take Center (4).
        # This is a theoretically optimal opening and saves search time.
        if len(valid_moves) == 9:
            return 4
        
        # Optimization: If only one move is available, take it immediately.
        if len(valid_moves) == 1:
            return valid_moves[0]

        # Randomize move order to ensure variety when multiple moves have the same optimal score.
        # random is available from the global scope as per instructions.
        random.shuffle(valid_moves)

        best_score = -float('inf')
        best_move = valid_moves[0]
        alpha = -float('inf')
        beta = float('inf')

        for move in valid_moves:
            # Simulate the move
            new_board = list(board)
            new_board[move] = self.symbol
            
            # Call Minimax. Next turn is opponent's (Minimizing player)
            score = self.minimax(new_board, False, alpha, beta)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            # Alpha-Beta Pruning: update alpha
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        
        return best_move

    def minimax(self, board, is_maximizing, alpha, beta):
        # Use a tuple of the board state and turn flag as the cache key
        state_key = (tuple(board), is_maximizing)
        if state_key in self.cache:
            return self.cache[state_key]

        # Check for terminal states
        winner = self.check_winner(board)
        empty_count = board.count(' ')

        # Scoring Logic:
        # Win: Base 100 + empty_count (Rewards winning in fewer moves)
        # Loss: Base -100 - empty_count (Rewards prolonging the game if loss is inevitable)
        # Draw: 0
        if winner == self.symbol:
            return 100 + empty_count
        elif winner == self.opponent_symbol:
            return -100 - empty_count
        elif empty_count == 0:
            return 0

        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval_score = self.minimax(board, False, alpha, beta)
                    board[i] = ' ' # Backtrack
                    
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            self.cache[state_key] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent_symbol
                    eval_score = self.minimax(board, True, alpha, beta)
                    board[i] = ' ' # Backtrack
                    
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            self.cache[state_key] = min_eval
            return min_eval

    def check_winner(self, board):
        """
        Helper to check if there is a winner on the current board.
        Returns 'X', 'O', or None.
        """
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] and board[a] != ' ':
                return board[a]
        return None
