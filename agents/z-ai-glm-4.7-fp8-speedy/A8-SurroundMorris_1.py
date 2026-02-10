"""
Agent Code: A8-SurroundMorris
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-10 22:37:41
"""



import random

class SurroundMorrisAgent:
    """
    A strategic agent for Surround Morris.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.piece_values = {
            'crossroad': 4,  # Spots 4, 10, 13, 19
            't_junction': 2, # Spots 1, 3, 5, 7, 9, 11, 12, 14, 16, 17, 18, 20
            'corner': 1      # Spots 0, 2, 6, 8, 15, 21, 22, 23
        }
        self.spot_types = {
            0: 'corner', 1: 't_junction', 2: 'corner',
            3: 't_junction', 4: 'crossroad', 5: 't_junction',
            6: 'corner', 7: 't_junction', 8: 'corner',
            9: 't_junction', 10: 'crossroad', 11: 't_junction',
            12: 't_junction', 13: 'crossroad', 14: 't_junction',
            15: 'corner', 16: 't_junction', 17: 't_junction',
            18: 't_junction', 19: 'crossroad', 20: 't_junction',
            21: 'corner', 22: 'corner', 23: 'corner'
        }

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        my_color = state["your_color"]
        opp_color = state["opponent_color"]
        
        # Generate all legal moves
        if phase == "placement":
            legal_moves = [i for i in range(24) if board[i] == '']
        else:
            legal_moves = []
            for spot in range(24):
                if board[spot] == my_color:
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == '':
                            legal_moves.append((spot, neighbor))

        if not legal_moves:
            # Fallback if no moves (should be caught by engine as Mate, but safe to handle)
            return 0 if phase == "placement" else (0, 1)

        # Search for the best move using 1-ply simulation
        best_score = -float('inf')
        best_moves = []

        # Evaluate current state to determine if we are winning/losing for repetition logic
        current_material_diff = self.count_pieces(board, my_color) - self.count_pieces(board, opp_color)
        
        for move in legal_moves:
            # Simulate the move and capture resolution
            next_board, captured_enemies, captured_friendlies = self.simulate_move(board, move, phase, my_color)
            
            # Check for repetition draw
            # The next state will be (next_board, opp_color)
            next_state_key = (tuple(next_board), opp_color)
            history = state["history"]
            
            # Avoid 3-fold repetition
            if history.count(next_state_key) >= 2:
                # If we are winning, avoid draw heavily. If losing, maybe we want it, 
                # but for simplicity we treat draw as neutral/slightly negative unless desperate.
                # Here we just penalize it to avoid premature draws.
                continue

            # Evaluate the board
            score = self.evaluate(next_board, my_color, opp_color)
            
            # Add capture bonuses/penalties
            score += captured_enemies * 15
            score -= captured_friendlies * 15
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # If all moves lead to draw or we filtered everything, pick random from legal
        if not best_moves:
            return random.choice(legal_moves)
            
        return random.choice(best_moves)

    def simulate_move(self, board, move, phase, color):
        """Simulates a move and returns the resulting board state and capture counts."""
        new_board = list(board)
        opp_color = 'W' if color == 'B' else 'B'
        active_spot = None
        
        # 1. Apply Move
        if phase == "placement":
            active_spot = move
            new_board[active_spot] = color
        else:
            from_spot, to_spot = move
            new_board[from_spot] = ''
            new_board[to_spot] = color
            active_spot = to_spot
            
        captured_friendlies = 0
        captured_enemies = 0
        
        # 2. Active Piece Suicide Check
        if self.is_overwhelmed(new_board, active_spot, color):
            new_board[active_spot] = ''
            return new_board, 0, 1 # Active piece dies

        # 3. Universal Sweep (Self-Harm Priority)
        
        # Step 3a: Remove overwhelmed friendlies
        friendlies_to_remove = []
        for i in range(24):
            if new_board[i] == color:
                # Check if overwhelmed. 
                # Note: Active piece is checked again technically, but if it survived step 2 
                # and board hasn't changed, it's safe. But checking all is robust.
                if self.is_overwhelmed(new_board, i, color):
                    friendlies_to_remove.append(i)
        
        for i in friendlies_to_remove:
            new_board[i] = ''
            captured_friendlies += 1
            
        # Step 3b: Remove overwhelmed enemies (after friendlies removed)
        enemies_to_remove = []
        for i in range(24):
            if new_board[i] == opp_color:
                if self.is_overwhelmed(new_board, i, opp_color):
                    enemies_to_remove.append(i)
                    
        for i in enemies_to_remove:
            new_board[i] = ''
            captured_enemies += 1
            
        return new_board, captured_enemies, captured_friendlies

    def is_overwhelmed(self, board, spot, piece_color):
        """Checks if a piece at spot is overwhelmed."""
        neighbors = ADJACENCY[spot]
        empty_count = 0
        opp_count = 0
        friendly_count = 0
        opp_color = 'W' if piece_color == 'B' else 'B'
        
        for n in neighbors:
            val = board[n]
            if val == '':
                empty_count += 1
            elif val == piece_color:
                friendly_count += 1
            elif val == opp_color:
                opp_count += 1
        
        # Must be completely blocked
        if empty_count > 0:
            return False
            
        # Opponents must strictly outnumber friendlies
        return opp_count > friendly_count

    def evaluate(self, board, my_color, opp_color):
        """Heuristic evaluation of the board state."""
        score = 0
        my_mobility = 0
        opp_mobility = 0
        
        for i in range(24):
            p = board[i]
            if p == my_color:
                # Material value
                score += 20
                # Positional value
                score += self.piece_values[self.spot_types[i]]
                # Mobility
                for n in ADJACENCY[i]:
                    if board[n] == '':
                        my_mobility += 1
            elif p == opp_color:
                score -= 20
                score -= self.piece_values[self.spot_types[i]]
                for n in ADJACENCY[i]:
                    if board[n] == '':
                        opp_mobility += 1
        
        score += (my_mobility - opp_mobility) * 2
        return score

    def count_pieces(self, board, color):
        return sum(1 for p in board if p == color)
