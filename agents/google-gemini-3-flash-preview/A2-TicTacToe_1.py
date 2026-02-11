"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-flash-preview
Run: 1
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    """
    An optimized Tic Tac Toe agent using the Minimax algorithm with depth-based 
    scoring to ensure perfect play and maximize tie-breaker points.
    """
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)               # Diagonals
        ]

    def _check_winner(self, board: list[str]) -> str:
        """Helper to check the winner of a board state."""
        for combo in self.win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _minimax(self, board: list[str], depth: int, is_maximizing: bool) -> int:
        """Recursive minimax to find the best score for a state."""
        res = self._check_winner(board)
        if res == self.symbol:
            return 10 - depth
        if res == self.opponent:
            return depth - 10
        if res == 'DRAW':
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self._minimax(board, depth + 1, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    score = self._minimax(board, depth + 1, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            return best_score

    def make_move(self, board: list[str]) -> int:
        """
        Calculates the optimal move. If it's the first move of the game, 
        it takes the center or a corner for efficiency. Otherwise, it uses Minimax.
        """
        # Hardcoded optimization for the very first move to save time/computation
        empty_count = board.count(' ')
        if empty_count == 9:
            return 4  # Start in the center
        if empty_count == 8 and board[4] == ' ':
            return 4  # Take center if opponent didn't

        best_move = -1
        best_val = -float('inf')
        
        # Check all available moves
        available_moves = [i for i, cell in enumerate(board) if cell == ' ']
        
        # If only one move left, just take it
        if len(available_moves) == 1:
            return available_moves[0]

        # Shuffle moves to ensure variety in non-critical situations 
        # (though in perfect play, outcomes are deterministic)
        random.shuffle(available_moves)

        for move in available_moves:
            board[move] = self.symbol
            move_val = self._minimax(board, 0, False)
            board[move] = ' '
            
            if move_val > best_val:
                best_val = move_val
                best_move = move

        return best_move
