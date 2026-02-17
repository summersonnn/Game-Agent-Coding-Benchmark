"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3.5-plus-02-15
Run: 2
Generated: 2026-02-16 18:46:09
"""

from typing import Optional

import random
from typing import Optional

class SurroundMorrisAgent:
    # Adjacency map included for isolation as per requirements
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
        self.opponent_color = 'W' if color == 'B' else 'B'

    def _get_neighbors(self, spot):
        return self.ADJACENCY.get(spot, [])

    def _is_overwhelmed(self, spot, board):
        """
        Checks if a piece at 'spot' is overwhelmed on the given 'board'.
        Rule: 0 empty neighbors AND opponent_neighbors > friendly_neighbors.
        """
        piece = board[spot]
        if not piece:
            return False
        neighbors = self._get_neighbors(spot)
        empty_count = 0
        friendly_count = 0
        enemy_count = 0
        
        for n in neighbors:
            val = board[n]
            if val == '':
                empty_count += 1
            elif val == piece:
                friendly_count += 1
            else:
                enemy_count += 1
        
        if empty_count > 0:
            return False
        return enemy_count > friendly_count

    def _simulate_captures(self, board, active_spot=None, my_color='B', opp_color='W'):
        """
        Simulates the capture logic after a move.
        Returns a list of spots that are captured.
        """
        captured = []
        
        # 1. Active Piece Suicide Check
        if active_spot is not None and 0 <= active_spot < 24:
            if self._is_overwhelmed(active_spot, board):
                # Active piece dies immediately, no other captures occur
                return [active_spot]
        
        # 2. Universal Capture Sweep (Self-Harm Priority)
        # 2a. Find overwhelmed friendlies
        friendlies_to_die = []
        for i in range(24):
            if board[i] == my_color:
                if i == active_spot: continue 
                if self._is_overwhelmed(i, board):
                    friendlies_to_die.append(i)
        
        # Create temp board with friendlies removed to check enemies
        temp_board = list(board)
        for spot in friendlies_to_die:
            temp_board[spot] = ''
            
        # 2b. Find overwhelmed enemies on the modified board
        enemies_to_die = []
        for i in range(24):
            if temp_board[i] == opp_color:
                if self._is_overwhelmed(i, temp_board):
                    enemies_to_die.append(i)
                    
        return friendlies_to_die + enemies_to_die

    def _count_legal_moves(self, board, color):
        count = 0
        for i in range(24):
            if board[i] == color:
                for n in self._get_neighbors(i):
                    if board[n] == '':
                        count += 1
        return count

    def make_move(self, state: dict, feedback: Optional[dict] = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        history = state.get("history", [])
        
        # Update internal color tracking to match state
        self.color = color
        self.opponent_color = opp

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0 

            best_spot = None
            best_score = -float('inf')
            random.shuffle(empty_spots)

            for spot in empty_spots:
                temp_board = list(board)
                temp_board[spot] = color
                
                # Check captures
                captured = self._simulate_captures(temp_board, active_spot=spot, my_color=color, opp_color=opp)
                
                final_board = list(temp_board)
                for c in captured:
                    final_board[c] = ''
                
                my_count = final_board.count(color)
                opp_count = final_board.count(opp)
                
                # Base score: material difference
                score = (my_count - opp_count) * 100
                
                # Penalty for Suicide (Active piece captured)
                if spot in captured:
                    score -= 500 
                
                # Penalty for Friendly Fire (Other friendlies captured)
                friendlies_killed = [c for c in captured if temp_board[c] == color]
                score -= len(friendlies_killed) * 200
                
                # Bonus for Enemy Kills
                enemies_killed = [c for c in captured if temp_board[c] == opp]
                score += len(enemies_killed) * 200
                
                # Position Heuristic (Centers 4, 10, 13, 19 are valuable)
                if spot in [4, 10, 13, 19]:
                    score += 10
                
                if score > best_score:
                    best_score = score
                    best_spot = spot
            
            return best_spot if best_spot is not None else empty_spots[0]

        else: # Movement
            moves = []
            for spot in range(24):
                if board[spot] != color:
                    continue
                for neighbor in self._get_neighbors(spot):
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
            
            if not moves:
                return (0, 1) 

            best_move = None
            best_score = -float('inf')
            random.shuffle(moves)
            
            # Current material balance to decide on repetition strategy
            current_my_pieces = board.count(color)
            current_opp_pieces = board.count(opp)
            am_ahead = current_my_pieces > current_opp_pieces

            for from_spot, to_spot in moves:
                temp_board = list(board)
                temp_board[to_spot] = color
                temp_board[from_spot] = ''
                
                captured = self._simulate_captures(temp_board, active_spot=to_spot, my_color=color, opp_color=opp)
                
                final_board = list(temp_board)
                for c in captured:
                    final_board[c] = ''
                
                my_count = final_board.count(color)
                opp_count = final_board.count(opp)
                
                score = (my_count - opp_count) * 100
                
                # Suicide penalty
                if to_spot in captured:
                    score -= 500
                
                # Friendly fire penalty
                friendlies_killed = [c for c in captured if temp_board[c] == color and c != from_spot]
                score -= len(friendlies_killed) * 200
                
                # Enemy kill bonus
                enemies_killed = [c for c in captured if temp_board[c] == opp]
                score += len(enemies_killed) * 200
                
                # Mobility
                my_moves = self._count_legal_moves(final_board, color)
                opp_moves = self._count_legal_moves(final_board, opp)
                score += (my_moves - opp_moves) * 5
                
                # Repetition Check (Movement Phase Only)
                # Next state will be opponent's turn
                board_tuple = tuple(final_board)
                next_player = opp
                rep_count = sum(1 for h_b, h_p in history if h_b == board_tuple and h_p == next_player)
                
                if rep_count >= 2:
                    if am_ahead:
                        score -= 10000 # Avoid draw if winning
                    else:
                        score += 10000 # Force draw if losing
                elif rep_count == 1:
                    score -= 100 # Slight penalty to avoid approaching 3-fold
                
                if score > best_score:
                    best_score = score
                    best_move = (from_spot, to_spot)
            
            return best_move if best_move else moves[0]
