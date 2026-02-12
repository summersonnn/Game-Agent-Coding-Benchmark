"""
Agent Code: A5-Connect4RandomStart
Model: google-gemini-3-flash-preview
Run: 1
Generated: 2026-02-12 14:51:10
"""

import random
import copy

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.depth = 4  # Adjust based on performance (1s timeout)

    def make_move(self, board):
        valid_moves = [c for c in range(7) if board[0][c] == ' ']
        if not valid_moves:
            return 0
        
        # Priority: Center column is strategically strongest in Connect 4
        valid_moves.sort(key=lambda x: abs(3 - x))

        best_score = float('-inf')
        best_col = random.choice(valid_moves)

        for col in valid_moves:
            temp_board = copy.deepcopy(board)
            self._drop_sim_disc(temp_board, col, self.symbol)
            score = self._minimax(temp_board, self.depth - 1, False, float('-inf'), float('inf'))
            
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col

    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        winner = self._check_sim_winner(board)
        if winner == self.symbol: return 100000
        if winner == self.opponent: return -100000
        if depth == 0 or all(board[0][c] != ' ' for c in range(7)):
            return self._evaluate_board(board)

        valid_moves = [c for c in range(7) if board[0][c] == ' ']

        if is_maximizing:
            max_eval = float('-inf')
            for col in valid_moves:
                temp = copy.deepcopy(board)
                self._drop_sim_disc(temp, col, self.symbol)
                eval = self._minimax(temp, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                temp = copy.deepcopy(board)
                self._drop_sim_disc(temp, col, self.opponent)
                eval = self._minimax(temp, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    def _drop_sim_disc(self, board, col, symbol):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return

    def _evaluate_board(self, board):
        # Heuristic: Score based on potential lines and center control
        score = 0
        # Center weight
        center_array = [board[r][3] for r in range(6)]
        score += center_array.count(self.symbol) * 3
        return score # Simplified for brevity; can be expanded to check windows of 4

    def _check_sim_winner(self, b):
        # Optimized win check (similar logic to your engine)
        for r in range(6):
            for c in range(4):
                if b[r][c] != ' ' and b[r][c] == b[r][c+1] == b[r][c+2] == b[r][c+3]: return b[r][c]
        for r in range(3):
            for c in range(7):
                if b[r][c] != ' ' and b[r][c] == b[r+1][c] == b[r+2][c] == b[r+3][c]: return b[r][c]
        for r in range(3, 6):
            for c in range(4):
                if b[r][c] != ' ' and b[r][c] == b[r-1][c+1] == b[r-2][c+2] == b[r-3][c+3]: return b[r][c]
        for r in range(3):
            for c in range(4):
                if b[r][c] != ' ' and b[r][c] == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3]: return b[r][c]
        return None