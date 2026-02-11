"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-flash-preview
Run: 2
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    """
    An optimized Tic Tac Toe agent using the Minimax algorithm with memoization.
    It prioritizes winning quickly and delaying losses to maximize points and 
    tie-breaker scores.
    """
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.memo = {}

    def make_move(self, board: list[str]) -> int:
        """
        Calculates the best move using Minimax.
        """
        # Reset memoization for the current move calculation
        self.memo = {}
        
        available_moves = [i for i, cell in enumerate(board) if cell == ' ']
        
        # If the board is empty or the center is available early, taking the center is optimal
        if board[4] == ' ':
            return 4
            
        best_score = float('-inf')
        best_move = -1
        
        # Shuffle moves to ensure variety when multiple moves have the same optimal score
        random.shuffle(available_moves)

        for move in available_moves:
            # Simulate the move
            board[move] = self.symbol
            score = self.minimax(board, 0, False)
            # Undo the move
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
        
        # Fallback to a random move if something goes wrong, though minimax should always find a move
        if best_move == -1 and available_moves:
            return random.choice(available_moves)
            
        return best_move

    def _get_winner(self, b: list[str]):
        """
        Helper to check for a winner or a draw.
        """
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)               # Diagonals
        ]
        for i, j, k in win_conditions:
            if b[i] == b[j] == b[k] != ' ':
                return b[i]
        if ' ' not in b:
            return 'DRAW'
        return None

    def minimax(self, board: list[str], depth: int, is_maximizing: bool) -> int:
        """
        Recursive minimax algorithm to evaluate board states.
        Score heuristic: (10 - depth) for a win, (depth - 10) for a loss.
        This encourages the agent to win as fast as possible and lose as slowly as possible.
        """
        state_key = tuple(board)
        if state_key in self.memo:
            return self.memo[state_key]

        winner = self._get_winner(board)
        if winner == self.symbol:
            return 10 - depth
        if winner == self.opponent:
            return depth - 10
        if winner == 'DRAW':
            return 0

        if is_maximizing:
            best_score = float('-inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            self.memo[state_key] = best_score
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    score = self.minimax(board, depth + 1, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            self.memo[state_key] = best_score
            return best_score
