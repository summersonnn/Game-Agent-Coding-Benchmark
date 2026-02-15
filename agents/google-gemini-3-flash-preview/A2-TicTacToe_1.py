"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-flash-preview
Run: 1
Generated: 2026-02-13 14:53:21
"""


import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.grid_size = 5
        self.win_conditions = self._generate_win_conditions()

    def _generate_win_conditions(self):
        """Pre-calculates all possible triplets that result in a win."""
        conditions = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                conditions.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                conditions.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                conditions.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                conditions.append((start, start + 4, start + 8))
        return conditions

    def make_move(self, board):
        """Strategic move selection based on immediate win/loss and position weighting."""
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return None

        # 1. Check if we can win in this move
        for move in available_moves:
            if self._is_winning_move(board, move, self.symbol):
                return move

        # 2. Check if we need to block the opponent's winning move
        for move in available_moves:
            if self._is_winning_move(board, move, self.opponent):
                return move

        # 3. Positional Strategy: Weight cells by how many win conditions they belong to
        # The center (12) and inner ring are generally stronger.
        move_weights = {move: 0 for move in available_moves}
        for combo in self.win_conditions:
            # Count how many of our marks are already in this combo
            our_marks = sum(1 for idx in combo if board[idx] == self.symbol)
            opp_marks = sum(1 for idx in combo if board[idx] == self.opponent)
            
            # If the combo is still 'alive' (no opponent marks)
            if opp_marks == 0:
                for idx in combo:
                    if idx in move_weights:
                        move_weights[idx] += (1 + our_marks)
            
            # If we can block a future setup (opponent has 1, we have 0)
            if our_marks == 0 and opp_marks == 1:
                for idx in combo:
                    if idx in move_weights:
                        move_weights[idx] += 1

        # Pick the move with the highest weight
        if move_weights:
            best_move = max(move_weights, key=move_weights.get)
            return best_move

        return random.choice(available_moves)

    def _is_winning_move(self, board, move, player_symbol):
        """Temporary simulation to see if a move completes any 3-in-a-row."""
        for combo in self.win_conditions:
            if move in combo:
                # Check if the other two spots in this specific combo are held by the player
                others = [board[idx] for idx in combo if idx != move]
                if all(s == player_symbol for s in others):
                    return True
        return False