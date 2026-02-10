"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-10 22:38:58
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    @staticmethod
    def is_captured(spot, board):
        if board[spot] == '':
            return False
        color = board[spot]
        empty_count = 0
        friendly_count = 0
        opponent_count = 0
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty_count += 1
            elif board[neighbor] == color:
                friendly_count += 1
            else:
                opponent_count += 1
        return (empty_count == 0) and (opponent_count > friendly_count)

    @staticmethod
    def resolve_captures(board, active_spot, color_moved):
        board = board[:]
        opp_color = 'W' if color_moved == 'B' else 'B'
        
        if board[active_spot] == color_moved and SurroundMorrisAgent.is_captured(active_spot, board):
            board[active_spot] = ''
            return board
        
        to_remove = []
        for spot in range(24):
            if board[spot] == color_moved and SurroundMorrisAgent.is_captured(spot, board):
                to_remove.append(spot)
        for spot in to_remove:
            board[spot] = ''
        
        to_remove = []
        for spot in range(24):
            if board[spot] == opp_color and SurroundMorrisAgent.is_captured(spot, board):
                to_remove.append(spot)
        for spot in to_remove:
            board[spot] = ''
        
        return board

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        if phase == "placement":
            candidates = [i for i in range(24) if board[i] == '']
        else:
            candidates = []
            for spot in range(24):
                if board[spot] == color:
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == '':
                            candidates.append((spot, neighbor))
        
        if not candidates:
            if phase == "placement":
                return 0
            else:
                return (0, 1)
        
        best_score = -10**9
        best_move = candidates[0]
        
        for move in candidates:
            board_after = board[:]
            if phase == "placement":
                spot = move
                board_after[spot] = color
                active_spot = spot
            else:
                from_spot, to_spot = move
                board_after[from_spot] = ''
                board_after[to_spot] = color
                active_spot = to_spot
            
            board_final = self.__class__.resolve_captures(board_after, active_spot, color)
            
            our_board_after = sum(1 for i in range(24) if board_final[i] == color)
            opp_board_after = sum(1 for i in range(24) if board_final[i] == opp)
            
            if phase == "placement":
                if our_board_after == 0 and state['pieces_in_hand'][color] == 1:
                    score = -10000
                elif opp_board_after == 0 and state['pieces_in_hand'][opp] == 0:
                    score = 10000 + our_board_after
                else:
                    our_total_after = our_board_after + (state['pieces_in_hand'][color] - 1)
                    opp_total_after = opp_board_after + state['pieces_in_hand'][opp]
                    score = our_total_after - opp_total_after
            else:
                if our_board_after == 0:
                    score = -10000
                elif opp_board_after == 0:
                    score = 10000 + our_board_after
                else:
                    has_legal_move = False
                    for spot in range(24):
                        if board_final[spot] == opp:
                            for neighbor in ADJACENCY[spot]:
                                if board_final[neighbor] == '':
                                    has_legal_move = True
                                    break
                            if has_legal_move:
                                break
                    if not has_legal_move:
                        score = 10000 + 7
                    else:
                        score = our_board_after - opp_board_after
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
