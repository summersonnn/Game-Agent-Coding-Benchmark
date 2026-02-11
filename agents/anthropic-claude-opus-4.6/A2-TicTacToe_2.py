"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-opus-4.6
Run: 2
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    """
    Perfect Tic Tac Toe agent using minimax with alpha-beta pruning.
    Never loses; wins whenever the opponent makes a suboptimal move.
    Prefers faster wins (more empty cells remaining) for tie-breaker scoring.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self._win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6),
        ]

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return 0

        best_score = -float('inf')
        best_move = available_moves[0]

        for move in available_moves:
            board[move] = self.symbol
            score = self._minimax(board, False, -float('inf'), float('inf'))
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _check_winner(self, board):
        for a, b, c in self._win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _minimax(self, board, is_maximizing, alpha, beta):
        result = self._check_winner(board)
        if result is not None:
            if result == self.symbol:
                return 10 + board.count(' ')   # prefer faster wins
            elif result == 'DRAW':
                return 0
            else:
                return -10 - board.count(' ')  # penalize faster losses more

        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval_score = self._minimax(board, False, alpha, beta)
                    board[i] = ' '
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    eval_score = self._minimax(board, True, alpha, beta)
                    board[i] = ' '
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            return min_eval
