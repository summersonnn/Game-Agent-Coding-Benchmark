"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-opus-4.6
Run: 1
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    """
    Perfect Tic Tac Toe agent using minimax with alpha-beta pruning.
    Wins whenever possible, never loses, and prefers faster wins.
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
        available_moves = [i for i in range(9) if board[i] == ' ']
        if not available_moves:
            return None

        # Quick check: if only one move, take it
        if len(available_moves) == 1:
            return available_moves[0]

        # If board is empty, take center (optimal opening)
        if len(available_moves) == 9:
            return 4

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
                # Prefer winning with more empty cells (faster win)
                return 10 + board.count(' ')
            elif result == self.opponent:
                # Prefer losing with fewer empty cells (delay loss)
                return -10 - board.count(' ')
            else:
                return 0

        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval_score = self._minimax(board, False, alpha, beta)
                    board[i] = ' '
                    if eval_score > max_eval:
                        max_eval = eval_score
                    if max_eval > alpha:
                        alpha = max_eval
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
                    if eval_score < min_eval:
                        min_eval = eval_score
                    if min_eval < beta:
                        beta = min_eval
                    if beta <= alpha:
                        break
            return min_eval
