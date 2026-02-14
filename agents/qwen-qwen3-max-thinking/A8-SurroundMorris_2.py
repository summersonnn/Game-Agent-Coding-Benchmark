"""
Agent Code: A8-SurroundMorris
Model: qwen-qwen3-max-thinking
Run: 2
Generated: 2026-02-09 19:15:26
"""

import random

class SurroundMorrisAgent:
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

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        history = state["history"]

        def is_captured(board, spot, piece_color):
            if board[spot] != piece_color:
                return False
            opp_color = 'W' if piece_color == 'B' else 'B'
            neighbors = self.ADJACENCY[spot]
            empty = opp_count = friendly = 0
            for nb in neighbors:
                nb_piece = board[nb]
                if nb_piece == '':
                    empty += 1
                elif nb_piece == opp_color:
                    opp_count += 1
                elif nb_piece == piece_color:
                    friendly += 1
            return empty == 0 and opp_count > friendly

        def resolve_captures(board, last_occupied_spot, mover_color):
            board = board.copy()
            opp_color = 'W' if mover_color == 'B' else 'B'
            
            if board[last_occupied_spot] == mover_color and is_captured(board, last_occupied_spot, mover_color):
                board[last_occupied_spot] = ''
                return board
            
            friendly_captures = []
            for spot in range(24):
                if board[spot] == mover_color and is_captured(board, spot, mover_color):
                    friendly_captures.append(spot)
            for spot in friendly_captures:
                board[spot] = ''
            
            enemy_captures = []
            for spot in range(24):
                if board[spot] == opp_color and is_captured(board, spot, opp_color):
                    enemy_captures.append(spot)
            for spot in enemy_captures:
                board[spot] = ''
            
            return board

        def evaluate_board(board, color, opp):
            our_count = board.count(color)
            opp_count = board.count(opp)
            score = (our_count - opp_count) * 100
            
            our_empty_neighbors = opp_empty_neighbors = 0
            for spot in range(24):
                if board[spot] == color:
                    for nb in self.ADJACENCY[spot]:
                        if board[nb] == '':
                            our_empty_neighbors += 1
                elif board[spot] == opp:
                    for nb in self.ADJACENCY[spot]:
                        if board[nb] == '':
                            opp_empty_neighbors += 1
            score += (our_empty_neighbors - opp_empty_neighbors) * 5
            
            degree_values = {2: 2, 3: 3, 4: 5}
            for spot in range(24):
                deg = len(self.ADJACENCY[spot])
                if board[spot] == color:
                    score += degree_values.get(deg, 0)
                elif board[spot] == opp:
                    score -= degree_values.get(deg, 0)
            
            return score

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0
            
            best_score = -10**9
            best_move = empty_spots[0]
            our_in_hand_after = pieces_in_hand[color] - 1
            opp_in_hand_after = pieces_in_hand[opp]
            
            for spot in empty_spots:
                board2 = board.copy()
                board2[spot] = color
                board2 = resolve_captures(board2, spot, color)
                
                our_count = board2.count(color)
                opp_count = board2.count(opp)
                
                if opp_count == 0 and opp_in_hand_after == 0:
                    return spot
                if our_count == 0 and our_in_hand_after == 0:
                    continue
                
                new_tuple = tuple(board2)
                next_player = opp
                rep_count = sum(1 for (b, p) in history if b == new_tuple and p == next_player)
                causes_draw = (rep_count >= 2)
                
                if causes_draw:
                    if our_count > opp_count:
                        score = -10**9
                    elif our_count < opp_count:
                        score = 10**9
                    else:
                        score = 0
                else:
                    score = evaluate_board(board2, color, opp)
                
                if score > best_score:
                    best_score = score
                    best_move = spot
            
            return best_move
        
        else:
            moves = []
            for spot in range(24):
                if board[spot] == color:
                    for nb in self.ADJACENCY[spot]:
                        if board[nb] == '':
                            moves.append((spot, nb))
            
            if not moves:
                return (0, 1) if board[0] == color and board[1] == '' else (0, 0)
            
            best_score = -10**9
            best_move = moves[0]
            
            for (from_spot, to_spot) in moves:
                board2 = board.copy()
                board2[from_spot] = ''
                board2[to_spot] = color
                board2 = resolve_captures(board2, to_spot, color)
                
                our_count = board2.count(color)
                opp_count = board2.count(opp)
                
                if opp_count == 0:
                    return (from_spot, to_spot)
                if our_count == 0:
                    continue
                
                new_tuple = tuple(board2)
                next_player = opp
                rep_count = sum(1 for (b, p) in history if b == new_tuple and p == next_player)
                causes_draw = (rep_count >= 2)
                
                if causes_draw:
                    if our_count > opp_count:
                        score = -10**9
                    elif our_count < opp_count:
                        score = 10**9
                    else:
                        score = 0
                else:
                    score = evaluate_board(board2, color, opp)
                
                if score > best_score:
                    best_score = score
                    best_move = (from_spot, to_spot)
            
            return best_move