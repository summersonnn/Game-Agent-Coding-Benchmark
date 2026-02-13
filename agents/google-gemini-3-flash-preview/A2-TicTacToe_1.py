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
        self.win_conditions = self._generate_win_conditions()

    def _generate_win_conditions(self):
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

        # 3. Strategic positioning: Prefer the center 3x3 area
        # These cells (6, 7, 8, 11, 12, 13, 16, 17, 18) are parts of more winning combos
        center_indices = [12, 6, 8, 16, 18, 7, 11, 13, 17]
        for idx in center_indices:
            if idx in available_moves:
                return idx

        # 4. Fallback to random available move
        return random.choice(available_moves)

    def _is_winning_move(self, board, move, player_symbol):
        """Simulates a move to see if it results in a win."""
        # Temporary move
        board[move] = player_symbol
        is_win = False
        
        # We only check conditions that involve the move just made for efficiency
        for combo in self.win_conditions:
            if move in combo:
                if board[combo[0]] == board[combo[1]] == board[combo[2]] == player_symbol:
                    is_win = True
                    break
        
        # Undo move
        board[move] = ' '
        return is_win