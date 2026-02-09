"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-09 19:15:26
"""



import random

def is_captured(spot, board):
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
    return (empty_count == 0) and (opp_count > friendly_count)

def is_mated(board, color):
    for spot in range(24):
        if board[spot] == color:
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    return False
    return True

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        pieces_on_board = state["pieces_on_board"]
        history = state["history"]
        
        if feedback:
            attempted_move = feedback['attempted_move']
        else:
            attempted_move = None

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            candidates = []
            for spot in empty_spots:
                if feedback and attempted_move == spot:
                    continue
                new_board = board[:]
                new_board[spot] = color
                active_captured = is_captured(spot, new_board)
                if active_captured:
                    new_board[spot] = ''
                    friendly_removed_step2a = 0
                    enemy_removed_step2b = 0
                else:
                    to_remove_friendly = []
                    for s in range(24):
                        if new_board[s] == color and is_captured(s, new_board):
                            to_remove_friendly.append(s)
                    for s in to_remove_friendly:
                        new_board[s] = ''
                    to_remove_enemy = []
                    for s in range(24):
                        if new_board[s] == opp and is_captured(s, new_board):
                            to_remove_enemy.append(s)
                    for s in to_remove_enemy:
                        new_board[s] = ''
                    friendly_removed_step2a = len(to_remove_friendly)
                    enemy_removed_step2b = len(to_remove_enemy)
                
                current_our_on_board = pieces_on_board[color]
                current_opp_on_board = pieces_on_board[opp]
                our_in_hand = pieces_in_hand[color]
                opp_in_hand = pieces_in_hand[opp]
                
                our_on_board_after = current_our_on_board + 1 - (1 if active_captured else 0) - friendly_removed_step2a
                opp_on_board_after = current_opp_on_board - enemy_removed_step2b
                our_in_hand_after = our_in_hand - 1
                opp_in_hand_after = opp_in_hand
                
                if opp_on_board_after == 0 and opp_in_hand_after == 0:
                    score = our_on_board_after
                elif our_on_board_after == 0 and our_in_hand_after == 0:
                    score = -1000
                else:
                    net_gain = enemy_removed_step2b - ((1 if active_captured else 0) + friendly_removed_step2a)
                    score = net_gain
                
                degree = len(ADJACENCY[spot])
                candidates.append((score, degree, spot))
            
            if not candidates:
                for spot in empty_spots:
                    if spot == attempted_move:
                        continue
                    degree = len(ADJACENCY[spot])
                    candidates.append((-1000, degree, spot))
                if not candidates:
                    return empty_spots[0] if empty_spots else 0
            
            candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
            best_score, best_degree, best_spot = candidates[0]
            return best_spot

        else:
            legal_moves = []
            for spot in range(24):
                if board[spot] == color:
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == '':
                            legal_moves.append((spot, neighbor))
            
            candidates = []
            for move in legal_moves:
                if feedback and attempted_move == move:
                    continue
                from_spot, to_spot = move
                new_board = board[:]
                new_board[from_spot] = ''
                new_board[to_spot] = color
                active_captured = is_captured(to_spot, new_board)
                if active_captured:
                    new_board[to_spot] = ''
                    friendly_removed_step2a = 0
                    enemy_removed_step2b = 0
                else:
                    to_remove_friendly = []
                    for s in range(24):
                        if new_board[s] == color and is_captured(s, new_board):
                            to_remove_friendly.append(s)
                    for s in to_remove_friendly:
                        new_board[s] = ''
                    to_remove_enemy = []
                    for s in range(24):
                        if new_board[s] == opp and is_captured(s, new_board):
                            to_remove_enemy.append(s)
                    for s in to_remove_enemy:
                        new_board[s] = ''
                    friendly_removed_step2a = len(to_remove_friendly)
                    enemy_removed_step2b = len(to_remove_enemy)
                
                current_our_on_board = pieces_on_board[color]
                current_opp_on_board = pieces_on_board[opp]
                our_on_board_after = current_our_on_board - friendly_removed_step2a
                opp_on_board_after = current_opp_on_board - enemy_removed_step2b
                
                if opp_on_board_after == 0:
                    score = our_on_board_after
                else:
                    if is_mated(new_board, opp):
                        score = 7
                    else:
                        next_state = (tuple(new_board), opp)
                        count = 0
                        for h in history:
                            if h == next_state:
                                count += 1
                        if count >= 2:
                            total_after = our_on_board_after + opp_on_board_after
                            score = total_after / 2.0
                        else:
                            net_gain = enemy_removed_step2b - friendly_removed_step2a
                            score = net_gain
                
                degree = len(ADJACENCY[to_spot])
                candidates.append((score, degree, move))
            
            if not candidates:
                for move in legal_moves:
                    if move == attempted_move:
                        continue
                    from_spot, to_spot = move
                    degree = len(ADJACENCY[to_spot])
                    candidates.append((-1000, degree, move))
                if not candidates:
                    return legal_moves[0] if legal_moves else (0, 1)
            
            candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
            best_score, best_degree, best_move = candidates[0]
            return best_move
