"""
Agent Code: A2-TicTacToe
Model: openai-gpt-5.2-codex
Run: 1
Generated: 2026-02-13 14:53:21
"""

import time


class TicTacToeAgent:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.opp = 'O' if symbol == 'X' else 'X'
        self.empty = ' '
        self.size = 5
        self.win_lines = self._build_win_lines()
        self.lines_by_cell = [[] for _ in range(25)]
        for line in self.win_lines:
            for idx in line:
                self.lines_by_cell[idx].append(line)

    def _build_win_lines(self):
        lines = []
        # Rows (length 3 windows)
        for r in range(5):
            base = r * 5
            for c in range(3):
                s = base + c
                lines.append((s, s + 1, s + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                lines.append((s, s + 5, s + 10))
        # Diagonal down-right
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                lines.append((s, s + 6, s + 12))
        # Diagonal down-left
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                lines.append((s, s + 4, s + 8))
        return lines

    def _winner(self, board):
        for a, b, c in self.win_lines:
            v = board[a]
            if v != self.empty and v == board[b] and v == board[c]:
                return v
        if self.empty not in board:
            return 'DRAW'
        return None

    def _immediate_wins(self, board, symbol):
        moves = []
        for i, v in enumerate(board):
            if v == self.empty:
                board[i] = symbol
                if self._winner(board) == symbol:
                    moves.append(i)
                board[i] = self.empty
        return moves

    def _heuristic(self, board):
        winner = self._winner(board)
        if winner == self.symbol:
            return 100000 + board.count(self.empty)
        if winner == self.opp:
            return -100000 - board.count(self.empty)
        if winner == 'DRAW':
            return 0

        score = 0

        # Line pressure
        for a, b, c in self.win_lines:
            line = (board[a], board[b], board[c])
            myc = line.count(self.symbol)
            opc = line.count(self.opp)
            emp = 3 - myc - opc

            if myc and opc:
                continue  # blocked line
            if myc == 2 and emp == 1:
                score += 420
            elif myc == 1 and emp == 2:
                score += 36
            elif myc == 3:
                score += 12000

            if opc == 2 and emp == 1:
                score -= 520
            elif opc == 1 and emp == 2:
                score -= 42
            elif opc == 3:
                score -= 12000

        # Light center preference
        for i, v in enumerate(board):
            if v == self.empty:
                continue
            r, c = divmod(i, 5)
            center_weight = 4 - (abs(r - 2) + abs(c - 2))
            if v == self.symbol:
                score += center_weight * 2
            else:
                score -= center_weight * 2

        return score

    def _candidate_moves(self, board):
        empties = [i for i, v in enumerate(board) if v == self.empty]
        if not empties:
            return []

        occupied = [i for i, v in enumerate(board) if v != self.empty]
        if not occupied:
            return empties

        neighbors = set()
        for idx in occupied:
            r, c = divmod(idx, 5)
            for dr in (-1, 0, 1):
                nr = r + dr
                if nr < 0 or nr >= 5:
                    continue
                for dc in (-1, 0, 1):
                    nc = c + dc
                    if nc < 0 or nc >= 5:
                        continue
                    j = nr * 5 + nc
                    if board[j] == self.empty:
                        neighbors.add(j)

        if neighbors:
            return list(neighbors)
        return empties

    def _local_move_score(self, board, move, actor):
        # board already contains actor at move
        opponent = self.opp if actor == self.symbol else self.symbol
        score = 0
        r, c = divmod(move, 5)
        score += (4 - (abs(r - 2) + abs(c - 2))) * 3

        for a, b, c3 in self.lines_by_cell[move]:
            vals = (board[a], board[b], board[c3])
            ac = vals.count(actor)
            oc = vals.count(opponent)
            emp = 3 - ac - oc

            if ac and oc:
                continue
            if ac == 3:
                score += 5000
            elif ac == 2 and emp == 1:
                score += 320
            elif ac == 1 and emp == 2:
                score += 24

            if oc == 2 and emp == 1:
                score += 220

        return score

    def _ordered_moves(self, board, actor, branch_cap):
        moves = self._candidate_moves(board)
        scored = []
        for m in moves:
            board[m] = actor
            s = self._local_move_score(board, m, actor)
            board[m] = self.empty
            scored.append((s, m))
        scored.sort(reverse=True)
        if branch_cap and len(scored) > branch_cap:
            scored = scored[:branch_cap]
        return [m for _, m in scored]

    def _search(self, board, depth, alpha, beta, actor, deadline):
        if time.time() >= deadline:
            raise TimeoutError

        winner = self._winner(board)
        if winner is not None:
            if winner == self.symbol:
                return 100000 + board.count(self.empty)
            if winner == self.opp:
                return -100000 - board.count(self.empty)
            return 0

        if depth == 0:
            return self._heuristic(board)

        empties = board.count(self.empty)
        if empties > 16:
            branch_cap = 8
        elif empties > 11:
            branch_cap = 10
        else:
            branch_cap = 14

        moves = self._ordered_moves(board, actor, branch_cap)

        if actor == self.symbol:
            value = -10**9
            next_actor = self.opp
            for m in moves:
                board[m] = actor
                v = self._search(board, depth - 1, alpha, beta, next_actor, deadline)
                board[m] = self.empty
                if v > value:
                    value = v
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:
            value = 10**9
            next_actor = self.symbol
            for m in moves:
                board[m] = actor
                v = self._search(board, depth - 1, alpha, beta, next_actor, deadline)
                board[m] = self.empty
                if v < value:
                    value = v
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
            return value

    def make_move(self, board):
        available = [i for i, v in enumerate(board) if v == self.empty]
        if not available:
            return 0

        # 1) Win immediately if possible
        my_wins = self._immediate_wins(board, self.symbol)
        if my_wins:
            best = my_wins[0]
            best_s = -10**9
            for m in my_wins:
                board[m] = self.symbol
                s = self._local_move_score(board, m, self.symbol)
                board[m] = self.empty
                if s > best_s:
                    best_s = s
                    best = m
            return best

        # 2) Block opponent's immediate win
        opp_wins = self._immediate_wins(board, self.opp)
        if opp_wins:
            if len(opp_wins) == 1:
                return opp_wins[0]
            # Multiple threats: pick the block that gives best counterplay
            best = opp_wins[0]
            best_s = -10**9
            for m in opp_wins:
                board[m] = self.symbol
                s = self._heuristic(board)
                board[m] = self.empty
                if s > best_s:
                    best_s = s
                    best = m
            return best

        # 3) Iterative deepening alpha-beta under time budget
        best_move = random.choice(available)
        deadline = time.time() + 0.92

        empties = len(available)
        if empties > 18:
            max_depth = 3
        elif empties > 12:
            max_depth = 4
        elif empties > 8:
            max_depth = 5
        else:
            max_depth = 6

        try:
            for depth in range(1, max_depth + 1):
                if time.time() >= deadline:
                    break
                moves = self._ordered_moves(board, self.symbol, branch_cap=14 if empties <= 12 else 10)
                if not moves:
                    break

                best_val = -10**9
                current_best = moves[0]
                alpha, beta = -10**9, 10**9

                for m in moves:
                    if time.time() >= deadline:
                        raise TimeoutError
                    board[m] = self.symbol
                    v = self._search(board, depth - 1, alpha, beta, self.opp, deadline)
                    board[m] = self.empty

                    if v > best_val:
                        best_val = v
                        current_best = m
                    if best_val > alpha:
                        alpha = best_val

                best_move = current_best
        except TimeoutError:
            pass

        if best_move in available:
            return best_move
        return random.choice(available)