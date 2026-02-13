"""
Agent Code: A2-TicTacToe
Model: anthropic-claude-opus-4.6
Run: 1
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
                self.win_lines.append((s, s+1, s+2))
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                self.win_lines.append((s, s+5, s+10))
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                self.win_lines.append((s, s+6, s+12))
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                self.win_lines.append((s, s+4, s+8))

    def make_move(self, board):
        available = [i for i, s in enumerate(board) if s == ' ']
        if not available:
            return 0
        if len(available) == 1:
            return available[0]

        for m in available:
            board[m] = self.symbol
            if self._wins(board, self.symbol):
                board[m] = ' '
                return m
            board[m] = ' '

        for m in available:
            board[m] = self.opponent
            if self._wins(board, self.opponent):
                board[m] = ' '
                return m
            board[m] = ' '

        n = len(available)
        depth = 4 if n > 20 else 5 if n > 16 else 6 if n > 12 else 8 if n > 8 else 14

        best_score = float('-inf')
        best_move = available[0]
        alpha = float('-inf')
        ordered = self._order_top(board, available)

        for move in ordered:
            board[move] = self.symbol
            score = self._minimax(board, depth - 1, False, alpha, float('inf'))
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        return best_move

    def _order_top(self, board, moves):
        scored = []
        for m in moves:
            r, c = divmod(m, 5)
            s = -(abs(r - 2) + abs(c - 2)) * 2
            board[m] = self.symbol
            for a, b, cc in self.win_lines:
                line = (board[a], board[b], board[cc])
                if line.count(self.symbol) == 2 and line.count(' ') == 1:
                    s += 5
            board[m] = ' '
            scored.append((-s, m))
        scored.sort()
        return [m for _, m in scored]

    def _minimax(self, board, depth, is_max, alpha, beta):
        if self._wins(board, self.symbol):
            return 1000 + depth
        if self._wins(board, self.opponent):
            return -1000 - depth

        available = [i for i, s in enumerate(board) if s == ' ']
        if not available or depth == 0:
            return self._evaluate(board)

        available.sort(key=lambda m: abs(m // 5 - 2) + abs(m % 5 - 2))

        if is_max:
            best = float('-inf')
            for move in available:
                board[move] = self.symbol
                val = self._minimax(board, depth - 1, False, alpha, beta)
                board[move] = ' '
                if val > best:
                    best = val
                if val > alpha:
                    alpha = val
                if beta <= alpha:
                    break
            return best
        else:
            best = float('inf')
            for move in available:
                board[move] = self.opponent
                val = self._minimax(board, depth - 1, True, alpha, beta)
                board[move] = ' '
                if val < best:
                    best = val
                if val < beta:
                    beta = val
                if beta <= alpha:
                    break
            return best

    def _wins(self, board, symbol):
        for a, b, c in self.win_lines:
            if board[a] == board[b] == board[c] == symbol:
                return True
        return False

    def _evaluate(self, board):
        score = 0
        my_threats = 0
        opp_threats = 0
        for a, b, c in self.win_lines:
            ba, bb, bc = board[a], board[b], board[c]
            my = (ba == self.symbol) + (bb == self.symbol) + (bc == self.symbol)
            opp = (ba == self.opponent) + (bb == self.opponent) + (bc == self.opponent)
            if opp == 0:
                if my == 2:
                    score += 10
                    my_threats += 1
                elif my == 1:
                    score += 1
            if my == 0:
                if opp == 2:
                    score -= 10
                    opp_threats += 1
                elif opp == 1:
                    score -= 1
        if my_threats >= 2:
            score += 50
        if opp_threats >= 2:
            score -= 50
        return score