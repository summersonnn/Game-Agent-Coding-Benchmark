"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-coder-next
Run: 1
Generated: 2026-02-09 19:15:26
"""

from collections import Counter

import random
from collections import Counter

# ADJACENCY is provided as a global at runtime, but we define it here for reference
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
        move_count = state["move_count"]
        history = state["history"]

        # Handle feedback from previous attempts
        if feedback is not None:
            # If we got an error, we should try a different move
            # For simplicity, we'll just recompute with slight variation
            pass

        if phase == "placement":
            # Get all empty spots
            empty_spots = [i for i in range(24) if board[i] == '']
            
            if not empty_spots:
                # Shouldn't happen in normal play, but fallback
                return 0

            # Prefer central spots (4, 10, 13, 19) for control
            central_spots = [4, 10, 13, 19]
            preferred = [s for s in empty_spots if s in central_spots]
            
            # Try to avoid suicide placements (but suicide is legal)
            # We'll check if placing at spot would immediately get captured
            safe_moves = []
            for spot in empty_spots:
                # Simulate placement
                temp_board = board.copy()
                temp_board[spot] = color
                
                # Check if this placement would kill the placed piece immediately
                if not self._is_captured_spot(spot, temp_board, color, opp):
                    safe_moves.append(spot)
            
            # If we have safe moves, prefer them
            if safe_moves:
                # Try to pick a safe move that also disrupts opponent or creates potential mills
                # Simple heuristic: avoid corners if opponent has pieces nearby
                # For now, just pick the best safe move
                if preferred:
                    # Try to find a preferred safe move
                    preferred_safe = [s for s in preferred if s in safe_moves]
                    if preferred_safe:
                        return random.choice(preferred_safe)
                return random.choice(safe_moves)
            else:
                # No safe moves - suicide is allowed but bad. Pick randomly.
                return random.choice(empty_spots)
        else:
            # Movement phase
            # Find all legal moves: from own piece to adjacent empty spot
            moves = []
            for spot in range(24):
                if board[spot] == color:
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == '':
                            moves.append((spot, neighbor))
            
            if not moves:
                # No moves available - will lose, but still need to return something
                return (0, 1)
            
            # Evaluate moves
            best_moves = []
            best_score = float('-inf')
            
            for move in moves:
                from_spot, to_spot = move
                
                # Simulate the move
                temp_board = board.copy()
                temp_board[from_spot] = ''
                temp_board[to_spot] = color
                
                # Check if the moved piece commits suicide
                if self._is_captured_spot(to_spot, temp_board, color, opp):
                    # Suicide move - avoid unless desperate
                    continue
                
                # Check if move causes friendly fire (capturing own pieces)
                # First, check if any friendly pieces get captured (self-harm priority)
                friendly_captured = self._get_captured_friendly_spots(temp_board, color, opp)
                
                # If friendly pieces are captured, this move might be bad
                if friendly_captured:
                    # Only consider if we can't find better moves
                    continue
                
                # Check if move captures enemy pieces
                enemy_captured = self._get_captured_enemy_spots(temp_board, color, opp)
                
                # Score the move
                score = 0
                score += len(enemy_captured) * 10  # Capturing enemies is good
                
                # Prefer moves that don't leave the moved piece vulnerable
                if self._is_vulnerable(to_spot, temp_board, color, opp):
                    score -= 5
                
                # Prefer moves that preserve escape routes (keep empty neighbors)
                empty_neighbors = sum(1 for n in ADJACENCY[to_spot] if temp_board[n] == '')
                score += empty_neighbors  # More empty neighbors is better
                
                # Prefer central positions
                if to_spot in [4, 10, 13, 19]:
                    score += 3
                
                # Avoid corners if opponent has many pieces nearby
                if to_spot in [0, 2, 8, 14, 15, 17, 21, 23]:
                    opp_neighbors = sum(1 for n in ADJACENCY[to_spot] if temp_board[n] == opp)
                    if opp_neighbors > 1:
                        score -= 5
                
                # Check for potential mate of opponent after this move
                # (i.e., check if opponent has no moves after this move)
                if self._check_mate(temp_board, opp):
                    score += 50  # Big bonus for mate
                
                # Avoid repetition - check if this state has been seen before
                board_tuple = tuple(temp_board)
                player = color  # After move, it's opponent's turn
                history_state = (board_tuple, opp)
                if history_state in history:
                    score -= 20  # Penalty for repetition
                
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            
            # If no good moves found, fall back to random legal move
            if best_moves:
                return random.choice(best_moves)
            else:
                return random.choice(moves)
    
    def _is_captured_spot(self, spot, board, color, opp):
        """Check if piece at spot should be captured based on Surround Morris rules."""
        neighbors = ADJACENCY[spot]
        empty_neighbors = sum(1 for n in neighbors if board[n] == '')
        if empty_neighbors > 0:
            return False
        
        friendly_neighbors = sum(1 for n in neighbors if board[n] == color)
        opponent_neighbors = sum(1 for n in neighbors if board[n] == opp)
        
        return opponent_neighbors > friendly_neighbors
    
    def _get_captured_friendly_spots(self, board, color, opp):
        """Get list of friendly spots that would be captured (self-harm priority)."""
        captured = []
        for spot in range(24):
            if board[spot] == color:
                if self._is_captured_spot(spot, board, color, opp):
                    captured.append(spot)
        return captured
    
    def _get_captured_enemy_spots(self, board, color, opp):
        """Get list of enemy spots that would be captured (after friendly captures are processed)."""
        # First, determine which friendly spots would be captured
        friendly_captured = self._get_captured_friendly_spots(board, color, opp)
        
        # Create a board state after removing captured friendly pieces
        temp_board = board.copy()
        for spot in friendly_captured:
            temp_board[spot] = ''
        
        # Now check which enemy pieces would be captured in this updated state
        captured = []
        for spot in range(24):
            if temp_board[spot] == opp:
                if self._is_captured_spot(spot, temp_board, color, opp):
                    captured.append(spot)
        return captured
    
    def _is_vulnerable(self, spot, board, color, opp):
        """Check if a piece at spot is vulnerable to capture in the next turn."""
        # Check if placing an opponent piece at an adjacent spot would capture it
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                # Simulate opponent placing there
                temp_board = board.copy()
                temp_board[neighbor] = opp
                
                # Check if the piece at spot is captured
                if self._is_captured_spot(spot, temp_board, color, opp):
                    return True
        return False
    
    def _check_mate(self, board, color):
        """Check if player with given color has no legal moves."""
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        return False
        return True
