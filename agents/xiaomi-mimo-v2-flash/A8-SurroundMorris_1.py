"""
Agent Code: A8-SurroundMorris
Model: xiaomi/mimo-v2-flash
Run: 1
Generated: 2026-02-09 19:15:26
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opp_color = 'W' if color == 'B' else 'B'

    def is_captured(self, spot, board):
        if board[spot] == '':
            return False
        color = board[spot]
        neighbors = ADJACENCY[spot]
        empty_count = 0
        opp_count = 0
        friendly_count = 0
        for n in neighbors:
            if board[n] == '':
                empty_count += 1
            elif board[n] == color:
                friendly_count += 1
            else:
                opp_count += 1
        if empty_count == 0 and opp_count > friendly_count:
            return True
        return False

    def make_move(self, state, feedback=None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        if phase == "placement":
            best_score = -10**9
            best_spot = None
            for spot in range(24):
                if board[spot] != '':
                    continue
                new_board = board.copy()
                new_board[spot] = color
                if self.is_captured(spot, new_board):
                    score = -1000
                else:
                    our_pieces = [i for i in range(24) if new_board[i] == color]
                    our_captured = [i for i in our_pieces if self.is_captured(i, new_board)]
                    temp_board = new_board.copy()
                    for i in our_captured:
                        temp_board[i] = ''
                    opp_pieces = [i for i in range(24) if temp_board[i] == opp]
                    opp_captured = [i for i in opp_pieces if self.is_captured(i, temp_board)]
                    net_capture = len(opp_captured) - len(our_captured)
                    deg = len(ADJACENCY[spot])
                    base_score = {4: 4, 3: 3, 2: 2}.get(deg, 0)
                    adj_friend = sum(1 for n in ADJACENCY[spot] if new_board[n] == color)
                    adj_opp = sum(1 for n in ADJACENCY[spot] if new_board[n] == opp)
                    score = base_score + 10 * net_capture + 0.5 * adj_friend - 0.5 * adj_opp
                if score > best_score:
                    best_score = score
                    best_spot = spot
            if best_spot is None:
                empty_spots = [i for i in range(24) if board[i] == '']
                return random.choice(empty_spots) if empty_spots else 0
            return best_spot
        
        else:  # movement
            best_score = -10**9
            best_move = None
            moves = []
            for from_spot in range(24):
                if board[from_spot] != color:
                    continue
                for to_spot in ADJACENCY[from_spot]:
                    if board[to_spot] != '':
                        continue
                    moves.append((from_spot, to_spot))
            if not moves:
                return (0, 1)
            for (from_spot, to_spot) in moves:
                new_board = board.copy()
                new_board[from_spot] = ''
                new_board[to_spot] = color
                if self.is_captured(to_spot, new_board):
                    score = -1000
                else:
                    our_pieces = [i for i in range(24) if new_board[i] == color]
                    our_captured = [i for i in our_pieces if self.is_captured(i, new_board)]
                    temp_board = new_board.copy()
                    for i in our_captured:
                        temp_board[i] = ''
                    opp_pieces = [i for i in range(24) if temp_board[i] == opp]
                    opp_captured = [i for i in opp_pieces if self.is_captured(i, temp_board)]
                    net_capture = len(opp_captured) - len(our_captured)
                    deg = len(ADJACENCY[to_spot])
                    base_score = {4: 4, 3: 3, 2: 2}.get(deg, 0)
                    adj_friend = sum(1 for n in ADJACENCY[to_spot] if new_board[n] == color)
                    adj_opp = sum(1 for n in ADJACENCY[to_spot] if new_board[n] == opp)
                    rep_factor = 0
                    new_state = (tuple(new_board), opp)
                    count = state['history'].count(new_state)
                    if count >= 2:
                        our_pieces_count = state['pieces_on_board'][color]
                        opp_pieces_count = state['pieces_on_board'][opp]
                        if our_pieces_count > opp_pieces_count:
                            rep_factor = -1000
                        else:
                            rep_factor = 1000
                    score = base_score + 10 * net_capture + 0.5 * adj_friend - 0.5 * adj_opp + rep_factor
                if score > best_score:
                    best_score = score
                    best_move = (from_spot, to_spot)
            if best_move is None:
                return moves[0]
            return best_move
