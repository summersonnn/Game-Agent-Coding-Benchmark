"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-5@preset/fp8-speedy
Run: 2
Generated: 2026-02-13 14:53:21
"""


import random
import time
import math

class TimeoutException(Exception):
    pass

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        self.triples = self._generate_triples()
        self.cell_triples = [[] for _ in range(25)]
        for idx, triple in enumerate(self.triples):
            for cell in triple:
                self.cell_triples[cell].append(idx)
        self.cell_value = [len(self.cell_triples[i]) for i in range(25)]

    def _generate_triples(self):
        triples = []
        # rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                triples.append((start, start+1, start+2))
        # columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                triples.append((start, start+5, start+10))
        # diagonals down-right
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                triples.append((start, start+6, start+12))
        # diagonals down-left
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                triples.append((start, start+4, start+8))
        return triples

    def _opponent(self, player):
        return self.opponent_symbol if player == self.symbol else self.symbol

    def _is_winner(self, board, player):
        for a, b, c in self.triples:
            if board[a] == board[b] == board[c] == player:
                return True
        return False

    def _is_draw(self, board):
        return ' ' not in board

    def _evaluate(self, board, player):
        opponent = self._opponent(player)
        score = 0
        for a, b, c in self.triples:
            cells = (board[a], board[b], board[c])
            my = cells.count(player)
            opp = cells.count(opponent)
            if my > 0 and opp > 0:
                continue
            if my > 0:
                if my == 1:
                    score += 1
                else:   # my == 2
                    score += 100
            elif opp > 0:
                if opp == 1:
                    score -= 1
                else:
                    score -= 100
        return score

    def _get_ordered_moves(self, board, player):
        opponent = self._opponent(player)
        empty = [i for i, v in enumerate(board) if v == ' ']

        # find opponent's immediate winning cells
        opp_winning = set()
        for cell in empty:
            for t_idx in self.cell_triples[cell]:
                a, b, c = self.triples[t_idx]
                marks = (board[a], board[b], board[c])
                if marks.count(opponent) == 2 and marks.count(' ') == 1:
                    opp_winning.add(cell)
                    break

        winning, blocking, other = [], [], []
        for cell in empty:
            # check if this move wins for player
            win = False
            for t_idx in self.cell_triples[cell]:
                a, b, c = self.triples[t_idx]
                marks = (board[a], board[b], board[c])
                if marks.count(player) == 2 and marks.count(' ') == 1:
                    win = True
                    break
            if win:
                winning.append(cell)
            elif cell in opp_winning:
                blocking.append(cell)
            else:
                other.append(cell)

        other.sort(key=lambda c: -self.cell_value[c])
        return winning + blocking + other

    def make_move(self, board):
        empty = [i for i, v in enumerate(board) if v == ' ']
        if not empty:
            return None

        # 1. immediate win
        for cell in empty:
            for t_idx in self.cell_triples[cell]:
                a, b, c = self.triples[t_idx]
                marks = (board[a], board[b], board[c])
                if marks.count(self.symbol) == 2 and marks.count(' ') == 1:
                    return cell

        # 2. opponent threats
        opp_winning = set()
        for cell in empty:
            for t_idx in self.cell_triples[cell]:
                a, b, c = self.triples[t_idx]
                marks = (board[a], board[b], board[c])
                if marks.count(self.opponent_symbol) == 2 and marks.count(' ') == 1:
                    opp_winning.add(cell)
                    break
        if len(opp_winning) == 1:
            return next(iter(opp_winning))
        if len(opp_winning) >= 2:
            return random.choice(empty)   # forced loss, any move

        # 3. iterative deepening search
        start_time = time.time()
        time_limit = 0.9
        best_move = empty[0]   # fallback

        for depth in range(1, 26):
            if time.time() - start_time > time_limit:
                break
            try:
                _, move = self._negamax_root(board, depth, start_time, time_limit)
                if move is not None:
                    best_move = move
            except TimeoutException:
                break
        return best_move

    def _negamax_root(self, board, depth, start_time, time_limit):
        player = self.symbol
        alpha = -math.inf
        beta = math.inf
        best_score = -math.inf
        best_move = None

        moves = self._get_ordered_moves(board, player)
        for move in moves:
            if time.time() - start_time > time_limit:
                raise TimeoutException
            board[move] = player
            score = -self._negamax(board, depth-1, -beta, -alpha,
                                   self._opponent(player), start_time, time_limit)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best_score, best_move

    def _negamax(self, board, depth, alpha, beta, player, start_time, time_limit):
        if time.time() - start_time > time_limit:
            raise TimeoutException

        # terminal
        if self._is_winner(board, self._opponent(player)):
            empty = board.count(' ')
            return - (1000000 + empty)
        if self._is_draw(board):
            return 0

        if depth == 0:
            return self._evaluate(board, player)

        best = -math.inf
        moves = self._get_ordered_moves(board, player)
        for move in moves:
            board[move] = player
            score = -self._negamax(board, depth-1, -beta, -alpha,
                                   self._opponent(player), start_time, time_limit)
            board[move] = ' '
            if score > best:
                best = score
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best