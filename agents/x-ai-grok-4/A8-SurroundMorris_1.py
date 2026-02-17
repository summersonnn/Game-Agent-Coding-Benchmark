"""
Agent Code: A8-SurroundMorris
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-10 22:38:58
"""


import random

ADJACENCY = {
    0: [1, 9],       1: [0, 2, 4],     2: [1, 14],
    3: [4, 10],      4: [1, 3, 5, 7],  5: [4, 13],
    6: [7, 11],      7: [4, 6, 8],     8: [7, 12],
    9: [0, 10, 21],  10: [3, 9, 11, 18], 11: [6, 10, 15],
    12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
    15: [11, 16],    16: [15, 17, 19],  17: [12, 16],
    18: [10, 19],    19: [16, 18, 20, 22], 20: [13, 19],
    21: [9, 22],     22: [19, 21, 23],  23: [14, 22],
}

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def is_captured(self, spot, board):
        if board[spot] == '':
            return False
        color = board[spot]
        opp = 'W' if color == 'B' else 'B'
        neighbors = ADJACENCY[spot]
        empty = sum(1 for n in neighbors if board[n] == '')
        friendly = sum(1 for n in neighbors if board[n] == color)
        opponent = len(neighbors) - empty - friendly
        return empty == 0 and opponent > friendly

    def apply_captures(self, board, active_color, active_spot):
        new_board = board[:]
        if self.is_captured(active_spot, new_board):
            new_board[active_spot] = ''
            return new_board
        friendly_captured = [s for s in range(24) if new_board[s] == active_color and self.is_captured(s, new_board)]
        for s in friendly_captured:
            new_board[s] = ''
        opp_color = 'W' if active_color == 'B' else 'B'
        opp_captured = [s for s in range(24) if new_board[s] == opp_color and self.is_captured(s, new_board)]
        for s in opp_captured:
            new_board[s] = ''
        return new_board

    def get_legal_placements(self, board):
        return [i for i in range(24) if board[i] == '']

    def get_legal_movements(self, board, color):
        moves = []
        for spot in range(24):
            if board[spot] == color:
                for n in ADJACENCY[spot]:
                    if board[n] == '':
                        moves.append((spot, n))
        return moves

    def simulate_placement(self, state, spot):
        color = state['your_color']
        board = state['board'][:]
        pieces_in_hand = state['pieces_in_hand'].copy()
        pieces_on_board = state['pieces_on_board'].copy()
        if board[spot] != '' or pieces_in_hand[color] <= 0:
            return None
        board[spot] = color
        pieces_in_hand[color] -= 1
        pieces_on_board[color] += 1
        new_board = self.apply_captures(board, color, spot)
        pieces_on_board['B'] = sum(1 for x in new_board if x == 'B')
        pieces_on_board['W'] = sum(1 for x in new_board if x == 'W')
        new_state = {}
        for k, v in state.items():
            if isinstance(v, list):
                new_state[k] = v[:]
            elif isinstance(v, dict):
                new_state[k] = v.copy()
            else:
                new_state[k] = v
        new_state['board'] = new_board
        new_state['pieces_in_hand'] = pieces_in_hand
        new_state['pieces_on_board'] = pieces_on_board
        new_state['your_color'] = state['opponent_color']
        new_state['opponent_color'] = state['your_color']
        if pieces_in_hand['B'] == 0 and pieces_in_hand['W'] == 0:
            new_state['phase'] = 'movement'
            new_state['move_count'] = 0
            new_state['history'] = []
        new_history = new_state['history'][:]
        board_tuple = tuple(new_state['board'])
        state_tuple = (board_tuple, new_state['your_color'])
        new_history.append(state_tuple)
        new_state['history'] = new_history
        return new_state

    def simulate_movement(self, state, fr, to):
        color = state['your_color']
        board = state['board'][:]
        pieces_on_board = state['pieces_on_board'].copy()
        if board[fr] != color or board[to] != '' or to not in ADJACENCY[fr]:
            return None
        board[to] = color
        board[fr] = ''
        new_board = self.apply_captures(board, color, to)
        pieces_on_board['B'] = sum(1 for x in new_board if x == 'B')
        pieces_on_board['W'] = sum(1 for x in new_board if x == 'W')
        new_state = {}
        for k, v in state.items():
            if isinstance(v, list):
                new_state[k] = v[:]
            elif isinstance(v, dict):
                new_state[k] = v.copy()
            else:
                new_state[k] = v
        new_state['board'] = new_board
        new_state['pieces_on_board'] = pieces_on_board
        new_state['your_color'] = state['opponent_color']
        new_state['opponent_color'] = state['your_color']
        new_state['move_count'] = state['move_count'] + 1
        new_history = new_state['history'][:]
        board_tuple = tuple(new_state['board'])
        state_tuple = (board_tuple, new_state['your_color'])
        new_history.append(state_tuple)
        new_state['history'] = new_history
        return new_state

    def get_score(self, state):
        opp_color = 'W' if self.color == 'B' else 'B'
        my_remaining = state['pieces_on_board'][self.color] + state['pieces_in_hand'][self.color]
        opp_remaining = state['pieces_on_board'][opp_color] + state['pieces_in_hand'][opp_color]
        if my_remaining == 0:
            return -1000
        if opp_remaining == 0:
            return 1000
        if state['phase'] == 'movement':
            board_tuple = tuple(state['board'])
            state_tuple = (board_tuple, state['your_color'])
            if state['history'].count(state_tuple) >= 3 or state['move_count'] >= 200:
                return 0
            legal = self.get_legal_movements(state['board'], state['your_color'])
            if len(legal) == 0:
                return -1000 if state['your_color'] == self.color else 1000
        my_mob = len(self.get_legal_placements(state['board']) if state['phase'] == 'placement' else self.get_legal_movements(state['board'], self.color))
        opp_mob = len(self.get_legal_placements(state['board']) if state['phase'] == 'placement' else self.get_legal_movements(state['board'], opp_color))
        return 10 * (my_remaining - opp_remaining) + (my_mob - opp_mob)

    def is_terminal(self, state):
        opp_color = 'W' if self.color == 'B' else 'B'
        my_remaining = state['pieces_on_board'][self.color] + state['pieces_in_hand'][self.color]
        opp_remaining = state['pieces_on_board'][opp_color] + state['pieces_in_hand'][opp_color]
        if my_remaining == 0 or opp_remaining == 0:
            return True
        if state['phase'] == 'movement':
            board_tuple = tuple(state['board'])
            state_tuple = (board_tuple, state['your_color'])
            if state['history'].count(state_tuple) >= 3 or state['move_count'] >= 200:
                return True
            if len(self.get_legal_movements(state['board'], state['your_color'])) == 0:
                return True
        return False

    def minimax(self, state, depth, alpha, beta, is_max):
        if depth == 0 or self.is_terminal(state):
            return self.get_score(state)
        current = state['your_color']
        phase = state['phase']
        legal = self.get_legal_placements(state['board']) if phase == 'placement' else self.get_legal_movements(state['board'], current)
        if is_max:
            max_eval = -float('inf')
            for action in legal:
                new_state = self.simulate_placement(state, action) if phase == 'placement' else self.simulate_movement(state, action[0], action[1])
                if new_state is None:
                    continue
                eval = self.minimax(new_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for action in legal:
                new_state = self.simulate_placement(state, action) if phase == 'placement' else self.simulate_movement(state, action[0], action[1])
                if new_state is None:
                    continue
                eval = self.minimax(new_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, state: dict, feedback: dict | None = None):
        phase = state["phase"]
        if phase == "placement":
            pieces_placed = 14 - (state['pieces_in_hand']['B'] + state['pieces_in_hand']['W'])
            depth = 1 if pieces_placed < 8 else 2
            legal = self.get_legal_placements(state['board'])
        else:
            my_remaining = state['pieces_on_board'][self.color] + state['pieces_in_hand'][self.color]
            opp_remaining = state['pieces_on_board']['W' if self.color == 'B' else 'B'] + state['pieces_in_hand']['W' if self.color == 'B' else 'B']
            total_pieces = my_remaining + opp_remaining
            depth = 2 if total_pieces > 10 else 3 if total_pieces > 5 else 4
            legal = self.get_legal_movements(state['board'], state['your_color'])
        if not legal:
            return random.choice(range(24)) if phase == "placement" else (0, 1)
        best_value = -float('inf')
        best_move = legal[0]
        for action in legal:
            new_state = self.simulate_placement(state, action) if phase == "placement" else self.simulate_movement(state, action[0], action[1])
            if new_state is None:
                continue
            value = self.minimax(new_state, depth, -float('inf'), float('inf'), False)
            if value > best_value:
                best_value = value
                best_move = action
        return best_move