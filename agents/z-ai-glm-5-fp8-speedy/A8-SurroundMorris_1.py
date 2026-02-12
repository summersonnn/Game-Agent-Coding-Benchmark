"""
Agent Code: A8-SurroundMorris
Model: z-ai/glm-5@preset/fp8
Run: 1
Generated: 2026-02-11 21:33:53
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.crossroads = {4, 10, 13, 19}
        self.t_junctions = {1, 7, 9, 11, 12, 14, 16, 22}
        self.corners = {0, 2, 3, 5, 6, 8, 15, 17, 18, 20, 21, 23}
    
    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        if phase == "placement":
            return self._placement_move(board, color, opp, state)
        else:
            return self._movement_move(board, color, opp, state)
    
    def _placement_move(self, board, color, opp, state):
        empty = [i for i in range(24) if board[i] == '']
        if not empty:
            return 0
        
        scored = []
        for spot in empty:
            score = self._evaluate_placement(board, spot, color, opp)
            if self._would_suicide(board, spot, color, opp):
                score -= 10000
            scored.append((score, spot))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1]
    
    def _movement_move(self, board, color, opp, state):
        moves = self._get_legal_moves(board, color)
        if not moves:
            return (0, 1)
        
        history = state.get("history", [])
        position_counts = {}
        for h in history:
            position_counts[h] = position_counts.get(h, 0) + 1
        
        my_pieces = sum(1 for s in range(24) if board[s] == color)
        opp_pieces = sum(1 for s in range(24) if board[s] == opp)
        winning = my_pieces > opp_pieces
        
        scored = []
        for move in moves:
            from_spot, to_spot = move
            new_board = self._simulate_move(board, from_spot, to_spot, color, opp)
            
            score = self._evaluate_board(new_board, color, opp)
            
            board_tuple = tuple(new_board)
            rep_count = position_counts.get((board_tuple, opp), 0)
            if rep_count >= 2:
                score -= 1000 if winning else 50
            
            captures = sum(1 for s in range(24) if board[s] == opp and new_board[s] == '')
            score += captures * 100
            
            friendly_fire = sum(1 for s in range(24) if s != from_spot and board[s] == color and new_board[s] == '')
            score -= friendly_fire * 120
            
            opp_moves_after = len(self._get_legal_moves(new_board, opp))
            if opp_moves_after == 0 and opp_pieces > 0:
                score += 800
            
            scored.append((score, move))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1]
    
    def _get_legal_moves(self, board, color):
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    moves.append((spot, neighbor))
        return moves
    
    def _would_suicide(self, board, spot, color, opp):
        neighbors = ADJACENCY[spot]
        empty = sum(1 for n in neighbors if board[n] == '')
        opp_count = sum(1 for n in neighbors if board[n] == opp)
        friendly = sum(1 for n in neighbors if board[n] == color)
        return empty == 0 and opp_count > friendly
    
    def _simulate_placement(self, board, spot, color, opp):
        new_board = list(board)
        new_board[spot] = color
        return self._process_captures(new_board, color, opp, active_piece=spot)
    
    def _simulate_move(self, board, from_spot, to_spot, color, opp):
        new_board = list(board)
        new_board[from_spot] = ''
        new_board[to_spot] = color
        return self._process_captures(new_board, color, opp, active_piece=to_spot)
    
    def _process_captures(self, board, color, opp, active_piece=None):
        new_board = list(board)
        
        # Step 1: Active piece suicide check
        if active_piece is not None and new_board[active_piece] != '':
            if self._is_captured(new_board, active_piece):
                new_board[active_piece] = ''
                return new_board
        
        # Step 2a: Remove overwhelmed friendlies first
        for spot in range(24):
            if new_board[spot] == color and self._is_captured(new_board, spot):
                new_board[spot] = ''
        
        # Step 2b: Then remove overwhelmed enemies
        for spot in range(24):
            if new_board[spot] == opp and self._is_captured(new_board, spot):
                new_board[spot] = ''
        
        return new_board
    
    def _is_captured(self, board, spot):
        if board[spot] == '':
            return False
        
        color = board[spot]
        opp = 'W' if color == 'B' else 'B'
        
        neighbors = ADJACENCY[spot]
        empty = sum(1 for n in neighbors if board[n] == '')
        opp_count = sum(1 for n in neighbors if board[n] == opp)
        friendly = sum(1 for n in neighbors if board[n] == color)
        
        return empty == 0 and opp_count > friendly
    
    def _evaluate_placement(self, board, spot, color, opp):
        score = 0
        
        if spot in self.crossroads:
            score += 50
        elif spot in self.t_junctions:
            score += 25
        else:
            score += 10
        
        sim_board = self._simulate_placement(board, spot, color, opp)
        
        for n in ADJACENCY[spot]:
            if board[n] == opp and sim_board[n] == '':
                score += 100
        
        for s in range(24):
            if board[s] == color and sim_board[s] == '':
                score -= 80
        
        friendly = sum(1 for n in ADJACENCY[spot] if board[n] == color)
        score += friendly * 25
        
        for n in ADJACENCY[spot]:
            if board[n] == opp:
                enemy_neighbors = ADJACENCY[n]
                my_count = sum(1 for en in enemy_neighbors if en == spot or board[en] == color)
                empty_count = sum(1 for en in enemy_neighbors if board[en] == '' and en != spot)
                
                if n in self.corners:
                    if my_count >= 2:
                        score += 45
                    elif my_count == 1 and empty_count == 0:
                        score += 30
                elif n in self.t_junctions and my_count >= 3:
                    score += 35
        
        empty_neighbors = sum(1 for n in ADJACENCY[spot] if board[n] == '')
        opp_neighbors = sum(1 for n in ADJACENCY[spot] if board[n] == opp)
        
        if empty_neighbors == 1 and opp_neighbors > friendly:
            score -= 30
        
        return score
    
    def _evaluate_board(self, board, color, opp):
        score = 0
        
        my_pieces = sum(1 for s in range(24) if board[s] == color)
        opp_pieces = sum(1 for s in range(24) if board[s] == opp)
        
        score += (my_pieces - opp_pieces) * 150
        
        my_moves = len(self._get_legal_moves(board, color))
        opp_moves = len(self._get_legal_moves(board, opp))
        score += (my_moves - opp_moves) * 30
        
        if opp_moves == 0 and opp_pieces > 0:
            score += 1000
        if my_moves == 0 and my_pieces > 0:
            score -= 1000
        
        for spot in range(24):
            if board[spot] == color:
                if spot in self.crossroads:
                    score += 35
                elif spot in self.t_junctions:
                    score += 18
                
                empty = sum(1 for n in ADJACENCY[spot] if board[n] == '')
                score += empty * 15
                
                opp_n = sum(1 for n in ADJACENCY[spot] if board[n] == opp)
                friendly = sum(1 for n in ADJACENCY[spot] if board[n] == color)
                if empty == 0 and opp_n > friendly:
                    score -= 80
                elif empty == 1 and opp_n > friendly:
                    score -= 25
        
        return score
