"""
Agent Code: A8-SurroundMorris
Model: anthropic/claude-sonnet-4.5
Run: 2
Generated: 2026-02-09 19:15:26
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
    
    def make_move(self, state: dict, feedback: dict | None = None):
        phase = state["phase"]
        
        if phase == "placement":
            return self.choose_placement(state)
        else:
            return self.choose_movement(state)
    
    def is_piece_captured(self, spot, board):
        """Check if piece at spot meets capture criteria"""
        if board[spot] == '':
            return False
        
        color = board[spot]
        empty = friendly = enemy = 0
        
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty += 1
            elif board[neighbor] == color:
                friendly += 1
            else:
                enemy += 1
        
        return empty == 0 and enemy > friendly
    
    def simulate_captures(self, board, active_spot, active_color):
        """Simulate capture logic: suicide first, then self-harm priority"""
        result = list(board)
        
        # Step 1: Suicide check
        if self.is_piece_captured(active_spot, result):
            result[active_spot] = ''
            return result
        
        # Step 2a: Remove friendly casualties
        for spot in range(24):
            if result[spot] == active_color and self.is_piece_captured(spot, result):
                result[spot] = ''
        
        # Step 2b: Remove enemy casualties
        opp_color = 'W' if active_color == 'B' else 'B'
        for spot in range(24):
            if result[spot] == opp_color and self.is_piece_captured(spot, result):
                result[spot] = ''
        
        return result
    
    def choose_placement(self, state):
        """Choose best placement spot"""
        board = state["board"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        empty = [i for i in range(24) if board[i] == '']
        if not empty:
            return 0
        
        scored = [(self.score_placement(spot, board, color, opp), spot) for spot in empty]
        best_score = max(s for s, _ in scored)
        best_spots = [spot for s, spot in scored if s == best_score]
        
        return random.choice(best_spots)
    
    def score_placement(self, spot, board, color, opp):
        """Evaluate placement move quality"""
        # Simulate placement and captures
        temp = list(board)
        temp[spot] = color
        final = self.simulate_captures(temp, spot, color)
        
        # Count material before and after
        our_before = sum(1 for s in board if s == color)
        our_after = sum(1 for s in final if s == color)
        opp_before = sum(1 for s in board if s == opp)
        opp_after = sum(1 for s in final if s == opp)
        
        score = 0
        
        # Suicide is catastrophic
        if final[spot] == '':
            return -100000
        
        # Material changes beyond just placing
        our_change = our_after - our_before - 1
        opp_casualties = opp_before - opp_after
        score += (our_change + opp_casualties) * 10000
        
        # Strategic position value (crossroads > T-junction > corner)
        neighbors = len(ADJACENCY[spot])
        score += {4: 50, 3: 30, 2: 15}[neighbors]
        
        # Connectivity to friendly pieces
        adjacent_friends = sum(1 for n in ADJACENCY[spot] if board[n] == color)
        score += adjacent_friends * 20
        
        # Maintain mobility (empty neighbors)
        empty_after = sum(1 for n in ADJACENCY[spot] if final[n] == '')
        score += empty_after * 5
        
        return score
    
    def choose_movement(self, state):
        """Choose best movement"""
        board = state["board"]
        color = state["your_color"]
        
        # Find all legal moves
        moves = []
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
        
        if not moves:
            return (0, 1)  # Fallback (should not happen if not mated)
        
        scored = [(self.score_movement(move, state), move) for move in moves]
        best_score = max(s for s, _ in scored)
        best_moves = [move for s, move in scored if s == best_score]
        
        return random.choice(best_moves)
    
    def score_movement(self, move, state):
        """Evaluate movement move quality"""
        from_spot, to_spot = move
        board = state["board"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        # Simulate move and captures
        temp = list(board)
        temp[to_spot] = color
        temp[from_spot] = ''
        final = self.simulate_captures(temp, to_spot, color)
        
        # Count material
        our_before = sum(1 for s in board if s == color)
        our_after = sum(1 for s in final if s == color)
        opp_before = sum(1 for s in board if s == opp)
        opp_after = sum(1 for s in final if s == opp)
        
        score = 0
        
        # Material swing is paramount (captures - losses)
        material_swing = (our_after - our_before) + (opp_before - opp_after)
        score += material_swing * 10000
        
        # Winning/losing conditions
        if opp_after == 0:
            score += 1000000
        if our_after == 0:
            score -= 1000000
        
        # Mobility (keep escape routes open)
        empty_neighbors = sum(1 for n in ADJACENCY[to_spot] if final[n] == '')
        score += empty_neighbors * 50
        
        # Strategic position value
        score += len(ADJACENCY[to_spot]) * 10
        
        # Avoid repetition when ahead, accept when behind
        history = state.get("history", [])
        if history:
            next_state = (tuple(final), opp)
            repetitions = sum(1 for h in history if h == next_state)
            
            if repetitions >= 2:
                if our_after > opp_after:
                    score -= 100000  # Ahead: avoid draw
                elif our_after < opp_after:
                    score += 50000   # Behind: draw is salvation
            elif repetitions == 1:
                score -= 1000  # Discourage repetition generally
        
        return score
