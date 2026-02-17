"""
Agent Code: A2-TicTacToe
Model: anthropic-claude-opus-4.6
Run: 2
Generated: 2026-02-13 14:53:21
"""


import time

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'

        self.lines = []
        for r in range(5):
            for c in range(3):
                s = r * 5 + c
                self.lines.append((s, s + 1, s + 2))
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                self.lines.append((s, s + 5, s + 10))
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                self.lines.append((s, s + 6, s + 12))
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                self.lines.append((s, s + 4, s + 8))

        self.cell_lines = [[] for _ in range(25)]
        for i, line in enumerate(self.lines):
            for cell in line:
                self.cell_lines[cell].append(i)

        self.center_score = [0] * 25
        for i in range(25):
            r, c = divmod(i, 5)
            self.center_score[i] = max(0, 3 - abs(r - 2)) + max(0, 3 - abs(c - 2))

    def make_move(self, board):
        empty = [i for i in range(25) if board[i] == ' ']
        if not empty:
            return 0

        for move in empty:
            if self._is_winning_move(board, move, self.symbol):
                return move
        for move in empty:
            if self._is_winning_move(board, move, self.opponent):
                return move

        self.start_time = time.time()
        self.time_limit = 0.8
        self.timed_out = False
        self.tt = {}

        best_move = empty[0]
        for depth in range(1, 30):
            if self.timed_out:
                break
            move, score = self._search_root(board, empty, depth)
            if not self.timed_out:
                best_move = move
                if score >= 10000:
                    break
        return best_move

    def _is_winning_move(self, board, pos, symbol):
        for li in self.cell_lines[pos]:
            a, b, c = self.lines[li]
            count = 0
            for cell in (a, b, c):
                if cell == pos:
                    continue
                if board[cell] == symbol:
                    count += 1
                elif board[cell] != ' ':
                    count = -1
                    break
            if count == 2:
                return True
        return False

    def _search_root(self, board, empty, max_depth):
        best_score = -float('inf')
        best_move = empty[0]
        moves = self._order_moves(board, empty, self.symbol)

        for move in moves:
            if time.time() - self.start_time > self.time_limit:
                self.timed_out = True
                break
            board[move] = self.symbol
            score = -self._negamax(board, max_depth - 1, -float('inf'), -best_score, self.opponent)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        return best_move, best_score

    def _negamax(self, board, depth, alpha, beta, current):
        if time.time() - self.start_time > self.time_limit:
            self.timed_out = True
            return 0

        opp = self.opponent if current == self.symbol else self.symbol

        for line in self.lines:
            a, b, c = line
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return 10000 + depth if board[a] == current else -(10000 + depth)

        empty = [i for i in range(25) if board[i] == ' ']
        if not empty:
            return 0

        if depth <= 0:
            return self._evaluate(board, current, opp)

        board_key = (tuple(board), current)
        tt_entry = self.tt.get(board_key)
        if tt_entry and tt_entry[0] >= depth:
            flag, tt_score, tt_alpha, tt_beta = tt_entry[0], tt_entry[1], tt_entry[2], tt_entry[3]
            if tt_alpha <= alpha and beta <= tt_beta:
                return tt_score

        moves = self._order_moves(board, empty, current)
        best = -float('inf')
        for move in moves:
            if self.timed_out:
                return 0
            board[move] = current
            score = -self._negamax(board, depth - 1, -beta, -alpha, opp)
            board[move] = ' '
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if not self.timed_out:
            self.tt[board_key] = (depth, best, alpha, beta)

        return best

    def _evaluate(self, board, current, opp):
        score = 0
        for a, b, c in self.lines:
            cur = 0
            op = 0
            for cell in (a, b, c):
                v = board[cell]
                if v == current:
                    cur += 1
                elif v == opp:
                    op += 1
            if op == 0:
                if cur == 2:
                    score += 50
                elif cur == 1:
                    score += 5
            elif cur == 0:
                if op == 2:
                    score -= 50
                elif op == 1:
                    score -= 5

        if board[12] == current:
            score += 3
        elif board[12] == opp:
            score -= 3
        return score

    def _order_moves(self, board, empty, current):
        opp = self.opponent if current == self.symbol else self.symbol
        scored = []
        for move in empty:
            s = self.center_score[move]
            if self._is_winning_move(board, move, current):
                s += 10000
            elif self._is_winning_move(board, move, opp):
                s += 5000
            else:
                for li in self.cell_lines[move]:
                    a, b, c = self.lines[li]
                    cur = op = 0
                    for cell in (a, b, c):
                        if cell == move:
                            continue
                        if board[cell] == current:
                            cur += 1
                        elif board[cell] == opp:
                            op += 1
                    if op == 0 and cur == 1:
                        s += 8
                    elif cur == 0 and op == 1:
                        s += 6
            scored.append((-s, move))
        scored.sort()
        return [m for _, m in scored]