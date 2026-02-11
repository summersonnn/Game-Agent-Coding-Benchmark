"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.EMPTY = ' '

    def make_move(self, board: list[str]) -> int:
        available_moves = [i for i, spot in enumerate(board) if spot == self.EMPTY]
        if not available_moves:
            return None  # Though this shouldn't happen in a valid game
        
        best_move = None
        best_value = -float('inf')
        
        for move in available_moves:
            board_copy = board.copy()
            board_copy[move] = self.symbol
            move_value = self._minimax(board_copy, False)  # After my move, it's opponent's turn
            if move_value > best_value:
                best_value = move_value
                best_move = move
        
        return best_move

    def _minimax(self, board: list[str], is_maximizing: bool, alpha: float = -float('inf'), beta: float = float('inf')) -> float:
        if self._is_winner(board, self.symbol):
            return 1
        if self._is_winner(board, self.opponent):
            return -1
        if self._is_draw(board):
            return 0
        
        available_moves = [i for i, spot in enumerate(board) if spot == self.EMPTY]
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in available_moves:
                board[move] = self.symbol
                eval = self._minimax(board, False, alpha, beta)
                board[move] = self.EMPTY  # Undo move
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available_moves:
                board[move] = self.opponent
                eval = self._minimax(board, True, alpha, beta)
                board[move] = self.EMPTY  # Undo move
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _is_winner(self, board: list[str], player: str) -> bool:
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)               # Diagonals
        ]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] == player:
                return True
        return False

    def _is_draw(self, board: list[str]) -> bool:
        return self.EMPTY not in board
