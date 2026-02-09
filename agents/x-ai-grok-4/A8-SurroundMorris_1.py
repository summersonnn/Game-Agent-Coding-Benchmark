"""
Agent Code: A8-SurroundMorris
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-09 19:05:17
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        hand = state["pieces_in_hand"]
        move_count = state["move_count"]

        # Helper functions
        def is_captured(b, spot):
            if b[spot] == '': return False
            p_color = b[spot]
            o_color = 'W' if p_color == 'B' else 'B'
            empty = 0
            friend = 0
            enemy = 0
            for n in ADJACENCY[spot]:
                if b[n] == '':
                    empty += 1
                elif b[n] == p_color:
                    friend += 1
                else:
                    enemy += 1
            return empty == 0 and enemy > friend

        def get_legal(player, b, ph, h):
            if ph == 'placement':
                if h[player] == 0:
                    return []
                return [i for i in range(24) if b[i] == '']
            else:
                moves = []
                for spot in range(24):
                    if b[spot] == player:
                        for n in ADJACENCY[spot]:
                            if b[n] == '':
                                moves.append((spot, n))
                return moves

        def simulate_move(b, ph, player, action, h, mc):
            o = 'W' if player == 'B' else 'B'
            new_b = list(b)
            new_h = dict(h)
            if ph == 'placement':
                spot = action
                new_b[spot] = player
                active = spot
                new_h[player] -= 1
            else:
                fr, to = action
                new_b[fr] = ''
                new_b[to] = player
                active = to
            # captures
            if is_captured(new_b, active):
                new_b[active] = ''
            else:
                to_remove = [s for s in range(24) if new_b[s] == player and is_captured(new_b, s)]
                for s in to_remove:
                    new_b[s] = ''
                to_remove = [s for s in range(24) if new_b[s] == o and is_captured(new_b, s)]
                for s in to_remove:
                    new_b[s] = ''
            # new_phase
            new_ph = 'movement' if ph == 'placement' and new_h['B'] == 0 and new_h['W'] == 0 else ph
            # check ended
            p_on = sum(1 for x in new_b if x == player)
            o_on = sum(1 for x in new_b if x == o)
            ended = False
            winner = None
            if p_on == 0 and (new_ph != 'placement' or new_h[player] == 0):
                ended = True
                winner = o
            if o_on == 0 and (new_ph != 'placement' or new_h[o] == 0):
                ended = True
                winner = player
            if ended:
                return new_b, new_h, new_ph, ended, winner
            # check if next player stuck
            next_player = o
            next_legal = get_legal(next_player, new_b, new_ph, new_h)
            if not next_legal:
                ended = True
                winner = player
            return new_b, new_h, new_ph, ended, winner

        # Get my legal moves
        my_legal = get_legal(color, board, phase, hand)
        if not my_legal:
            return 0 if phase == 'placement' else (0, 1)

        # Evaluate with depth-2 minimax
        best_score = -float('inf')
        best_actions = []
        for action in my_legal:
            sim_b, sim_h, sim_ph, ended, winner = simulate_move(board, phase, color, action, hand, move_count)
            if ended:
                if winner == color:
                    score = 1000
                elif winner == opp:
                    score = -1000
                else:
                    score = 0
            else:
                opp_legal = get_legal(opp, sim_b, sim_ph, sim_h)
                if not opp_legal:
                    score = 1000
                else:
                    min_score = float('inf')
                    for o_action in opp_legal:
                        o_sim_b, o_sim_h, o_sim_ph, o_ended, o_winner = simulate_move(sim_b, sim_ph, opp, o_action, sim_h, move_count)
                        if o_ended:
                            if o_winner == color:
                                this_score = 1000
                            elif o_winner == opp:
                                this_score = -1000
                            else:
                                this_score = 0
                        else:
                            my_on = sum(1 for x in o_sim_b if x == color)
                            opp_on = sum(1 for x in o_sim_b if x == opp)
                            my_t = my_on + o_sim_h[color] if o_sim_ph == 'placement' else my_on
                            opp_t = opp_on + o_sim_h[opp] if o_sim_ph == 'placement' else opp_on
                            this_score = my_t - opp_t
                        min_score = min(min_score, this_score)
                    score = min_score
            if score > best_score:
                best_score = score
                best_actions = [action]
            elif score == best_score:
                best_actions.append(action)

        return random.choice(best_actions)
