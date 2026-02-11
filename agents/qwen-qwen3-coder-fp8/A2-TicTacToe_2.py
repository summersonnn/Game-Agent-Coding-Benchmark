"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder@preset/fp8
Run: 2
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    """
    An intelligent Tic Tac Toe agent that uses the minimax algorithm
    with alpha-beta pruning to make optimal moves.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        """
        Return the index (0-8) of the cell you want to mark.
        Uses minimax with alpha-beta pruning for optimal play.
        """
        # Check for winning move
        for move in range(9):
            if board[move] == ' ':
                board[move] = self.symbol
                if self._check_winner(board) == self.symbol:
                    return move
                board[move] = ' '

        # Check for blocking opponent's winning move
        for move in range(9):
            if board[move] == ' ':
                board[move] = self.opponent_symbol
                if self._check_winner(board) == self.opponent_symbol:
                    return move
                board[move] = ' '

        # Use minimax for optimal move
        best_move = self._minimax(board, True, -float('inf'), float('inf'))[1]
        if best_move is not None:
            return best_move

        # Fallback to random move (should never happen with minimax)
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        return random.choice(available_moves) if available_moves else None

    def _check_winner(self, board):
        """Check if there's a winner on the board."""
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _minimax(self, board, is_maximizing, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning.
        Returns (score, move) tuple.
        """
        winner = self._check_winner(board)
        
        # Terminal states
        if winner == self.symbol:
            return (10, None)
        elif winner == self.opponent_symbol:
            return (-10, None)
        elif winner == 'DRAW':
            return (0, None)
            
        # Non-terminal state
        best_move = None
        if is_maximizing:
            max_eval = -float('inf')
            for move in range(9):
                if board[move] == ' ':
                    board[move] = self.symbol
                    eval_score = self._minimax(board, False, alpha, beta)[0]
                    board[move] = ' '
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = move
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            return (max_eval, best_move)
        else:
            min_eval = float('inf')
            for move in range(9):
                if board[move] == ' ':
                    board[move] = self.opponent_symbol
                    eval_score = self._minimax(board, True, alpha, beta)[0]
                    board[move] = ' '
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = move
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            return (min_eval, best_move)
