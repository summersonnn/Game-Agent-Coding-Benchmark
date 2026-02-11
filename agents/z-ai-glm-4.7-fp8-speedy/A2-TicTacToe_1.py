"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-11 20:47:17
"""

import math

import math

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        self.cache = {}

    def make_move(self, board):
        # Heuristic: Take center if available (strongest position)
        if board[4] == ' ':
            return 4
        
        best_score = -math.inf
        best_move = -1
        
        # Move ordering for efficiency: Center, Corners, Edges
        order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        available_moves = [i for i in order if board[i] == ' ']

        for move in available_moves:
            board[move] = self.symbol
            score = self.minimax(board, False)
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
        
        # Fallback: Should not be reached in a valid game state, but safety first
        if best_move == -1:
            empty_indices = [i for i, x in enumerate(board) if x == ' ']
            if empty_indices:
                # random is assumed to be available in the global scope
                return random.choice(empty_indices)
            
        return best_move

    def minimax(self, board, is_maximizing):
        # Create a unique key for the board state and turn
        state_key = (tuple(board), is_maximizing)
        if state_key in self.cache:
            return self.cache[state_key]

        winner = self.check_winner(board)
        empty_cells = board.count(' ')

        # Terminal state checks with tie-breaker scoring
        if winner == self.symbol:
            # Win: Score is max(empty_cells_remaining, 3)
            return max(empty_cells, 3)
        elif winner == self.opponent_symbol:
            # Loss: Score is -max(empty_cells_remaining, 3)
            return -max(empty_cells, 3)
        elif empty_cells == 0:
            # Draw
            return 0

        if is_maximizing:
            best_score = -math.inf
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            self.cache[state_key] = best_score
            return best_score
        else:
            best_score = math.inf
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent_symbol
                    score = self.minimax(board, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            self.cache[state_key] = best_score
            return best_score

    def check_winner(self, board):
        lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)               # Diagonals
        ]
        for a, b, c in lines:
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        return None
