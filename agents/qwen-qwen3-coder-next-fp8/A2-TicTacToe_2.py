"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder-next@preset/fp8
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'


class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'

    def make_move(self, board):
        # Get all available moves
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return -1  # Will be caught and handled by game engine

        # If it's the very first move (only one empty cell is X's initial random placement),
        # and this agent is X, then board has 24 empties - but game engine already placed first X randomly
        # So we just play normally

        # Try to find immediate win
        for move in available_moves:
            board[move] = self.symbol
            if self._check_win(board, self.symbol):
                board[move] = EMPTY
                return move
            board[move] = EMPTY

        # Block opponent's immediate win
        opponent = O_MARK if self.symbol == X_MARK else X_MARK
        for move in available_moves:
            board[move] = opponent
            if self._check_win(board, opponent):
                board[move] = EMPTY
                return move
            board[move] = EMPTY

        # Prefer center (12) if available
        if 12 in available_moves:
            return 12

        # Prefer corners (0, 4, 20, 24) and edges strategically
        # For 5x5 grid, corners are 0,4,20,24; edge centers of sides are 2,7,12,17,22 (vertical) etc.
        # Better: use a heuristic scoring for positions
        best_move = None
        best_score = -float('inf')
        
        # Precompute win conditions for faster evaluation
        win_conditions = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                win_conditions.append((start, start + 4, start + 8))

        for move in available_moves:
            score = self._evaluate_move(board, move, win_conditions)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move if best_move is not None else random.choice(available_moves)

    def _check_win(self, board, player):
        # Check all win conditions
        win_conditions = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                win_conditions.append((start, start + 4, start + 8))

        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] == player:
                return True
        return False

    def _evaluate_move(self, board, move, win_conditions):
        # Temporarily make the move
        board[move] = self.symbol
        opponent = O_MARK if self.symbol == X_MARK else X_MARK
        
        score = 0
        
        # Count potential lines for self and opponent
        for combo in win_conditions:
            cells = [board[i] for i in combo]
            if self.symbol in cells and opponent not in cells:
                # Self has potential
                if cells.count(self.symbol) == 2:
                    score += 10  # High value: one step to win
                elif cells.count(self.symbol) == 1:
                    score += 2   # Medium value: one piece in line
            if opponent in cells and self.symbol not in cells:
                # Opponent has potential
                if cells.count(opponent) == 2:
                    score += 8   # High priority to block
                elif cells.count(opponent) == 1:
                    score += 1   # Medium to block

        # Bonus for center control
        if move == 12:
            score += 5
        
        # Slight bonus for controlling corners
        if move in [0, 4, 20, 24]:
            score += 1

        # Slight penalty for edge moves that are less strategic (but not too much)
        if move in [1, 3, 5, 9, 15, 19, 21, 23]:
            score -= 1

        # Reset board
        board[move] = EMPTY
        
        return score
