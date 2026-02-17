"""
Agent Code: A8-SurroundMorris
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 1
Generated: 2026-02-17 14:26:05
"""



import random

class SurroundMorrisAgent:
    """
    Agent for Surround Morris game.
    Uses heuristic evaluation with lookahead for both placement and movement phases.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opponent_color = 'B' if color == 'W' else 'W'
        
    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        if phase == "placement":
            return self._placement_move(board, state)
        else:
            return self._movement_move(board, state)
    
    def _placement_move(self, board, state):
        """Choose a placement spot using heuristic evaluation."""
        empty_spots = [i for i in range(24) if board[i] == '']
        if not empty_spots:
            return 0  # Should never happen in valid game state
        
        # Evaluate each empty spot
        best_score = float('-inf')
        best_spot = random.choice(empty_spots)  # Default random
        
        for spot in empty_spots:
            score = self._evaluate_placement(board, spot, state)
            if score > best_score:
                best_score = score
                best_spot = spot
        
        return best_spot
    
    def _movement_move(self, board, state):
        """Choose a movement using heuristic evaluation with lookahead."""
        legal_moves = self._get_legal_moves(board, self.color)
        if not legal_moves:
            # No legal moves - we are mated, but must return something
            return (0, 1)  # Will be invalid, but engine will handle
        
        # Evaluate each move
        best_score = float('-inf')
        best_move = random.choice(legal_moves)
        
        for move in legal_moves:
            score = self._evaluate_move(board, move, state)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _evaluate_placement(self, board, spot, state):
        """Evaluate a placement spot."""
        score = 0
        
        # 1. Position value (central spots are better)
        central_spots = [4, 10, 13, 19]  # Crossroads (4 neighbors)
        t_junctions = [1, 3, 5, 7, 8, 11, 12, 14, 15, 17, 18, 20, 21, 22]  # T-junctions (3 neighbors)
        corners = [0, 2, 6, 9, 15, 17, 21, 23]  # Actually 2 neighbors, but let's use this list
        
        if spot in central_spots:
            score += 10
        elif spot in t_junctions:
            score += 5
        elif spot in corners:
            score += 2
        
        # 2. Check for immediate suicide (bad)
        if self._is_suicide_placement(board, spot, self.color):
            score -= 100  # Strongly discourage suicide
        
        # 3. Check if placement captures opponent pieces
        temp_board = board.copy()
        temp_board[spot] = self.color
        captured = self._get_captured_pieces(temp_board, spot, self.color)
        score += len([p for p in captured if temp_board[p] == self.opponent_color]) * 15
        
        # 4. Check if placement blocks opponent's potential captures
        # (simplified: count opponent pieces near this spot)
        opponent_nearby = 0
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == self.opponent_color:
                opponent_nearby += 1
        score += opponent_nearby * 3  # Blocking opponent is good
        
        # 5. Check if placement creates friendly clusters (but avoid over-clustering)
        friendly_nearby = 0
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == self.color:
                friendly_nearby += 1
        score += friendly_nearby * 2  # Slight bonus for friendly neighbors
        
        return score
    
    def _evaluate_move(self, board, move, state):
        """Evaluate a movement with lookahead."""
        from_spot, to_spot = move
        
        # 1. Basic move evaluation
        score = 0
        
        # Move towards center is generally good
        if to_spot in [4, 10, 13, 19]:
            score += 5
        elif to_spot in ADJACENCY[4] + ADJACENCY[10] + ADJACENCY[13] + ADJACENCY[19]:
            score += 3
        
        # 2. Simulate the move and evaluate resulting state
        temp_board = board.copy()
        temp_board[from_spot] = ''
        temp_board[to_spot] = self.color
        
        # 3. Check captures that would happen
        captured = self._get_captured_pieces(temp_board, to_spot, self.color)
        
        # Count captures (prioritize capturing opponent pieces)
        opp_captured = len([p for p in captured if temp_board[p] == self.opponent_color])
        friendly_captured = len([p for p in captured if temp_board[p] == self.color])
        
        score += opp_captured * 20  # Capturing opponent is very good
        score -= friendly_captured * 25  # Losing own pieces is bad
        
        # 4. Check if move creates threats for opponent
        threat_score = self._evaluate_threats(temp_board, to_spot)
        score += threat_score
        
        # 5. Mobility: ensure we don't reduce our own mobility too much
        current_mobility = len(self._get_legal_moves(board, self.color))
        new_mobility = len(self._get_legal_moves(temp_board, self.color))
        mobility_diff = new_mobility - current_mobility
        score += mobility_diff * 2
        
        # 6. Check for repetition avoidance
        if self._would_cause_repetition(temp_board, state):
            score -= 50  # Avoid repeating positions
        
        return score
    
    def _is_suicide_placement(self, board, spot, color):
        """Check if placing at spot would cause immediate suicide."""
        # Temporarily place the piece
        temp_board = board.copy()
        temp_board[spot] = color
        
        # Check if the placed piece would be captured immediately
        return self._is_captured(spot, temp_board, color)
    
    def _get_captured_pieces(self, board, active_spot, mover_color):
        """Get all pieces that would be captured after a move."""
        captured = []
        
        # Step 1: Check active piece
        if self._is_captured(active_spot, board, mover_color):
            captured.append(active_spot)
            return captured  # Active piece dies, no further captures
        
        # Step 2: Check all friendly pieces (self-harm priority)
        opp_color = self.opponent_color if mover_color == self.color else self.color
        friendly_captured = []
        for spot in range(24):
            if board[spot] == mover_color and self._is_captured(spot, board, mover_color):
                friendly_captured.append(spot)
        
        # Remove friendly pieces first
        temp_board = board.copy()
        for spot in friendly_captured:
            temp_board[spot] = ''
        
        # Step 3: Check enemy pieces after friendly removal
        enemy_captured = []
        for spot in range(24):
            if temp_board[spot] == opp_color and self._is_captured(spot, temp_board, opp_color):
                enemy_captured.append(spot)
        
        return friendly_captured + enemy_captured
    
    def _is_captured(self, spot, board, color):
        """Check if a piece at spot would be captured."""
        if board[spot] == '':
            return False
        
        empty_neighbors = 0
        friendly_neighbors = 0
        opponent_neighbors = 0
        
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty_neighbors += 1
            elif board[neighbor] == color:
                friendly_neighbors += 1
            else:
                opponent_neighbors += 1
        
        return (empty_neighbors == 0) and (opponent_neighbors > friendly_neighbors)
    
    def _get_legal_moves(self, board, color):
        """Get all legal moves for a color."""
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    moves.append((spot, neighbor))
        return moves
    
    def _evaluate_threats(self, board, moved_spot):
        """Evaluate threats created by the move."""
        score = 0
        
        # Check if the moved piece threatens opponent pieces
        for neighbor in ADJACENCY[moved_spot]:
            if board[neighbor] == self.opponent_color:
                # Check if this opponent piece is now in danger
                if self._is_captured(neighbor, board, self.opponent_color):
                    score += 10  # Direct threat
        
        # Check if we blocked opponent's escape routes
        for spot in range(24):
            if board[spot] == self.opponent_color:
                empty_neighbors = 0
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        empty_neighbors += 1
                if empty_neighbors == 1:  # About to be trapped
                    score += 5
        
        return score
    
    def _would_cause_repetition(self, new_board, state):
        """Check if the move would cause a 3-fold repetition."""
        # Create new state tuple
        new_state_tuple = (tuple(new_board), self.opponent_color)  # Next player is opponent
        
        # Count occurrences in history
        count = state['history'].count(new_state_tuple)
        return count >= 2  # Would be 3rd occurrence

# Global adjacency dictionary (provided by the game engine)
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
