"""
Agent Code: A8-SurroundMorris
Model: google/gemini-3-flash-preview
Run: 2
Generated: 2026-02-09 18:54:48
"""



import random

class SurroundMorrisAgent:
    """
    A strategic agent for Surround Morris that uses 1-step lookahead, 
    material evaluation, and positional heuristics.
    """
    def __init__(self, name: str, color: str):
        """
        Initialize the agent.
        """
        self.name = name
        self.color = color

    def _is_overwhelmed(self, board, spot):
        """
        Check if the piece at 'spot' is captured according to the Overwhelm rule.
        """
        color = board[spot]
        if not color:
            return False
        
        opp = 'W' if color == 'B' else 'B'
        neighbors = ADJACENCY[spot]
        
        counts = {'': 0, 'B': 0, 'W': 0}
        for n in neighbors:
            counts[board[n]] += 1
            
        # Condition: 0 empty neighbors AND opponents > friendlies
        return counts[''] == 0 and counts[opp] > counts[color]

    def _simulate_move(self, board, move, color):
        """
        Simulate a move (placement or movement) and apply capture rules.
        Follows 'Suicide First' and 'Self-Harm Priority' logic.
        """
        new_board = list(board)
        active_spot = -1
        
        # Apply the move
        if isinstance(move, int):  # Placement
            new_board[move] = color
            active_spot = move
        else:  # Movement
            f, t = move
            new_board[f] = ''
            new_board[t] = color
            active_spot = t
            
        # Step 1: Active Piece Suicide Check
        if self._is_overwhelmed(new_board, active_spot):
            new_board[active_spot] = ''
            return new_board  # Turn ends immediately
            
        # Step 2a: Friendly Sweep (Universal Capture)
        to_remove_friendly = [i for i in range(24) if new_board[i] == color and self._is_overwhelmed(new_board, i)]
        for i in to_remove_friendly:
            new_board[i] = ''
            
        # Step 2b: Enemy Sweep (Some might be saved by Step 2a)
        opp_color = 'W' if color == 'B' else 'B'
        to_remove_enemy = [i for i in range(24) if new_board[i] == opp_color and self._is_overwhelmed(new_board, i)]
        for i in to_remove_enemy:
            new_board[i] = ''
            
        return new_board

    def _evaluate(self, board, my_color, opp_color, phase):
        """
        Heuristic evaluation of a board state.
        """
        my_p = [i for i, v in enumerate(board) if v == my_color]
        opp_p = [i for i, v in enumerate(board) if v == opp_color]
        
        # Termination conditions
        if not my_p: return -7000  # Loss
        if not opp_p: return 7000  # Win
        
        # Material weight
        score = (len(my_p) - len(opp_p)) * 1000
        
        # Movement phase specific logic
        if phase == "movement":
            # Check for Mate (Stalemate)
            opp_has_moves = any(board[n] == '' for p in opp_p for n in ADJACENCY[p])
            if not opp_has_moves: return 7000  # Win by Mate
            
            my_has_moves = any(board[n] == '' for p in my_p for n in ADJACENCY[p])
            if not my_has_moves: return -7000  # Loss by Mate

        # Positional Heuristics
        for p in my_p:
            # Centrality: Crossroads (4 neighbors) > T-junctions (3) > Corners (2)
            score += len(ADJACENCY[p]) * 15
            # Mobility/Safety: Each empty neighbor is an escape route
            score += sum(60 for n in ADJACENCY[p] if board[n] == '')
            
        for p in opp_p:
            score -= len(ADJACENCY[p]) * 15
            score -= sum(60 for n in ADJACENCY[p] if board[n] == '')
                
        return score

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Choose the best move based on 1-step simulation and heuristics.
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        history = state.get("history", [])
        
        # 1. Identify all legal moves
        if phase == "placement":
            moves = [i for i in range(24) if board[i] == '']
        else:
            moves = []
            for i in range(24):
                if board[i] == color:
                    for n in ADJACENCY[i]:
                        if board[n] == '':
                            moves.append((i, n))
        
        if not moves:
            return 0 if phase == "placement" else (0, 1)

        # 2. Handle feedback from previous invalid attempts
        if feedback and "attempted_move" in feedback:
            attempted = feedback["attempted_move"]
            if isinstance(attempted, list):
                attempted = tuple(attempted)
            if attempted in moves:
                moves.remove(attempted)
            if not moves:
                # Emergency fallback if all moves were rejected
                empty_spots = [i for i in range(24) if board[i] == '']
                return random.choice(empty_spots) if phase == "placement" else (0, 1)

        # 3. Evaluate each move
        best_moves = []
        best_score = -float('inf')
        
        for move in moves:
            sim_board = self._simulate_move(board, move, color)
            
            # Repetition / Draw logic
            # History stores (board_tuple, next_player). 
            # If our move results in a state seen twice, it's a draw.
            if phase == "movement" and history.count((tuple(sim_board), opp)) >= 2:
                my_p_count = sum(1 for v in sim_board if v == color)
                opp_p_count = sum(1 for v in sim_board if v == opp)
                # Draw score is average of pieces on board * 1000
                score = ((my_p_count + opp_p_count) / 2.0) * 1000
            else:
                score = self._evaluate(sim_board, color, opp, phase)
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        
        # 4. Tie-break randomly among best moves
        return random.choice(best_moves) if best_moves else moves[0]
