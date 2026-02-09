"""
Agent Code: A8-SurroundMorris
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-09 19:05:17
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opp_color = 'W' if color == 'B' else 'B'
        self.ADJACENCY = {
            0: [1, 9], 1: [0, 2, 4], 2: [1, 14],
            3: [4, 10], 4: [1, 3, 5, 7], 5: [4, 13],
            6: [7, 11], 7: [4, 6, 8], 8: [7, 12],
            9: [0, 10, 21], 10: [3, 9, 11, 18], 11: [6, 10, 15],
            12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
            15: [11, 16], 16: [15, 17, 19], 17: [12, 16],
            18: [10, 19], 19: [16, 18, 20, 22], 20: [13, 19],
            21: [9, 22], 22: [19, 21, 23], 23: [14, 22],
        }

    def is_captured(self, spot, board):
        color = board[spot]
        if color == '':
            return False
        neighbors = self.ADJACENCY[spot]
        empty = 0
        friendly = 0
        opponent = 0
        opp = 'W' if color == 'B' else 'B'
        for n in neighbors:
            b = board[n]
            if b == '':
                empty += 1
            elif b == color:
                friendly += 1
            else:
                opponent += 1
        return empty == 0 and opponent > friendly

    def apply_move(self, state, move):
        new_state = {}
        for k in state:
            if k == 'board':
                new_state[k] = state[k].copy()
            elif k == 'history':
                new_state[k] = state[k].copy()
            elif k == 'pieces_in_hand' or k == 'pieces_on_board':
                new_state[k] = state[k].copy()
            else:
                new_state[k] = state[k]
        phase = new_state['phase']
        color = new_state['current_player']
        opp = 'W' if color == 'B' else 'B'
        board = new_state['board']
        if phase == 'placement':
            spot = move
            if board[spot] != '' or spot < 0 or spot > 23:
                return None
            board[spot] = color
            new_state['pieces_in_hand'][color] -= 1
            if self.is_captured(spot, board):
                board[spot] = ''
            else:
                to_remove = [s for s in range(24) if board[s] == color and self.is_captured(s, board)]
                for s in to_remove:
                    board[s] = ''
                to_remove = [s for s in range(24) if board[s] == opp and self.is_captured(s, board)]
                for s in to_remove:
                    board[s] = ''
        else:
            from_sp, to_sp = move
            if board[from_sp] != color or board[to_sp] != '' or to_sp not in self.ADJACENCY[from_sp]:
                return None
            board[to_sp] = color
            board[from_sp] = ''
            if self.is_captured(to_sp, board):
                board[to_sp] = ''
            else:
                to_remove = [s for s in range(24) if board[s] == color and self.is_captured(s, board)]
                for s in to_remove:
                    board[s] = ''
                to_remove = [s for s in range(24) if board[s] == opp and self.is_captured(s, board)]
                for s in to_remove:
                    board[s] = ''
            new_state['move_count'] += 1
        pob = {'B': 0, 'W': 0}
        for i in range(24):
            c = board[i]
            if c == 'B':
                pob['B'] += 1
            elif c == 'W':
                pob['W'] += 1
        new_state['pieces_on_board'] = pob
        if phase == 'placement' and new_state['pieces_in_hand']['B'] == 0 and new_state['pieces_in_hand']['W'] == 0:
            new_state['phase'] = 'movement'
            new_state['history'] = []
        new_state['current_player'] = opp
        return new_state

    def get_legal_moves(self, state):
        phase = state['phase']
        color = state['current_player']
        board = state['board']
        if phase == 'placement':
            return [i for i in range(24) if board[i] == '']
        else:
            moves = []
            for s in range(24):
                if board[s] == color:
                    for n in self.ADJACENCY[s]:
                        if board[n] == '':
                            moves.append((s, n))
            return moves

    def evaluate(self, state):
        my_p = state['pieces_on_board'][self.color] + state['pieces_in_hand'][self.color]
        opp_p = state['pieces_on_board'][self.opp_color] + state['pieces_in_hand'][self.opp_color]
        return my_p - opp_p

    def minimax(self, state, depth, alpha, beta, maximizing):
        if depth == 0:
            return self.evaluate(state)
        color = state['current_player']
        opp = 'W' if color == 'B' else 'B'
        pob = state['pieces_on_board']
        pih = state['pieces_in_hand']
        phase = state['phase']
        if pob[color] == 0 and (phase == 'movement' or pih[color] == 0):
            winner = opp
            if winner == self.color:
                return pob[opp]
            else:
                return 0
        legal_moves = self.get_legal_moves(state)
        if phase == 'movement' and not legal_moves:
            winner = opp
            if winner == self.color:
                return 7
            else:
                return -7
        if maximizing:
            max_eval = -float('inf')
            for move in legal_moves:
                new_state = self.apply_move(state, move)
                if new_state is None:
                    continue
                eval = self.minimax(new_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, max_eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_state = self.apply_move(state, move)
                if new_state is None:
                    continue
                eval = self.minimax(new_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, min_eval)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, state: dict, feedback: dict | None = None):
        phase = state["phase"]
        board = state["board"]
        legal = []
        if phase == "placement":
            legal = [i for i in range(24) if board[i] == '']
        else:
            for spot in range(24):
                if board[spot] == self.color:
                    for n in self.ADJACENCY[spot]:
                        if board[n] == '':
                            legal.append((spot, n))
        if not legal:
            return 0 if phase == "placement" else (0, 1)
        best_value = -float('inf')
        best_moves = []
        for move in legal:
            new_state = self.apply_move(state, move)
            if new_state is None:
                continue
            value = self.minimax(new_state, 3, -float('inf'), float('inf'), False)
            if value > best_value:
                best_value = value
                best_moves = [move]
            elif value == best_value:
                best_moves.append(move)
        return random.choice(best_moves)
