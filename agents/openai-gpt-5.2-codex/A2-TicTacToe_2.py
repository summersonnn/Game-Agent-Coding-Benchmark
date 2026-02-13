"""
Agent Code: A2-TicTacToe
Model: openai-gpt-5.2-codex
Run: 2
Generated: 2026-02-13 14:53:21
"""

class TicTacToeAgent:
    _LINES = None
    _PREFERRED_OPENING_ORDER = [
        12, 6, 8, 16, 18, 7, 11, 13, 17, 2, 10, 14, 22, 1, 3, 5, 9, 15, 19, 21, 23, 0, 4, 20, 24
    ]
    _CELL_WEIGHTS = [
        1, 2, 3, 2, 1,
        2, 4, 5, 4, 2,
        3, 5, 6, 5, 3,
        2, 4, 5, 4, 2,
        1, 2, 3, 2, 1,
    ]

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.empty = ' '
        if TicTacToeAgent._LINES is None:
            TicTacToeAgent._LINES = self._build_lines()

    def make_move(self, board):
        available = [i for i, v in enumerate(board) if v == self.empty]
        if not available:
            return None
        if len(available) == 1:
            return available[0]

        # 1) Immediate win
        winning_moves = self._find_winning_moves(board, self.symbol, available)
        if winning_moves:
            return self._pick_best_tactical(board, winning_moves, self.symbol)

        # 2) Immediate block
        blocking_moves = self._find_winning_moves(board, self.opponent, available)
        if blocking_moves:
            return self._pick_best_tactical(board, blocking_moves, self.symbol)

        # 3) Create fork (two threats next turn)
        my_forks = self._find_fork_moves(board, self.symbol, available)
        if my_forks:
            return self._pick_best_tactical(board, my_forks, self.symbol)

        # 4) Prevent opponent fork
        opp_forks = self._find_fork_moves(board, self.opponent, available)
        if opp_forks:
            return self._pick_best_tactical(board, opp_forks, self.symbol)

        # 5) Alpha-beta search with move ordering and candidate pruning
        empties = len(available)
        if empties > 18:
            depth = 3
        elif empties > 12:
            depth = 4
        elif empties > 8:
            depth = 5
        else:
            depth = 6

        candidates = self._candidate_moves(board, available)
        candidates.sort(key=lambda m: self._move_order_score(board, m, self.symbol), reverse=True)

        best_score = float('-inf')
        best_moves = []

        alpha = float('-inf')
        beta = float('inf')

        for move in candidates:
            board[move] = self.symbol
            score = self._alphabeta(board, depth - 1, alpha, beta, self.opponent)
            board[move] = self.empty

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

            if score > alpha:
                alpha = score

        if best_moves:
            return random.choice(best_moves)

        return random.choice(available)

    def _build_lines(self):
        lines = []

        # Rows
        for r in range(5):
            base = r * 5
            for c in range(3):
                s = base + c
                lines.append((s, s + 1, s + 2))

        # Columns
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                lines.append((s, s + 5, s + 10))

        # Diagonals down-right
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                lines.append((s, s + 6, s + 12))

        # Diagonals down-left
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                lines.append((s, s + 4, s + 8))

        return lines

    def _check_winner(self, board):
        for a, b, c in TicTacToeAgent._LINES:
            mark = board[a]
            if mark != self.empty and mark == board[b] == board[c]:
                return mark
        if self.empty not in board:
            return 'DRAW'
        return None

    def _find_winning_moves(self, board, player, available):
        wins = []
        for m in available:
            board[m] = player
            if self._check_winner(board) == player:
                wins.append(m)
            board[m] = self.empty
        return wins

    def _find_fork_moves(self, board, player, available):
        forks = []
        for m in available:
            board[m] = player
            next_avail = [i for i, v in enumerate(board) if v == self.empty]
            wins_next = self._find_winning_moves(board, player, next_avail)
            board[m] = self.empty
            if len(wins_next) >= 2:
                forks.append(m)
        return forks

    def _pick_best_tactical(self, board, moves, player):
        best_val = float('-inf')
        best = []
        for m in moves:
            board[m] = player
            val = self._evaluate(board)
            board[m] = self.empty
            if val > best_val:
                best_val = val
                best = [m]
            elif val == best_val:
                best.append(m)
        return random.choice(best) if best else random.choice(moves)

    def _candidate_moves(self, board, available):
        occupied = [i for i, v in enumerate(board) if v != self.empty]
        if not occupied:
            return [m for m in TicTacToeAgent._PREFERRED_OPENING_ORDER if m in available]

        candidates = set()
        for idx in occupied:
            r, c = divmod(idx, 5)
            for dr in (-2, -1, 0, 1, 2):
                rr = r + dr
                if rr < 0 or rr > 4:
                    continue
                for dc in (-2, -1, 0, 1, 2):
                    cc = c + dc
                    if cc < 0 or cc > 4:
                        continue
                    j = rr * 5 + cc
                    if board[j] == self.empty:
                        candidates.add(j)

        if len(candidates) < 6:
            candidates = set(available)

        ordered = list(candidates)
        ordered.sort(key=lambda m: TicTacToeAgent._CELL_WEIGHTS[m], reverse=True)
        return ordered

    def _move_order_score(self, board, move, player):
        board[move] = player
        if self._check_winner(board) == player:
            score = 10_000_000
        else:
            score = self._evaluate(board)
        board[move] = self.empty

        if player == self.symbol:
            return score
        return -score

    def _alphabeta(self, board, depth, alpha, beta, player):
        winner = self._check_winner(board)
        if winner is not None:
            if winner == self.symbol:
                return 1_000_000 + board.count(self.empty)
            if winner == self.opponent:
                return -1_000_000 - board.count(self.empty)
            return 0

        if depth <= 0:
            return self._evaluate(board)

        available = [i for i, v in enumerate(board) if v == self.empty]
        moves = self._candidate_moves(board, available)
        moves.sort(key=lambda m: self._move_order_score(board, m, player), reverse=True)

        # Prune width deeper in tree for speed.
        if depth >= 4 and len(moves) > 10:
            moves = moves[:10]
        elif depth >= 2 and len(moves) > 14:
            moves = moves[:14]

        if player == self.symbol:
            value = float('-inf')
            for m in moves:
                board[m] = player
                value = max(value, self._alphabeta(board, depth - 1, alpha, beta, self.opponent))
                board[m] = self.empty
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            for m in moves:
                board[m] = player
                value = min(value, self._alphabeta(board, depth - 1, alpha, beta, self.symbol))
                board[m] = self.empty
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    def _evaluate(self, board):
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 1_000_000 + board.count(self.empty)
        if winner == self.opponent:
            return -1_000_000 - board.count(self.empty)
        if winner == 'DRAW':
            return 0

        score = 0

        # Positional pressure (center-heavy).
        for i, cell in enumerate(board):
            if cell == self.symbol:
                score += TicTacToeAgent._CELL_WEIGHTS[i]
            elif cell == self.opponent:
                score -= TicTacToeAgent._CELL_WEIGHTS[i]

        # Line potential.
        for a, b, c in TicTacToeAgent._LINES:
            line = (board[a], board[b], board[c])
            my_count = line.count(self.symbol)
            opp_count = line.count(self.opponent)
            empty_count = line.count(self.empty)

            if my_count and opp_count:
                continue

            if my_count == 2 and empty_count == 1:
                score += 130
            elif my_count == 1 and empty_count == 2:
                score += 14

            if opp_count == 2 and empty_count == 1:
                score -= 160
            elif opp_count == 1 and empty_count == 2:
                score -= 16

        return score