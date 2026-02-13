"""
Agent Code: A2-TicTacToe
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        # Precompute all possible winning triplets for quick lookup
        self.win_conditions = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 1, start + 2))
        # Columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_conditions.append((start, start + 4, start + 8))

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return None

        # Check for immediate winning move
        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.symbol
            if self.check_win(temp_board, self.symbol):
                return move

        # Block opponent's immediate winning move
        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.opponent_symbol
            if self.check_win(temp_board, self.opponent_symbol):
                return move

        # Create or block potential forks (two ways to win)
        fork_moves = self.find_forks(board, self.symbol)
        if fork_moves:
            return random.choice(fork_moves)

        opponent_fork_moves = self.find_forks(board, self.opponent_symbol)
        if opponent_fork_moves:
            # Try to block one of the fork moves
            return random.choice(opponent_fork_moves)

        # Center control (prioritize center and corners)
        center = 12
        if center in available_moves:
            return center

        corners = [0, 4, 20, 24]
        for corner in corners:
            if corner in available_moves:
                return corner

        # Try to create a two-in-a-row with an open end
        two_in_a_row_moves = self.find_two_in_a_row(board, self.symbol)
        if two_in_a_row_moves:
            return random.choice(two_in_a_row_moves)

        # Block opponent's two-in-a-row
        opponent_two_in_a_row = self.find_two_in_a_row(board, self.opponent_symbol)
        if opponent_two_in_a_row:
            return random.choice(opponent_two_in_a_row)

        # Default to random move if no strategic move found
        return random.choice(available_moves)

    def check_win(self, board, symbol):
        for combo in self.win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] == symbol:
                return True
        return False

    def find_forks(self, board, symbol):
        fork_moves = []
        for move in [i for i, spot in enumerate(board) if spot == EMPTY]:
            temp_board = board.copy()
            temp_board[move] = symbol
            winning_combos = 0
            for combo in self.win_conditions:
                if (temp_board[combo[0]] == symbol or temp_board[combo[0]] == EMPTY) and \
                   (temp_board[combo[1]] == symbol or temp_board[combo[1]] == EMPTY) and \
                   (temp_board[combo[2]] == symbol or temp_board[combo[2]] == EMPTY):
                    count = sum(1 for pos in combo if temp_board[pos] == symbol)
                    empty = sum(1 for pos in combo if temp_board[pos] == EMPTY)
                    if count == 1 and empty == 2:
                        winning_combos += 1
            if winning_combos >= 2:
                fork_moves.append(move)
        return fork_moves

    def find_two_in_a_row(self, board, symbol):
        two_in_a_row_moves = []
        for combo in self.win_conditions:
            cells = [board[pos] for pos in combo]
            if cells.count(symbol) == 2 and cells.count(EMPTY) == 1:
                empty_pos = combo[cells.index(EMPTY)]
                if empty_pos in [i for i, spot in enumerate(board) if spot == EMPTY]:
                    two_in_a_row_moves.append(empty_pos)
        return two_in_a_row_moves
