"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-13 14:53:21
"""



class TicTacToeAgent:
    """
    Your agent implementation goes here.
    Implement smart logic to beat your opponent.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        """
        Return the index (0-24) of the cell you want to mark.
        board: List of 25 strings representing the current board state.
              Each element is ' ' (empty), 'X', or 'O'.
        """
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return None

        # Generate all winning lines (3 in a row)
        win_lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                win_lines.append([r * 5 + c, r * 5 + c + 1, r * 5 + c + 2])
        # Columns
        for c in range(5):
            for r in range(3):
                win_lines.append([r * 5 + c, (r + 1) * 5 + c, (r + 2) * 5 + c])
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                win_lines.append([r * 5 + c, r * 5 + c + 6, r * 5 + c + 12])
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                win_lines.append([r * 5 + c, r * 5 + c + 4, r * 5 + c + 8])

        # Check for winning move
        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.symbol
            for line in win_lines:
                if all(temp_board[pos] == self.symbol for pos in line):
                    return move

        # Check for blocking opponent's win
        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.opponent
            for line in win_lines:
                if all(temp_board[pos] == self.opponent for pos in line):
                    return move

        # Prefer center if available
        if 12 in available_moves:
            return 12

        # Otherwise, random move
        return random.choice(available_moves)
