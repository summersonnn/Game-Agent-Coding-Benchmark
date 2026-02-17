"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3.5-plus-02-15
Run: 1
Generated: 2026-02-16 18:46:09
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

    def _get_neighbors(self, spot):
        return self.ADJACENCY.get(spot, [])

    def _is_overwhelmed(self, spot, board):
        if board[spot] == '':
            return False
        neighbors = self._get_neighbors(spot)
        empty_count = 0
        friendly_count = 0
        opponent_count = 0
        piece = board[spot]
        
        for n in neighbors:
            val = board[n]
            if val == '':
                empty_count += 1
            elif val == piece:
                friendly_count += 1
            else:
                opponent_count += 1
        
        if empty_count > 0:
            return False
        return opponent_count > friendly_count

    def _simulate_captures(self, board, active_spot, mover_color):
        new_board = list(board)
        
        # 1. Active Piece Suicide Check
        if active_spot is not None and new_board[active_spot] != '':
            if self._is_overwhelmed(active_spot, new_board):
                new_board[active_spot] = ''
                return new_board 
        
        # 2. Universal Capture Sweep
        # 2a. Friendly pieces first
        friendly_to_die = []
        for i in range(24):
            if new_board[i] == mover_color:
                if self._is_overwhelmed(i, new_board):
                    friendly_to_die.append(i)
        
        for i in friendly_to_die:
            new_board[i] = ''
            
        # 2b. Enemy pieces (re-check after friendly removals)
        enemy_to_die = []
        for i in range(24):
            if new_board[i] == self.opp_color:
                if self._is_overwhelmed(i, new_board):
                    enemy_to_die.append(i)
        
        for i in enemy_to_die:
            new_board[i] = ''
            
        return new_board

    def _count_pieces(self, board, color):
        return sum(1 for x in board if x == color)

    def _count_mobility(self, board, color):
        moves = 0
        for i in range(24):
            if board[i] == color:
                for n in self._get_neighbors(i):
                    if board[n] == '':
                        moves += 1
        return moves

    def _evaluate_board(self, board):
        my_pieces = self._count_pieces(board, self.color)
        opp_pieces = self._count_pieces(board, self.opp_color)
        
        if my_pieces == 0:
            return -1000
        if opp_pieces == 0:
            return 1000
            
        my_mobility = self._count_mobility(board, self.color)
        opp_mobility = self._count_mobility(board, self.opp_color)
        
        if my_mobility == 0:
            return -500
        if opp_mobility == 0:
            return 500
            
        score = (my_pieces - opp_pieces) * 10
        score += (my_mobility - opp_mobility) * 1
        
        crossroads = [4, 10, 13, 19]
        for i in crossroads:
            if board[i] == self.color:
                score += 1
            elif board[i] == self.opp_color:
                score -= 1
                
        return score

    def _is_repetition(self, board, history):
        target = (tuple(board), self.opp_color)
        count = 0
        for h in history:
            if h == target:
                count += 1
        return count >= 2

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        history = state.get("history", [])

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0 
            
            best_spot = None
            best_score = -float('inf')
            
            random.shuffle(empty_spots)
            
            for spot in empty_spots:
                temp_board = list(board)
                temp_board[spot] = self.color
                resolved_board = self._simulate_captures(temp_board, spot, self.color)
                
                if self._is_repetition(resolved_board, history):
                    score = -100 
                else:
                    score = self._evaluate_board(resolved_board)
                
                if resolved_board[spot] == '':
                    score -= 50 
                
                if score > best_score:
                    best_score = score
                    best_spot = spot
            
            return best_spot if best_spot is not None else empty_spots[0]

        else: 
            moves = []
            for spot in range(24):
                if board[spot] != self.color:
                    continue
                for neighbor in self._get_neighbors(spot):
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
            
            if not moves:
                return (0, 1) 
            
            best_move = None
            best_score = -float('inf')
            
            random.shuffle(moves)
            
            for from_spot, to_spot in moves:
                temp_board = list(board)
                temp_board[from_spot] = ''
                temp_board[to_spot] = self.color
                
                resolved_board = self._simulate_captures(temp_board, to_spot, self.color)
                
                if self._is_repetition(resolved_board, history):
                    score = -100
                else:
                    score = self._evaluate_board(resolved_board)
                
                if resolved_board[to_spot] == '':
                    score -= 50
                
                my_before = self._count_pieces(board, self.color)
                my_after = self._count_pieces(resolved_board, self.color)
                opp_before = self._count_pieces(board, self.opp_color)
                opp_after = self._count_pieces(resolved_board, self.opp_color)
                
                piece_diff = (my_after - opp_after) - (my_before - opp_before)
                score += piece_diff * 20
                
                if score > best_score:
                    best_score = score
                    best_move = (from_spot, to_spot)
            
            return best_move if best_move is not None else moves[0]
