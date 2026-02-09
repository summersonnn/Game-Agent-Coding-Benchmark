"""
Agent Code: A8-SurroundMorris
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-09 19:15:26
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
    
    def count_neighbors(self, spot, board):
        """Count empty, friendly, and opponent neighbors."""
        empty = 0
        friendly = 0
        opp = 0
        for n in ADJACENCY[spot]:
            val = board[n]
            if val == '':
                empty += 1
            elif val == self.color:
                friendly += 1
            else:
                opp += 1
        return empty, friendly, opp
    
    def is_captured(self, spot, board, piece_color):
        """Check if piece at spot would be captured."""
        empty, friendly, opp = self.count_neighbors(spot, board)
        if empty > 0:
            return False
        if piece_color == self.color:
            return opp > friendly
        else:
            # Opponent perspective: their friends are our opponents
            return friendly > opp
    
    def simulate_captures(self, board, active_spot, is_placement):
        """Simulate capture resolution. Returns (friendlies_lost, enemies_lost)."""
        # Check active piece suicide first
        if self.is_captured(active_spot, board, self.color):
            return (1, 0) if is_placement else (0, 0)  # In placement we lose the piece, in movement suicide is prevented
        
        # Step 2a: Check friendly casualties (excluding active piece)
        friendlies_lost = 0
        temp_board = list(board)
        
        for i in range(24):
            if temp_board[i] == self.color and i != active_spot:
                if self.is_captured(i, temp_board, self.color):
                    friendlies_lost += 1
                    temp_board[i] = ''
        
        # Step 2b: Check enemy casualties
        enemies_lost = 0
        opp_color = 'W' if self.color == 'B' else 'B'
        for i in range(24):
            if temp_board[i] == opp_color:
                if self.is_captured(i, temp_board, opp_color):
                    enemies_lost += 1
        
        return friendlies_lost, enemies_lost
    
    def make_move(self, state, feedback=None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp_color = state["opponent_color"]
        
        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0
            
            candidates = []
            for spot in empty_spots:
                # Simulate placement
                test_board = list(board)
                test_board[spot] = color
                
                # Evaluate
                friendlies_lost, enemies_lost = self.simulate_captures(test_board, spot, True)
                
                # Skip suicide moves unless forced
                if friendlies_lost > 0 and test_board[spot] == '':
                    continue
                
                score = enemies_lost * 100 - friendlies_lost * 90
                
                # Positional bonus: prefer high connectivity
                score += len(ADJACENCY[spot]) * 5
                
                # Penalty for corners (easier to trap)
                if len(ADJACENCY[spot]) == 2:
                    score -= 3
                
                candidates.append((score, spot))
            
            # If all moves are suicidal, pick least bad
            if not candidates:
                # Pick spot with most neighbors to make it harder to capture
                return max(empty_spots, key=lambda s: len(ADJACENCY[s]))
            
            # Pick best
            candidates.sort(reverse=True)
            best_score = candidates[0][0]
            best_spots = [s for sc, s in candidates if sc == best_score]
            return random.choice(best_spots)
        
        else:  # movement phase
            # Generate legal moves
            moves = []
            for spot in range(24):
                if board[spot] == color:
                    for n in ADJACENCY[spot]:
                        if board[n] == '':
                            moves.append((spot, n))
            
            if not moves:
                return (0, 0)  # No legal moves, should not reach here (mate ends game)
            
            candidates = []
            for from_spot, to_spot in moves:
                # Simulate move
                test_board = list(board)
                test_board[from_spot] = ''
                test_board[to_spot] = color
                
                # Check suicide
                if self.is_captured(to_spot, test_board, color):
                    continue  # Skip suicidal moves
                
                friendlies_lost, enemies_lost = self.simulate_captures(test_board, to_spot, False)
                
                score = enemies_lost * 100 - friendlies_lost * 80
                
                # Mobility bonus: prefer squares with more escape routes
                empty_to, _, _ = self.count_neighbors(to_spot, test_board)
                score += empty_to * 10
                
                # Slight preference for keeping pieces away from corners
                if len(ADJACENCY[to_spot]) == 2:
                    score -= 5
                
                # Prefer moves that don't reduce our mobility
                empty_from, _, _ = self.count_neighbors(from_spot, board)
                if empty_from == 0:
                    # Moving from a trapped piece, good!
                    score += 20
                
                candidates.append((score, from_spot, to_spot))
            
            if not candidates:
                # All moves suicidal or no good options, pick any legal move
                return random.choice(moves)
            
            candidates.sort(reverse=True)
            best_score = candidates[0][0]
            best_moves = [(f, t) for sc, f, t in candidates if sc == best_score]
            return random.choice(best_moves)
