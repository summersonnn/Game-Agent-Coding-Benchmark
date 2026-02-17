"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5.2-codex
Run: 2
Generated: 2026-02-17 13:30:08
"""



class TicTacToeAgent:
    EMPTY = ' '
    LINE_SCORE = (0, 2, 20, 1000)
    WIN_VALUE = 100000
    WIN_LINES = None
    CELL_WEIGHTS = None
    MOVE_ORDER = None

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        cls = self.__class__
        if cls.WIN_LINES is None:
            cls._init_class_vars()

    @classmethod
    def _init_class_vars(cls):
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))
        cls.WIN_LINES = tuple(lines)

        weights = [0] * 25
        for a, b, c in lines:
            weights[a] += 1
            weights[b] += 1
            weights[c] += 1
        cls.CELL_WEIGHTS = weights
        cls.MOVE_ORDER = sorted(range(25), key=lambda i: weights[i], reverse=True)

    def _get_winner(self, board):
        for a, b, c in self.WIN_LINES:
            s = board[a]
            if s != self.EMPTY and s == board[b] == board[c]:
                return s
        return None

    def _evaluate(self, board):
        score = 0
        sym = self.symbol
        opp = self.opponent
        ls = self.LINE_SCORE
        for a, b, c in self.WIN_LINES:
            s1 = board[a]
            s2 = board[b]
            s3 = board[c]
            count_sym = (s1 == sym) + (s2 == sym) + (s3 == sym)
            count_opp = (s1 == opp) + (s2 == opp) + (s3 == opp)
            if count_sym and count_opp:
                continue
            if count_sym:
                score += ls[count_sym]
            elif count_opp:
                score -= ls[count_opp]

        weights = self.CELL_WEIGHTS
        for idx, cell in enumerate(board):
            if cell == sym:
                score += weights[idx]
            elif cell == opp:
                score -= weights[idx]
        return score

    def _minimax(self, board, depth, alpha, beta, maximizing):
        winner = self._get_winner(board)
        if winner == self.symbol:
            return self.WIN_VALUE + depth
        if winner == self.opponent:
            return -self.WIN_VALUE - depth
        if depth == 0:
            return self._evaluate(board)

        moves = [i for i in self.MOVE_ORDER if board[i] == self.EMPTY]
        if not moves:
            return 0

        if maximizing:
            value = -float('inf')
            for move in moves:
                board[move] = self.symbol
                score = self._minimax(board, depth - 1, alpha, beta, False)
                board[move] = self.EMPTY
                if score > value:
                    value = score
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for move in moves:
                board[move] = self.opponent
                score = self._minimax(board, depth - 1, alpha, beta, True)
                board[move] = self.EMPTY
                if score < value:
                    value = score
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
            return value

    def make_move(self, board):
        empty = [i for i, cell in enumerate(board) if cell == self.EMPTY]
        if not empty:
            return None

        # Immediate win
        for move in empty:
            board[move] = self.symbol
            if self._get_winner(board) == self.symbol:
                board[move] = self.EMPTY
                return move
            board[move] = self.EMPTY

        # Immediate block
        block_moves = []
        for move in empty:
            board[move] = self.opponent
            if self._get_winner(board) == self.opponent:
                block_moves.append(move)
            board[move] = self.EMPTY

        # Determine search depth
        n = len(empty)
        if n <= 6:
            depth = n
        elif n <= 10:
            depth = 5
        elif n <= 14:
            depth = 4
        else:
            depth = 3

        if block_moves:
            candidate_moves = sorted(block_moves, key=lambda i: self.CELL_WEIGHTS[i], reverse=True)
        else:
            candidate_moves = [i for i in self.MOVE_ORDER if board[i] == self.EMPTY]

        if not candidate_moves:
            return empty[0]

        best_move = candidate_moves[0]
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        for move in candidate_moves:
            board[move] = self.symbol
            score = self._minimax(board, depth - 1, alpha, beta, False)
            board[move] = self.EMPTY
            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score

        return best_move
