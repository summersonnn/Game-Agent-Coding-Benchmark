"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-13 14:53:21
"""

import random
import time
import math

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.flip = lambda p: 'O' if p == 'X' else 'X'
        self.win_conditions = []
        for r in range(5):
            for c in range(3):
                self.win_conditions.append((r*5 + c, r*5 + c + 1, r*5 + c + 2))
        for c in range(5):
            for r in range(3):
                self.win_conditions.append((r*5 + c, (r+1)*5 + c, (r+2)*5 + c))
        for r in range(3):
            for c in range(3):
                self.win_conditions.append((r*5 + c, (r+1)*5 + c + 1, (r+2)*5 + c + 2))
        for r in range(3):
            for c in range(2, 5):
                self.win_conditions.append((r*5 + c, (r+1)*5 + c - 1, (r+2)*5 + c - 2))

    def _get_winner(self, board):
        for a, b, c in self.win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        return None

    def get_score(self, term, empty):
        if term == 'DRAW':
            return 0
        bonus = empty / 25.0 * 0.1
        if term == self.symbol:
            return 1 + bonus
        else:
            return -1 - bonus

    def build_board_and_player(self, original_board, node):
        sim_board = original_board[:]
        path = []
        temp = node
        while temp.parent:
            path.append(temp.move)
            temp = temp.parent
        path.reverse()
        current_player = self.symbol
        for move in path:
            sim_board[move] = current_player
            current_player = self.flip(current_player)
        return sim_board, current_player

    def simulate(self, sim_board, sim_player):
        board = sim_board[:]
        player = sim_player
        while True:
            winner = self._get_winner(board)
            if winner:
                return self.get_score(winner, board.count(' '))
            if ' ' not in board:
                return self.get_score('DRAW', 0)
            available = [i for i in range(25) if board[i] == ' ']
            move = random.choice(available)
            board[move] = player
            player = self.flip(player)

    def uct_select(self, node):
        log_n = math.log(node.visits)
        best_score = -float('inf')
        best_child = None
        for child in node.children:
            uct = child.score / child.visits + 1.4142135623730951 * math.sqrt(log_n / child.visits)
            if uct > best_score:
                best_score = uct
                best_child = child
        return best_child

    def make_move(self, board):
        available = [i for i in range(25) if board[i] == ' ']
        if not available:
            return None
        if len(available) == 1:
            return available[0]

        class Node:
            def __init__(self, parent=None, move=None):
                self.parent = parent
                self.move = move
                self.children = []
                self.visits = 0
                self.score = 0.0
                self.untried_moves = []

        root = Node()
        dist = lambda p: abs(divmod(p, 5)[0] - 2) + abs(divmod(p, 5)[1] - 2)
        available.sort(key=lambda p: -dist(p))
        root.untried_moves = available[:]
        start_time = time.time()
        timeout = 0.9
        while time.time() - start_time < timeout:
            node = root
            while node.untried_moves == [] and node.children:
                node = self.uct_select(node)
            if node.untried_moves:
                move = node.untried_moves.pop()
                child = Node(parent=node, move=move)
                node.children.append(child)
                sim_board, _ = self.build_board_and_player(board, child)
                child_available = [i for i in range(25) if sim_board[i] == ' ']
                child_available.sort(key=lambda p: -dist(p))
                child.untried_moves = child_available
                node = child
            sim_board, sim_player = self.build_board_and_player(board, node)
            score = self.simulate(sim_board, sim_player)
            temp = node
            while temp:
                temp.visits += 1
                temp.score += score
                temp = temp.parent
        best_child = max(root.children, key=lambda c: c.score / c.visits if c.visits > 0 else 0)
        return best_child.move