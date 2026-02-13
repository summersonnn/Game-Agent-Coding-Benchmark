"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-13 14:53:21
"""

import time

import random
import time

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_conditions = []
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 1, start + 2))
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 5, start + 10))
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 6, start + 12))
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_conditions.append((start, start + 4, start + 8))

    def check_winner(self, board):
        for a, b, c in self.win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if all(cell != ' ' for cell in board):
            return 'DRAW'
        return None

    def heuristic(self, board):
        return self.player_score(board, self.symbol) - self.player_score(board, self.opponent)

    def player_score(self, board, player):
        opp = self.opponent if player == self.symbol else self.symbol
        score = 0
        for combo in self.win_conditions:
            cells = [board[i] for i in combo]
            num_player = cells.count(player)
            num_opp = cells.count(opp)
            if num_opp > 0:
                continue
            if num_player == 2:
                score += 10
            elif num_player == 1:
                score += 1
        return score

    def minimax(self, board, is_maximizing, alpha, beta, current_depth, max_depth):
        winner = self.check_winner(board)
        if winner is not None:
            if winner == 'DRAW':
                return 0
            empty = sum(1 for c in board if c == ' ')
            base = max(empty, 3)
            if winner == self.symbol:
                return 1000 + base
            else:
                return -(1000 + base)
        if current_depth >= max_depth:
            return self.heuristic(board)
        moves = [i for i in range(25) if board[i] == ' ']
        if moves:
            current_player = self.symbol if is_maximizing else self.opponent
            move_scores = []
            for move in moves:
                board[move] = current_player
                sc = self.heuristic(board)
                board[move] = ' '
                move_scores.append((sc, move))
            if is_maximizing:
                move_scores.sort(key=lambda x: x[0], reverse=True)
            else:
                move_scores.sort(key=lambda x: x[0])
            moves = [m for _, m in move_scores]
        if is_maximizing:
            max_eval = -float('inf')
            for move in moves:
                board[move] = self.symbol
                eval_ = self.minimax(board, False, alpha, beta, current_depth + 1, max_depth)
                board[move] = ' '
                max_eval = max(max_eval, eval_)
                alpha = max(alpha, eval_)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                board[move] = self.opponent
                eval_ = self.minimax(board, True, alpha, beta, current_depth + 1, max_depth)
                board[move] = ' '
                min_eval = min(min_eval, eval_)
                beta = min(beta, eval_)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, board):
        start_time = time.time()
        moves = [i for i in range(25) if board[i] == ' ']
        if not moves:
            return None
        best_move = random.choice(moves)
        move_scores = []
        for m in moves:
            board[m] = self.symbol
            sc = self.heuristic(board)
            board[m] = ' '
            move_scores.append((sc, m))
        move_scores.sort(key=lambda x: x[0], reverse=True)
        ordered_moves = [m for _, m in move_scores]
        depth = 1
        while True:
            current_best_move = None
            best_score = -float('inf')
            for move in ordered_moves:
                board[move] = self.symbol
                score = self.minimax(board, False, -float('inf'), float('inf'), 1, depth)
                board[move] = ' '
                if score > best_score:
                    best_score = score
                    current_best_move = move
            if current_best_move is not None:
                best_move = current_best_move
            elapsed = time.time() - start_time
            if elapsed > 0.8 or depth > 20:
                break
            depth += 1
        return best_move
