"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def _check_winner(self, board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6),              # Diagonals
        ]
        for combo in win_conditions:
            a, b, c = combo
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _minimax(self, board, alpha, beta, cache):
        board_tuple = tuple(board)
        if board_tuple in cache:
            return cache[board_tuple]
        
        winner = self._check_winner(board)
        if winner is not None:
            if winner == 'DRAW':
                score = 0
            else:
                empty_count = board.count(' ')
                T = max(empty_count, 3)
                if winner == self.symbol:
                    score = T
                else:
                    score = -T
            cache[board_tuple] = score
            return score

        moves_made = 9 - board.count(' ')
        current_player = 'X' if moves_made % 2 == 0 else 'O'
        is_our_turn = (current_player == self.symbol)

        if is_our_turn:
            best_score = -float('inf')
            for move in range(9):
                if board[move] == ' ':
                    new_board = board.copy()
                    new
