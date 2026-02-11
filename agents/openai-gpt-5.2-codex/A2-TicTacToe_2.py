"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5.2-codex
Run: 2
Generated: 2026-02-11 21:05:13
"""



class TicTacToeAgent:
    WIN_COMBOS = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
        (0, 4, 8), (2, 4, 6)              # Diagonals
    )
    PREF_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
    EMPTY = ' '

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self._memo = {}

    def make_move(self, board):
        available = [i for i, v in enumerate(board) if v == self.EMPTY]
        if not available:
            return None

        best_score = -float('inf')
        best_moves = []
        for move in available:
            board[move] = self.symbol
            score = self._minimax(board, self.opponent)
            board[move] = self.EMPTY
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return self._choose_preferred(best_moves)

    def _choose_preferred(self, moves):
        if len(moves) == 1:
            return moves[0]
        move_set = set(moves)
        for pref in self.PREF_ORDER:
            if pref in move_set:
                return pref
        return moves[0]

    def _minimax(self, board, current):
        key = (tuple(board), current)
        if key in self._memo:
            return self._memo[key]

        winner = self._check_winner(board)
        if winner is not None:
            if winner == 'DRAW':
                score = 0
            elif winner == self.symbol:
                score = 1000 + board.count(self.EMPTY)
            else:
                score = -1000 - board.count(self.EMPTY)
            self._memo[key] = score
            return score

        available = [i for i, v in enumerate(board) if v == self.EMPTY]

        if current == self.symbol:
            best = -float('inf')
            for move in available:
                board[move] = current
                score = self._minimax(board, self.opponent)
                board[move] = self.EMPTY
                if score > best:
                    best = score
        else:
            best = float('inf')
            for move in available:
                board[move] = current
                score = self._minimax(board, self.symbol)
                board[move] = self.EMPTY
                if score < best:
                    best = score

        self._memo[key] = best
        return best

    def _check_winner(self, board):
        for a, b, c in self.WIN_COMBOS:
            if board[a] != self.EMPTY and board[a] == board[b] == board[c]:
                return board[a]
        if self.EMPTY not in board:
            return 'DRAW'
        return None
