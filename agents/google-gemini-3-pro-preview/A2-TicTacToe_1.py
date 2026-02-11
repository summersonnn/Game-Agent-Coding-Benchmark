"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-pro-preview
Run: 1
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    """
    An unbeatable Tic Tac Toe agent using the Minimax algorithm with Alpha-Beta pruning.
    It prioritizes winning as quickly as possible and prolonging the game when losing,
    optimizing for the match point and tie-breaker metrics.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        """
        Determines the best move using Minimax strategy.
        """
        available_moves = [i for i, cell in enumerate(board) if cell == ' ']

        # If no moves are available, return an indicator (game logic handles end)
        if not available_moves:
            return -1

        # Optimization: Check for immediate win to avoid search overhead
        for move in available_moves:
            board[move] = self.symbol
            if self._check_winner(board) == self.symbol:
                return move
            board[move] = ' '  # Backtrack

        # Optimization: If it's the very first move (empty board), take center.
        # This is the statistically best opening and saves processing time.
        if len(available_moves) == 9:
            return 4

        # Initialize Minimax
        best_score = -float('inf')
        best_move = available_moves[0]
        alpha = -float('inf')
        beta = float('inf')

        # Shuffle moves to ensure variety in gameplay for equal-value moves
        # (random is available in the global scope as per instructions)
        random.shuffle(available_moves)

        for move in available_moves:
            board[move] = self.symbol
            score = self._minimax(board, 0, False, alpha, beta)
            board[move] = ' '  # Backtrack

            if score > best_score:
                best_score = score
                best_move = move
            
            # Alpha-Beta Pruning Update
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        
        return best_move

    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        """
        Minimax recursive algorithm to evaluate board states.
        Returns a score: positive for win, negative for loss, 0 for draw.
        Adjusts score by depth to prefer winning sooner or losing later.
        """
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 100 - depth  # Win sooner is better
        elif winner == self.opponent:
            return depth - 100  # Lose later is better (minimize opp score)
        
        if ' ' not in board:
            return 0  # Draw

        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval = self._minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    eval = self._minimax(board, depth + 1, True, alpha, beta)
                    board[i] = ' '
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
            return min_eval

    def _check_winner(self, board):
        """
        Helper to check if there is a winner on the current board.
        Returns 'X', 'O', or None.
        """
        # check rows
        if board[0] == board[1] == board[2] != ' ': return board[0]
        if board[3] == board[4] == board[5] != ' ': return board[3]
        if board[6] == board[7] == board[8] != ' ': return board[6]
        # check columns
        if board[0] == board[3] == board[6] != ' ': return board[0]
        if board[1] == board[4] == board[7] != ' ': return board[1]
        if board[2] == board[5] == board[8] != ' ': return board[2]
        # check diagonals
        if board[0] == board[4] == board[8] != ' ': return board[0]
        if board[2] == board[4] == board[6] != ' ': return board[2]
        return None
