"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5.2-codex
Run: 1
Generated: 2026-02-11 21:23:16
"""



class TicTacToeAgent:
    WIN_LINES = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    )
    CORNERS = (0, 2, 6, 8)
    EDGES = (1, 3, 5, 7)

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.memo = {}

    def make_move(self, board):
        board = list(board)
        available = [i for i, s in enumerate(board) if s == ' ']
        if not available:
            return 0
        _, move = self._minimax(board, self.symbol)
        if move is None or move not in available:
            return self._prefer_move(available)
        return move

    def _check_winner(self, board):
        for a, b, c in self.WIN_LINES:
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _minimax(self, board, player):
        key = (tuple(board), player)
        if key in self.memo:
            return self.memo[key]

        winner = self._check_winner(board)
        if winner is not None:
            if winner == self.symbol:
                score = 10 + board.count(' ')
            elif winner == self.opponent:
                score = -10 - board.count(' ')
            else:
                score = 0
            self.memo[key] = (score, None)
            return score, None

        moves = [i for i, s in enumerate(board) if s == ' ']

        if player == self.symbol:
            best_score = -float('inf')
            best_moves = []
            for move in moves:
                board[move] = player
                score, _ = self._minimax(board, self.opponent)
                board[move] = ' '
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            best_move = self._prefer_move(best_moves)
        else:
            best_score = float('inf')
            best_moves = []
            for move in moves:
                board[move] = player
                score, _ = self._minimax(board, self.symbol)
                board[move] = ' '
                if score < best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            best_move = self._prefer_move(best_moves)

        self.memo[key] = (best_score, best_move)
        return best_score, best_move

    def _prefer_move(self, moves):
        if not moves:
            return None
        if 4 in moves:
            return 4
        corners = [m for m in moves if m in self.CORNERS]
        if corners:
            return random.choice(corners)
        edges = [m for m in moves if m in self.EDGES]
        if edges:
            return random.choice(edges)
        return random.choice(moves)
