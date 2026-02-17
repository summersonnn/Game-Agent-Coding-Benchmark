"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3.5-397b-a17b
Run: 4
Generated: 2026-02-16 17:46:27
"""

import random

class SurroundMorrisAgent:
    """
    Agent for Surround Morris.
    """
    # Board adjacency map
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
        self.opp = 'W' if color == 'B' else 'B'

    def _get_neighbors(self, spot):
        return self.ADJACENCY.get(spot, [])

    def _check_piece_captured(self, board, spot):
        """Returns True if piece at spot is captured."""
        piece = board[spot]
        if not piece:
            return False
        
        friends = 0
        opponents = 0
        empty = 0
        
        for n in self._get_neighbors(spot):
            neighbor_piece = board[n]
            if neighbor_piece == '':
                empty += 1
            elif neighbor_piece == piece:
                friends += 1
            else:
                opponents += 1
        
        # Capture condition: 0 empty AND opponents > friends
        if empty == 0 and opponents > friends:
            return True
        return False

    def _simulate_captures(self, board, active_spot, active_color):
        """
        Simulates the capture logic on a copy of the board.
        Returns the new board state.
        """
        new_board = list(board)
        
        # 1. Active Piece Suicide Check
        if active_spot is not None and 0 <= active_spot < 24:
            if new_board[active_spot] == active_color:
                if self._check_piece_captured(new_board, active_spot):
                    new_board[active_spot] = ''
                    return new_board # Turn ends immediately
        
        # 2. Universal Capture Sweep
        # 2a. Friendly pieces (excluding active as it survived)
        friendlies_to_remove = []
        for i in range(24):
            if new_board[i] == active_color:
                if i == active_spot: continue 
                if self._check_piece_captured(new_board, i):
                    friendlies_to_remove.append(i)
        
        for i in friendlies_to_remove:
            new_board[i] = ''
            
        # 2b. Enemy pieces (Re-check after friendly removals)
        enemies_to_remove = []
        for i in range(24):
            if new_board[i] == self.opp:
                if self._check_piece_captured(new_board, i):
                    enemies_to_remove.append(i)
        
        for i in enemies_to_remove:
            new_board[i] = ''
            
        return new_board

    def _count_legal_moves(self, board, color):
        count = 0
        for i in range(24):
            if board[i] == color:
                for n in self._get_neighbors(i):
                    if board[n] == '':
                        count += 1
        return count

    def _get_repetition_count(self, history, board_tuple, next_player):
        count = 0
        target = (board_tuple, next_player)
        for h in history:
            if h == target:
                count += 1
        return count

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = self.color
        opp = self.opp
        history = state.get("history", [])
        
        my_pieces = state["pieces_on_board"][color]
        opp_pieces = state["pieces_on_board"][opp]
        is_winning = my_pieces > opp_pieces

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0 
            
            best_spot = None
            best_score = -float('inf')
            
            random.shuffle(empty_spots)
            
            for spot in empty_spots:
                sim_board = list(board)
                sim_board[spot] = color
                
                final_board = self._simulate_captures(sim_board, spot, color)
                
                score = 0
                
                # Penalty for Suicide
                if final_board[spot] == '':
                    score -= 10000 
                
                # Piece Count Change
                init_friends = sum(1 for x in board if x == color)
                init_enemies = sum(1 for x in board if x == opp)
                
                final_friends = sum(1 for x in final_board if x == color)
                final_enemies = sum(1 for x in final_board if x == opp)
                
                friends_lost = init_friends - final_friends
                enemies_lost = init_enemies - final_enemies
                
                score += enemies_lost * 1000
                score -= friends_lost * 500
                
                # Mobility
                mobility = self._count_legal_moves(final_board, color)
                score += mobility * 10
                
                # Centrality
                degree = len(self._get_neighbors(spot))
                score += degree * 5
                
                # Repetition
                rep_count = self._get_repetition_count(history, tuple(final_board), opp)
                if rep_count >= 2:
                    if is_winning:
                        score -= 5000
                    else:
                        score += 5000
                
                if score > best_score:
                    best_score = score
                    best_spot = spot
            
            return best_spot if best_spot is not None else empty_spots[0]

        else: # Movement Phase
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
            
            for from_spot, to_spot in moves:
                sim_board = list(board)
                sim_board[from_spot] = ''
                sim_board[to_spot] = color
                
                final_board = self._simulate_captures(sim_board, to_spot, color)
                
                score = 0
                
                # Penalty for Suicide
                if final_board[to_spot] == '':
                    score -= 10000
                
                # Piece Count Change
                init_friends = sum(1 for x in board if x == color)
                init_enemies = sum(1 for x in board if x == opp)
                
                final_friends = sum(1 for x in final_board if x == color)
                final_enemies = sum(1 for x in final_board if x == opp)
                
                friends_lost = init_friends - final_friends
                enemies_lost = init_enemies - final_enemies
                
                score += enemies_lost * 1000
                score -= friends_lost * 500
                
                # Mobility
                mobility = self._count_legal_moves(final_board, color)
                score += mobility * 10
                
                # Centrality
                degree = len(self._get_neighbors(to_spot))
                score += degree * 2
                
                # Repetition
                rep_count = self._get_repetition_count(history, tuple(final_board), opp)
                if rep_count >= 2:
                    if is_winning:
                        score -= 5000
                    else:
                        score += 5000
                
                if score > best_score:
                    best_score = score
                    best_move = (from_spot, to_spot)
            
            return best_move if best_move else moves[0]