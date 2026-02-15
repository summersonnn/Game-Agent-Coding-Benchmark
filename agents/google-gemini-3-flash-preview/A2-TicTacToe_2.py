"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-flash-preview
Run: 2
Generated: 2026-02-13 14:53:21
"""


import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_conditions = self._generate_win_conditions()

    def _generate_win_conditions(self):
        conditions = []
        # Horizontal rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                conditions.append((start, start + 1, start + 2))
        # Vertical columns
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
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return None

        # 1. Check for immediate win
        for move in available_moves:
            if self._is_winning_move(board, move, self.symbol):
                return move

        # 2. Block opponent's immediate win
        for move in available_moves:
            if self._is_winning_move(board, move, self.opponent):
                return move

        # 3. Create a "Two-in-a-row" with an open end (Offense)
        # Prioritize moves that belong to multiple potential winning lines
        move_scores = {move: 0 for move in available_moves}
        for combo in self.win_conditions:
            marks = [board[i] for i in combo]
            # Check if we have 1 mark and 2 empties in a line
            if marks.count(self.symbol) == 1 and marks.count(' ') == 2:
                for i in combo:
                    if board[i] == ' ':
                        move_scores[i] += 1
            # Check if we can create a two-in-a-row
            elif marks.count(self.symbol) == 0 and marks.count(self.opponent) == 0:
                for i in combo:
                    if board[i] == ' ':
                        move_scores[i] += 0.5

        # 4. Positional Weighting (Center is better)
        center_weights = [
            2, 2, 2, 2, 2,
            2, 4, 4, 4, 2,
            2, 4, 6, 4, 2,
            2, 4, 4, 4, 2,
            2, 2, 2, 2, 2
        ]
        
        for move in available_moves:
            move_scores[move] += center_weights[move]

        # Return move with highest score
        best_move = max(available_moves, key=lambda m: move_scores[m])
        return best_move

    def _is_winning_move(self, board, move, player_symbol):
        # Temporarily place mark
        board[move] = player_symbol
        is_win = False
        for combo in self.win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] == player_symbol:
                is_win = True
                break
        # Revert move
        board[move] = ' '
        return is_win