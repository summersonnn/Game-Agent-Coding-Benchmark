"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-flash-preview
Run: 2
Generated: 2026-02-13 14:53:21
"""



class TicTacToeAgent:
    """
    An advanced Tic Tac Toe agent for a 5x5 grid with a 3-in-a-row win condition.
    Uses Minimax with Alpha-Beta pruning and a heuristic evaluation function.
    """

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_combos = self._get_win_combos()
        self.cell_to_combos = self._get_cell_to_combos()

    def _get_win_combos(self):
        """Pre-calculates all possible 3-in-a-row winning combinations on a 5x5 grid."""
        combos = []
        # Rows
        for r in range(5):
            for c in range(3):
                combos.append((r * 5 + c, r * 5 + c + 1, r * 5 + c + 2))
        # Columns
        for c in range(5):
            for r in range(3):
                combos.append((r * 5 + c, (r + 1) * 5 + c, (r + 2) * 5 + c))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                combos.append((r * 5 + c, (r + 1) * 5 + c + 1, (r + 2) * 5 + c + 2))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                combos.append((r * 5 + c, (r + 1) * 5 + c - 1, (r + 2) * 5 + c - 2))
        return combos

    def _get_cell_to_combos(self):
        """Maps each cell index to the winning combinations it belongs to."""
        cell_to_combos = [[] for _ in range(25)]
        for combo in self.win_combos:
            for cell in combo:
                cell_to_combos[cell].append(combo)
        return cell_to_combos

    def _check_win_at(self, board, player, last_move):
        """Checks if the last move made resulted in a win for the player."""
        for c1, c2, c3 in self.cell_to_combos[last_move]:
            if board[c1] == player and board[c2] == player and board[c3] == player:
                return True
        return False
