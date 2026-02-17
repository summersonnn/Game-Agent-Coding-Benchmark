"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3.5-397b-a17b
Run: 1
Generated: 2026-02-16 17:46:27
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
        self.opp_color = 'W' if color == 'B' else 'B'

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        history = state.get("history", [])
        
        if phase == "placement":
            return self._get_placement_move(board, history)
        else:
            return self._get_movement_move(board, history)

    def _get_legal_placements(self, board):
        return [i for i, spot in enumerate(board) if spot == '']

    def _get_legal_movements(self, board, color):
        moves = []
        for i, spot in enumerate(board):
            if spot == color:
                for neighbor in self.ADJACENCY[i]:
                    if board[neighbor] == '':
                        moves.append((i, neighbor))
        return moves

    def _is_captured_local(self, spot, board):
        p_color = board[spot]
        if p_color == '': 
            return False
        
        empty = 0
        friendly = 0
        opponent = 0
        
        for neighbor in self.ADJACENCY[spot]:
            val = board[neighbor]
            if val == '':
                empty += 1
            elif val == p_color:
                friendly += 1
            else:
                opponent += 1
        
        return (empty == 0) and (opponent > friendly)

    def _simulate_capture_process(self, board, active_spot, mover_color):
        new_board = list(board)
        
        # 1. Active Piece Suicide Check
        if active_spot is not None and 0 <= active_spot < 24 and new_board[active_spot] != '':
            if self._is_captured_local(active_spot, new_board):
                new_board[active_spot] = ''
                return new_board
        
        # 2. Universal Capture Sweep
        # 2a. Friendly pieces
        friendlies_to_remove = []
        for i in range(24):
            if new_board[i] == mover_color:
                if self._is_captured_local(i, new_board):
                    friendlies_to_remove.append(i)
        
        for i in friendlies_to_remove:
            new_board[i] = ''
            
        # 2b. Enemy pieces
        opp_color = 'W' if mover_color == 'B' else 'B'
        enemies_to_remove = []
        for i in range(24):
            if new_board[i] == opp_color:
                if self._is_captured_local(i, new_board):
                    enemies_to_remove.append(i)
                    
        for i in enemies_to_remove:
            new_board[i] = ''
            
        return new_board

    def _evaluate_board(self, board, my_color):
        opp_color = 'W' if my_color == 'B' else 'B'
        score = 0
        
        my_pieces = sum(1 for x in board if x == my_color)
        opp_pieces = sum(1 for x in board if x == opp_color)
        
        # Material is king
        score += (my_pieces - opp_pieces) * 1000
        
        # Mobility
        my_moves = len(self._get_legal_movements(board, my_color))
        opp_moves = len(self._get_legal_movements(board, opp_color))
        
        # Mate conditions are game-ending
        if my_moves == 0:
            score -= 100000
        if opp_moves == 0:
            score += 100000
            
        score += (my_moves - opp_moves) * 10
        
        # Threats (pieces with 1 empty neighbor)
        for i in range(24):
            if board[i] == my_color:
                empty, f, o = self._get_neighbor_counts_local(i, board)
                if empty == 1:
                    score -= 50 
            elif board[i] == opp_color:
                empty, f, o = self._get_neighbor_counts_local(i, board)
                if empty == 1:
                    score += 50
        
        return score

    def _get_neighbor_counts_local(self, spot, board):
        empty = 0
        friendly = 0
        opponent = 0
        p_color = board[spot]
        if p_color == '': return 0,0,0
        
        opp_color = 'W' if p_color == 'B' else 'B'
        
        for n in self.ADJACENCY[spot]:
            val = board[n]
            if val == '': empty += 1
            elif val == p_color: friendly += 1
            else: opponent += 1
        return empty, friendly, opponent

    def _get_placement_move(self, board, history):
        legal_spots = self._get_legal_placements(board)
        if not legal_spots:
            return 0 
        
        best_spot = None
        best_score = -float('inf')
        
        for spot in legal_spots:
            temp_board = list(board)
            temp_board[spot] = self.color
            
            final_board = self._simulate_capture_process(temp_board, spot, self.color)
            
            rep_penalty = 0
            next_player = self.opp_color
            board_tuple = tuple(final_board)
            count = 0
            for h_board, h_player in history:
                if h_board == board_tuple and h_player == next_player:
                    count += 1
            if count >= 2:
                rep_penalty = -5000
            
            score = self._evaluate_board(final_board, self.color) + rep_penalty
            score += random.random() 
            
            if score > best_score:
                best_score = score
                best_spot = spot
                
        return best_spot

    def _get_movement_move(self, board, history):
        legal_moves = self._get_legal_movements(board, self.color)
        if not legal_moves:
            return (0, 1) 
        
        best_move = None
        best_score = -float('inf')
        
        for move in legal_moves:
            from_s, to_s = move
            temp_board = list(board)
            temp_board[from_s] = ''
            temp_board[to_s] = self.color
            
            final_board = self._simulate_capture_process(temp_board, to_s, self.color)
            
            rep_penalty = 0
            next_player = self.opp_color
            board_tuple = tuple(final_board)
            count = 0
            for h_board, h_player in history:
                if h_board == board_tuple and h_player == next_player:
                    count += 1
            if count >= 2:
                rep_penalty = -5000
            
            score = self._evaluate_board(final_board, self.color) + rep_penalty
            score += random.random()
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move