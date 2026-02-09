"""
Agent Code: A8-SurroundMorris
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 2
Generated: 2026-02-09 19:15:26
"""



import random

class SurroundMorrisAgent:
    """
    An agent for Surround Morris that uses heuristic evaluation to select moves.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.spot_values = {}

    def get_spot_values(self):
        """Calculate the value of each spot based on its degree (centrality)."""
        if not self.spot_values:
            for i in range(24):
                self.spot_values[i] = len(ADJACENCY[i])
        return self.spot_values

    def is_captured(self, spot, board, piece_color):
        """
        Check if a piece at 'spot' of 'piece_color' is captured on 'board'.
        Rule: Zero empty neighbors AND Opponent neighbors > Friendly neighbors.
        """
        neighbors = ADJACENCY[spot]
        empty = 0
        friendly = 0
        opponent = 0
        
        for n in neighbors:
            val = board[n]
            if val == '':
                empty += 1
            elif val == piece_color:
                friendly += 1
            else:
                opponent += 1
        
        if empty > 0:
            return False
        return opponent > friendly

    def simulate_move(self, board, my_color, opp_color, move, is_placement):
        """
        Simulate a move and return (score, new_board_tuple).
        """
        new_board = list(board)
        active_spot = -1
        
        # Apply the move
        if is_placement:
            spot = move
            new_board[spot] = my_color
            active_spot = spot
        else:
            start, end = move
            new_board[start] = ''
            new_board[end] = my_color
            active_spot = end
            
        # 1. Active Piece Suicide Check
        if self.is_captured(active_spot, new_board, my_color):
            new_board[active_spot] = ''
            # Suicide is usually a wasted move (score penalty)
            return -10000, tuple(new_board)
        
        # 2. Universal Capture Sweep
        
        # 2a. Friendly Fire (Self-Harm Priority)
        captured_friends = []
        for s in range(24):
            if new_board[s] == my_color:
                if self.is_captured(s, new_board, my_color):
                    captured_friends.append(s)
        
        for s in captured_friends:
            new_board[s] = ''
            
        # 2b. Enemy Capture (Re-check after friends removed)
        captured_enemies = []
        for s in range(24):
            if new_board[s] == opp_color:
                if self.is_captured(s, new_board, opp_color):
                    captured_enemies.append(s)
        
        for s in captured_enemies:
            new_board[s] = ''
            
        # --- Heuristic Scoring ---
        score = 0
        
        # Material difference
        score += len(captured_enemies) * 100
        score -= len(captured_friends) * 50
        
        # Positional value (prefer high-degree spots)
        spot_vals = self.get_spot_values()
        if is_placement:
            score += spot_vals[move] * 3
        else:
            score += spot_vals[move[1]] * 3  # Value of destination
            score -= spot_vals[move[0]] * 1  # Cost of vacating
            
        # Mobility (number of legal moves available in resulting state)
        # Helps avoid getting mated
        mobility = 0
        for i in range(24):
            if new_board[i] == my_color:
                for n in ADJACENCY[i]:
                    if new_board[n] == '':
                        mobility += 1
        score += mobility * 2
        
        # Avoid elimination (having 0 pieces)
        if new_board.count(my_color) == 0:
            score = -100000
            
        return score, tuple(new_board)

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        my_color = state["your_color"]
        opp_color = state["opponent_color"]
        history = state["history"]
        
        if phase == "placement":
            hand_count = state["pieces_in_hand"][my_color]
            board_count = state["pieces_on_board"][my_color]
            
            legal_spots = [i for i in range(24) if board[i] == '']
            random.shuffle(legal_spots)
            
            best_score = -float('inf')
            best_spot = legal_spots[0] if legal_spots else 0
            
            for spot in legal_spots:
                score, new_board = self.simulate_move(board, my_color, opp_color, spot, is_placement=True)
                
                # Special case: If this is the very last piece to place, suicide results in immediate loss.
                if hand_count == 1 and board_count == 0:
                    if score < -5000: # Indicates suicide
                        score = -200000
                
                # Avoid 3-fold repetition (Draw)
                if history.count((new_board, opp_color)) >= 2:
                    score = -100000
                
                if score > best_score:
                    best_score = score
                    best_spot = spot
            
            return best_spot
            
        else:
            # Movement Phase
            legal_moves = []
            for start in range(24):
                if board[start] == my_color:
                    for end in ADJACENCY[start]:
                        if board[end] == '':
                            legal_moves.append((start, end))
            
            random.shuffle(legal_moves)
            best_score = -float('inf')
            best_move = legal_moves[0] if legal_moves else (0, 1)
            
            for move in legal_moves:
                score, new_board = self.simulate_move(board, my_color, opp_color, move, is_placement=False)
                
                # Avoid 3-fold repetition
                if history.count((new_board, opp_color)) >= 2:
                    score = -100000
                
                if score > best_score:
                    best_score = score
                    best_move = move
            
            return best_move
