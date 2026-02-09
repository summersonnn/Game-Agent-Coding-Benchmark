"""
Agent Code: A8-SurroundMorris
Model: google/gemini-3-flash-preview
Run: 1
Generated: 2026-02-09 18:54:48
"""



import random

class SurroundMorrisAgent:
    """
    An agent for Surround Morris that uses a 1-ply search with a heuristic evaluation function.
    It accounts for the unique capture rules, self-harm priority, and repetition rules.
    """
    def __init__(self, name: str, color: str):
        """
        Initialize the agent.
        """
        self.name = name
        self.color = color
        self.opp_color = 'W' if color == 'B' else 'B'

    def is_overwhelmed(self, board: list[str], spot: int) -> bool:
        """
        Checks if a piece at a given spot is captured according to the Overwhelm rule.
        """
        color = board[spot]
        if not color:
            return False
        
        opp = 'W' if color == 'B' else 'B'
        neighbors = ADJACENCY[spot]
        
        empty_count = 0
        friend_count = 0
        opp_count = 0
        for n in neighbors:
            if board[n] == '':
                empty_count += 1
            elif board[n] == color:
                friend_count += 1
            elif board[n] == opp:
                opp_count += 1
        
        # A piece is captured if it has no air and more enemies than friends adjacent.
        return empty_count == 0 and opp_count > friend_count

    def simulate_move(self, board: list[str], move: int | tuple[int, int], color: str, phase: str) -> list[str]:
        """
        Simulates the board state after a move, applying the specific capture logic:
        1. Suicide First 
        2. Friendly pieces die first (Self-Harm Priority)
        3. Enemy pieces die
        """
        new_board = list(board)
        if phase == 'placement':
            # move is an int (spot)
            new_board[move] = color
            active_spot = move
        else:
            # move is a tuple (from, to)
            start, end = move
            new_board[start] = ''
            new_board[end] = color
            active_spot = end

        # 1. Active Piece Suicide Check
        if self.is_overwhelmed(new_board, active_spot):
            new_board[active_spot] = ''
            return new_board # Turn ends immediately; no other captures processed.

        # 2. Universal Capture Sweep (Self-Harm Priority)
        # 2a. Friendly pieces (same color as mover) are removed first.
        to_remove_friendly = [i for i in range(24) if new_board[i] == color and self.is_overwhelmed(new_board, i)]
        for i in to_remove_friendly:
            new_board[i] = ''
        
        # 2b. Enemy pieces are re-checked and removed.
        opp = 'W' if color == 'B' else 'B'
        to_remove_opp = [i for i in range(24) if new_board[i] == opp and self.is_overwhelmed(new_board, i)]
        for i in to_remove_opp:
            new_board[i] = ''
        
        return new_board

    def has_legal_moves(self, board: list[str], color: str) -> bool:
        """
        Checks if the player has any legal sliding moves available.
        """
        for i in range(24):
            if board[i] == color:
                for n in ADJACENCY[i]:
                    if board[n] == '':
                        return True
        return False

    def evaluate_board(self, board: list[str], color: str, phase: str) -> float:
        """
        Heuristic evaluation of the board state.
        Higher is better for 'color'.
        """
        opp = 'W' if color == 'B' else 'B'
        my_pieces = [i for i, v in enumerate(board) if v == color]
        opp_pieces = [i for i, v in enumerate(board) if v == opp]
        
        # Elimination check
        if not my_pieces:
            return -1000
        if not opp_pieces:
            return 1000
        
        # Check for Mate (Stalemate) in movement phase
        if phase == 'movement':
            if not self.has_legal_moves(board, opp):
                return 900 # Opponent is stuck, I win
            if not self.has_legal_moves(board, color):
                return -900 # I am stuck, I lose

        # Base score on piece count
        score = len(my_pieces) * 20 - len(opp_pieces) * 20
        
        # Centrality: Crossroads (4 neighbors) are high value
        crossroads = {4, 10, 13, 19}
        for p in my_pieces:
            if p in crossroads:
                score += 2
        for p in opp_pieces:
            if p in crossroads:
                score -= 2
        
        # Safety: Bonus for pieces with at least one empty neighbor (less likely to be captured)
        for p in my_pieces:
            if any(board[n] == '' for n in ADJACENCY[p]):
                score += 1
                    
        return score

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Selects a move based on the 1-ply simulation and evaluation.
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        history = state["history"]

        if phase == "placement":
            legal_spots = [i for i in range(24) if board[i] == '']
            random.shuffle(legal_spots)
            
            best_score = -float('inf')
            best_spot = legal_spots[0] if legal_spots else 0
            
            for spot in legal_spots:
                sim_board = self.simulate_move(board, spot, color, 'placement')
                score = self.evaluate_board(sim_board, color, 'placement')
                
                # Penalize suicide moves during placement
                if sim_board[spot] == '':
                    score -= 50
                
                if score > best_score:
                    best_score = score
                    best_spot = spot
            return best_spot

        else:
            # Generate all legal sliding moves
            moves = []
            for i in range(24):
                if board[i] == color:
                    for n in ADJACENCY[i]:
                        if board[n] == '':
                            moves.append((i, n))
            
            if not moves:
                return (0, 1) # Should not be reachable if engine calls make_move

            random.shuffle(moves)
            best_score = -float('inf')
            best_move = moves[0]
            
            for move in moves:
                sim_board = self.simulate_move(board, move, color, 'movement')
                
                # 3-Fold Repetition Check
                # history contains (board_tuple, current_player). 
                # If this move leads to a state that has appeared twice, it's a draw.
                state_tuple = (tuple(sim_board), opp)
                rep_count = history.count(state_tuple)
                
                score = self.evaluate_board(sim_board, color, 'movement')
                
                if rep_count >= 2:
                    # If we are currently at a disadvantage, a draw is acceptable (0).
                    # If we are winning, a draw is penalized.
                    current_eval = self.evaluate_board(board, color, 'movement')
                    score = 0 if current_eval < 0 else -10
                
                if score > best_score:
                    best_score = score
                    best_move = move
                        
            return best_move
