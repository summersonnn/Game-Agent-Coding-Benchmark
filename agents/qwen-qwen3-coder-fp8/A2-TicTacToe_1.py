"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder@preset/fp8
Run: 1
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    """
    An AI agent for playing Tic Tac Toe using the minimax algorithm with alpha-beta pruning.
    """

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        """
        Return the index (0-8) of the cell you want to mark.
        Uses minimax with alpha-beta pruning to determine the best move.
        """
        # Check if any immediate winning move is available
        for move in self._get_available_moves(board):
            board_copy = board[:]
            board_copy[move] = self.symbol
            if self._check_winner(board_copy) == self.symbol:
                return move

        # Check if opponent has a winning move and block it
        for move in self._get_available_moves(board):
            board_copy = board[:]
            board_copy[move] = self.opponent_symbol
            if self._check_winner(board_copy) == self.opponent_symbol:
                return move

        # Use minimax for optimal move
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        for move in self._get_available_moves(board):
            board_copy = board[:]
            board_copy[move] = self.symbol
            value = self._minimax(board_copy, False, alpha, beta, 0)
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)
            
        return best_move if best_move is not None else random.choice(self._get_available_moves(board))

    def _minimax(self, board, is_maximizing, alpha, beta, depth):
        winner = self._check_winner(board)
        
        if winner == self.symbol:
            return 10 - depth
        elif winner == self.opponent_symbol:
            return depth - 10
        elif winner == 'DRAW' or not self._get_available_moves(board):
            return 0
            
        if is_maximizing:
            max_eval = float('-inf')
            for move in self._get_available_moves(board):
                board_copy = board[:]
                board_copy[move] = self.symbol
                eval_score = self._minimax(board_copy, False, alpha, beta, depth + 1)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in self._get_available_moves(board):
                board_copy = board[:]
                board_copy[move] = self.opponent_symbol
                eval_score = self._minimax(board_copy, True, alpha, beta, depth + 1)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def _get_available_moves(self, board):
        return [i for i, spot in enumerate(board) if spot == ' ']

    def _check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
                
        if ' ' not in board:
            return 'DRAW'
            
        return None
