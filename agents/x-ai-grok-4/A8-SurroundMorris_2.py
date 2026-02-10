"""
Agent Code: A8-SurroundMorris
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-10 22:38:58
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.spot_values = [len(ADJACENCY[i]) for i in range(24)]

    def make_move(self, state: dict, feedback: dict | None = None):
        my_state = {
            'board': state['board'][:],
            'phase': state['phase'],
            'current_player': state['your_color'],
            'pieces_in_hand': state['pieces_in_hand'].copy(),
            'pieces_on_board': state['pieces_on_board'].copy(),
            'move_count': state['move_count'],
            'history': state['history'][:],
        }

        legal_moves = self.get_legal_moves(my_state)
        if not legal_moves:
            return 0 if my_state['phase'] == 'placement' else (0, 1)

        best_move = None
        best_score = -float('inf')
        for move in legal_moves:
            result = self.apply_move(my_state, move)
            if isinstance(result, dict):
                score = self.minimax(result, 3, -float('inf'), float('inf'))
            else:
                end_type, *args = result
                if end_type == 'elimination':
                    winner, sc = args
                    score = sc if winner == self.color else -sc
                elif end_type == 'turn_limit' or end_type == 'elimination_draw':
                    score = 0
            if score > best_score or (score == best_score and random.random() < 0.5):
                best_score = score
                best_move = move
        return best_move

    def get_legal_moves(self, my_state):
        color = my_state['current_player']
        board = my_state['board']
        phase = my_state['phase']
        if phase == 'placement':
            return [i for i in range(24) if board[i] == '']
        else:
            moves = []
            for spot in range(24):
                if board[spot] == color:
                    for n in ADJACENCY[spot]:
                        if board[n] == '':
                            moves.append((spot, n))
            return moves

    def is_captured(self, spot, board):
        color = board[spot]
        if color == '':
            return False
        neighbors = ADJACENCY[spot]
        empty = 0
        friendly = 0
        opponent = 0
        opp = 'W' if color == 'B' else 'B'
        for n in neighbors:
            b = board[n]
            if b == '': empty += 1
            elif b == color: friendly += 1
            else: opponent += 1
        return empty == 0 and opponent > friendly

    def process_captures(self, board, active_spot, active_color):
        board = board[:]
        if self.is_captured(active_spot, board):
            board[active_spot] = ''
            return board
        friendly_captured = [s for s in range(24) if board[s] == active_color and self.is_captured(s, board)]
        for s in friendly_captured:
            board[s] = ''
        opp_color = 'W' if active_color == 'B' else 'B'
        opp_captured = [s for s in range(24) if board[s] == opp_color and self.is_captured(s, board)]
        for s in opp_captured:
            board[s] = ''
        return board

    def apply_move(self, my_state, move):
        new_s = {k: v.copy() if isinstance(v, (list, dict)) else v for k, v in my_state.items()}
        color = new_s['current_player']
        opp_color = 'W' if color == 'B' else 'B'
        phase = new_s['phase']
        if phase == 'placement':
            spot = move
            new_s['board'][spot] = color
            new_s['pieces_in_hand'][color] -= 1
            new_s['pieces_on_board'][color] += 1
            active_spot = spot
        else:
            from_sp, to_sp = move
            new_s['board'][to_sp] = color
            new_s['board'][from_sp] = ''
            active_spot = to_sp
            new_s['move_count'] += 1
        new_s['board'] = self.process_captures(new_s['board'], active_spot, color)
        pob = {'B': 0, 'W': 0}
        for i, p in enumerate(new_s['board']):
            if p in pob:
                pob[p] += 1
        new_s['pieces_on_board'] = pob
        if phase == 'placement' and all(v == 0 for v in new_s['pieces_in_hand'].values()):
            new_s['phase'] = 'movement'
            new_s['history'] = []
            new_s['move_count'] = 0
        elim = []
        for c in ['B', 'W']:
            if pob[c] == 0 and (new_s['phase'] != 'placement' or new_s['pieces_in_hand'][c] == 0):
                elim.append(c)
        if len(elim) == 2:
            return 'elimination_draw', 0
        elif len(elim) == 1:
            loser = elim[0]
            winner = 'W' if loser == 'B' else 'B'
            score = pob[winner]
            return 'elimination', winner, score
        if new_s['phase'] == 'movement' and new_s['move_count'] >= 200:
            return 'turn_limit', 'draw'
        new_s['current_player'] = opp_color
        return new_s

    def evaluate_board(self, my_state):
        my_color = self.color
        opp_color = 'W' if my_color == 'B' else 'B'
        my_p = my_state['pieces_on_board'][my_color] + my_state['pieces_in_hand'][my_color]
        opp_p = my_state['pieces_on_board'][opp_color] + my_state['pieces_in_hand'][opp_color]
        my_control = sum(self.spot_values[s] for s in range(24) if my_state['board'][s] == my_color)
        opp_control = sum(self.spot_values[s] for s in range(24) if my_state['board'][s] == opp_color)
        return (my_p - opp_p) * 10 + (my_control - opp_control)

    def minimax(self, my_state, depth, alpha, beta):
        my_color = self.color
        current = my_state['current_player']
        is_max = (current == my_color)
        pos = (tuple(my_state['board']), current)
        temp_history = my_state['history'] + [pos]
        if temp_history.count(pos) >= 3:
            return 0
        if my_state['phase'] == 'movement' and my_state['move_count'] >= 200:
            return 0
        legal = self.get_legal_moves(my_state)
        if not legal:
            winner = 'W' if current == 'B' else 'B'
            return 7 if winner == my_color else -7
        if depth == 0:
            return self.evaluate_board(my_state)
        if is_max:
            max_eval = -float('inf')
            for move in legal:
                result = self.apply_move(my_state, move)
                if isinstance(result, dict):
                    eval = self.minimax(result, depth - 1, alpha, beta)
                else:
                    end_type, *args = result
                    if end_type == 'elimination_draw' or end_type == 'turn_limit':
                        eval = 0
                    elif end_type == 'elimination':
                        w, sc = args
                        eval = sc if w == my_color else -sc
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal:
                result = self.apply_move(my_state, move)
                if isinstance(result, dict):
                    eval = self.minimax(result, depth - 1, alpha, beta)
                else:
                    end_type, *args = result
                    if end_type == 'elimination_draw' or end_type == 'turn_limit':
                        eval = 0
                    elif end_type == 'elimination':
                        w, sc = args
                        eval = sc if w == my_color else -sc
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
