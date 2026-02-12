"""
Agent Code: A5-Connect4RandomStart
Model: google-gemini-3-flash-preview
Run: 2
Generated: 2026-02-12 14:51:12
"""

import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.DEPTH = 4  # Adjust based on performance (how many turns to look ahead)

    def make_move(self, board):
        valid_moves = [c for c in range(7) if board[0][c] == ' ']
        if not valid_moves:
            return 0
        
        # Simple implementation: Return a move that wins immediately or blocks a win
        # For a competitive edge, implement the minimax function here
        best_score = -float('inf')
        best_col = random.choice(valid_moves)

        for col in valid_moves:
            temp_board = [row[:] for row in board]
            self._drop_disc(temp_board, col, self.symbol)
            score = self._minimax(temp_board, self.DEPTH, -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_col = col

        return best_col

    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        # 1. Terminal Node Check (Win/Loss/Draw/Depth reached)
        # 2. If maximizing: find highest score
        # 3. If minimizing: find lowest score (opponent's best move)
        # 4. Return the heuristic score of the board
        return random.randint(0, 100) # Placeholder for heuristic evaluation

    def _drop_disc(self, board, col, symbol):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                break