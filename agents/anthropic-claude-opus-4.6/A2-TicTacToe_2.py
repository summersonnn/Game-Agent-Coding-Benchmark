"""
Agent Code: A2-TicTacToe
Model: anthropic-claude-opus-4.6
Run: 2
Generated: 2026-02-13 14:53:21
"""


class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'

        self.win_lines = []
        for r in range(5):
            for c in range(3):
                s = r * 5 + c
                self.win_lines.append((s, s + 1, s + 2))
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                self.win_lines.append((s, s + 5, s + 10))
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                self.win_lines.append((s, s + 6, s + 12))
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                self.win_lines.append((s, s + 4, s + 8))

        self.cell_lines = [[] for _ in range(25)]
        for i, line in enumerate(self.win_lines):
            for cell in line:
                self.cell_lines[cell].append(i)

        self.center_dist = []
        for i in range(25):
            r, c = divmod(i, 5)
            self.center_dist.append(abs(r - 2) + abs(c - 2))

    def make_move(self, board):
        empty = [i for i in range(25) if board[i] == ' ']
        if not empty:
            return 0

        win = self._find_winning_move(board, self.symbol, empty)
        if win is not None:
            return win

        block = self._find_winning_move(board, self.opponent, empty)
        if block is not None:
            return block

        fork = self._find_fork_move(board, self.symbol, empty)
        if fork is not None:
            return fork

        block_fork = self._find_fork_move(board, self.opponent, empty)
        if block_fork is not None:
            return block_fork

        n = len(empty)
        if n > 20:
            depth = 5
        elif n > 16:
            depth = 6
        elif n > 12:
            depth = 7
        elif n > 8:
            depth = 10
        else:
            depth = 14

        moves = sorted(empty, key=lambda m: (-self._move_score(board, m, self.symbol), self.center_dist[m]))

        best_score = float('-inf')
        best_move = moves[0]
        alpha = float('-inf')

        for move in moves:
            board[move] = self.symbol
            score = self._minimax(board, depth - 1, False, alpha, float('inf'))
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        return best_move

    def _find_winning_move(self, board, symbol, empty):
        for move in empty:
            for li in self.cell_lines[move]:
                a, b, c = self.win_lines[li]
                vals = [board[a], board[b], board[c]]
                if vals.count(symbol) == 2 and vals.count(' ') == 1:
                    idx = [a, b, c][vals.index(' ')]
                    if idx == move:
                        return move
        return None

    def _find_fork_move(self, board, symbol, empty):
        best = None
        best_threats = 0
        for move in empty:
            board[move] = symbol
            threats = 0
            for li in self.cell_lines[move]:
                a, b, c = self.win_lines[li]
                vals = [board[a], board[b], board[c]]
                if vals.count(symbol) == 2 and vals.count(' ') == 1:
                    threats += 1
            board[move] = ' '
            if threats >= 2 and threats > best_threats:
                best_threats = threats
                best = move
        return best

    def _move_score(self, board, move, symbol):
        score = 0
        for li in self.cell_lines[move]:
            a, b, c = self.win_lines[li]
            my = 0
            opp = 0
            for cell in (a, b, c):
                if board[cell] == symbol:
                    my += 1
                elif board[cell] != ' ':
                    opp += 1
            if opp == 0:
                score += my * 3 + 1
            if my == 0 and opp > 0:
                score += opp
        return score

    def _minimax(self, board, depth, is_max, alpha, beta):
        winner = self._check_winner_fast(board)
        if winner:
            return (1000 + depth) if winner == self.symbol else (-1000 - depth)

        empty = [i for i in range(25) if board[i] == ' ']
        if not empty:
            return 0
        if depth == 0:
            return self._evaluate(board)

        if depth >= 3:
            sym = self.symbol if is_max else self.opponent
            moves = sorted(empty, key=lambda m: (-self._move_score(board, m, sym), self.center_dist[m]))
        else:
            moves = empty

        if is_max:
            best = float('-inf')
            for move in moves:
                board[move] = self.symbol
                score = self._minimax(board, depth - 1, False, alpha, beta)
                board[move] = ' '
                best = max(best, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return best
        else:
            best = float('inf')
            for move in moves:
                board[move] = self.opponent
                score = self._minimax(board, depth - 1, True, alpha, beta)
                board[move] = ' '
                best = min(best, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return best

    def _check_winner_fast(self, board):
        for a, b, c in self.win_lines:
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        return None

    def _evaluate(self, board):
        score = 0
        for a, b, c in self.win_lines:
            va, vb, vc = board[a], board[b], board[c]
            my = (va == self.symbol) + (vb == self.symbol) + (vc == self.symbol)
            opp = (va == self.opponent) + (vb == self.opponent) + (vc == self.opponent)
            if opp == 0:
                if my == 2:
                    score += 15
                elif my == 1:
                    score += 2
            elif my == 0:
                if opp == 2:
                    score -= 15
                elif opp == 1:
                    score -= 2
        return score