"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-haiku-4.5
Run: 1
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    """
    Tic Tac Toe agent using minimax with alpha-beta pruning.
    This strategy is optimal for tic-tac-toe and will always win or draw.
    """
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        """
        Return the best move using minimax with alpha-beta pruning.
        """
        available_moves = [i for i in range(9) if board[i] == ' ']
        
        if not available_moves:
            return None
        
        if len(available_moves) == 1:
            return available_moves[0]
        
        best_score = float('-inf')
        best_move = available_moves[0]
        
        for move in available_moves:
            board[move] = self.symbol
            score = self.minimax(board, 0, False, float('-inf'), float('inf'))
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move

    def minimax(self, board, depth, is_maximizing, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning.
        Returns a score: 10-depth for wins (prefer fast wins),
                        depth-10 for losses (prefer slow losses),
                        0 for draws.
        """
        winner = self.check_winner(board)
        
        # Terminal states
        if winner == self.symbol:
            return 10 - depth
        elif winner == self.opponent:
            return depth - 10
        elif winner == 'DRAW':
            return 0
        
        available_moves = [i for i in range(9) if board[i] == ' ']
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in available_moves:
                board[move] = self.symbol
                eval_score = self.minimax(board, depth + 1, False, alpha, beta)
                board[move] = ' '
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available_moves:
                board[move] = self.opponent
                eval_score = self.minimax(board, depth + 1, True, alpha, beta)
                board[move] = ' '
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def check_winner(self, board):
        """
        Check if there's a winner or if the board is full.
        Returns: self.symbol, self.opponent, 'DRAW', or None
        """
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6),
        ]
        for combo in win_conditions:
            if (board[combo[0]] == board[combo[1]] == board[combo[2]] and 
                board[combo[0]] != ' '):
                return board[combo[0]]
        
        if ' ' not in board:
            return 'DRAW'
        
        return None
