"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-max
Run: 2
Generated: 2026-02-09 18:54:48
"""



import random

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
    """
    Your agent for Surround Morris.
    """
    def __init__(self, name: str, color: str):
        """
        Initialize your agent.

        Parameters:
        -----------
        name : str
            Your agent name (e.g., "Agent-1").
        color : str
            Your piece color: 'B' (Black) or 'W' (White).
        """
        self.name = name
        self.color = color

    def _count_neighbors(self, board, spot, color):
        """Count neighbors of a specific color around a spot."""
        neighbors = ADJACENCY[spot]
        friendly = 0
        opponent = 0
        empty = 0
        
        for n in neighbors:
            if board[n] == '':
                empty += 1
            elif board[n] == color:
                friendly += 1
            else:
                opponent += 1
                
        return friendly, opponent, empty
    
    def _would_cause_self_capture(self, board, spot, color):
        """Check if placing/moving to this spot would cause immediate self-capture."""
        # Temporarily place the piece
        temp_board = board[:]
        temp_board[spot] = color
        
        friendly, opponent, empty = self._count_neighbors(temp_board, spot, color)
        
        # Check capture condition: no empty neighbors and more opponents than friendlies
        if empty == 0 and opponent > friendly:
            return True
        return False
    
    def _get_capture_after_move(self, board, from_spot, to_spot, color):
        """Simulate a move and return which pieces would be captured."""
        # Make the move
        temp_board = board[:]
        temp_board[from_spot] = ''
        temp_board[to_spot] = color
        
        captured = []
        
        # Check if the moved piece commits suicide
        friendly, opponent, empty = self._count_neighbors(temp_board, to_spot, color)
        if empty == 0 and opponent > friendly:
            # Suicide - only the moved piece is captured
            return [to_spot]
        
        # Check all friendly pieces first (self-harm priority)
        for spot in range(24):
            if temp_board[spot] == color:
                f, o, e = self._count_neighbors(temp_board, spot, color)
                if e == 0 and o > f:
                    captured.append(spot)
        
        # Remove captured friendly pieces temporarily
        for spot in captured:
            temp_board[spot] = ''
            
        # Now check enemy pieces
        opp_color = 'W' if color == 'B' else 'B'
        for spot in range(24):
            if temp_board[spot] == opp_color:
                f, o, e = self._count_neighbors(temp_board, spot, opp_color)
                if e == 0 and o > f:
                    captured.append(spot)
                    
        return captured
    
    def _evaluate_placement(self, board, spot, color):
        """Evaluate how good a placement spot is."""
        score = 0
        
        # Avoid suicide placements
        if self._would_cause_self_capture(board, spot, color):
            return -1000
        
        # Prefer central positions (crossroads have 4 neighbors)
        neighbors = len(ADJACENCY[spot])
        if neighbors == 4:
            score += 10
        elif neighbors == 3:
            score += 5
        elif neighbors == 2:
            score += 2
            
        # Prefer spots that threaten opponent pieces
        temp_board = board[:]
        temp_board[spot] = color
        
        opp_color = 'W' if color == 'B' else 'B'
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == opp_color:
                # Check if this placement puts pressure on opponent
                f, o, e = self._count_neighbors(temp_board, neighbor, opp_color)
                if e <= 1:  # If opponent has 1 or 0 escape routes
                    score += 3
                    
        return score
    
    def _evaluate_move(self, board, from_spot, to_spot, color):
        """Evaluate how good a move is."""
        score = 0
        
        # Check if this move leads to captures
        captured = self._get_capture_after_move(board, from_spot, to_spot, color)
        friendly_captures = 0
        enemy_captures = 0
        
        opp_color = 'W' if color == 'B' else 'B'
        for spot in captured:
            if spot == to_spot or board[spot] == color:
                friendly_captures += 1
            else:
                enemy_captures += 1
                
        # If we capture more enemies than we lose friends, it's good
        net_capture = enemy_captures - friendly_captures
        score += net_capture * 10
        
        # Avoid moves that cause self-capture
        if self._would_cause_self_capture(board, to_spot, color):
            return -1000
            
        # Prefer moves to central positions
        neighbors = len(ADJACENCY[to_spot])
        if neighbors == 4:
            score += 5
        elif neighbors == 3:
            score += 3
        elif neighbors == 2:
            score += 1
            
        # Prefer keeping pieces with escape routes
        temp_board = board[:]
        temp_board[from_spot] = ''
        temp_board[to_spot] = color
        
        # Check if any friendly pieces are now in danger
        for spot in range(24):
            if temp_board[spot] == color:
                f, o, e = self._count_neighbors(temp_board, spot, color)
                if e == 0 and o > f:
                    score -= 20  # Bad - we're putting our pieces at risk
                    
        return score
    
    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Called each turn. Return your move based on the current game state.

        Parameters:
        -----------
        state : dict
            {
                "board": list[str],
                    # 24-element list. Each element is '', 'B', or 'W'.
                    # Index corresponds to spot number on the board.
                "phase": str,
                    # 'placement' or 'movement'
                "your_color": str,
                    # Your color: 'B' or 'W'
                "opponent_color": str,
                    # Opponent's color
                "pieces_in_hand": dict,
                    # {'B': int, 'W': int} - pieces not yet placed
                "pieces_on_board": dict,
                    # {'B': int, 'W': int} - pieces currently on the board
                "move_count": int,
                    # Number of movement turns elapsed (0 during placement)
                "history": list[tuple],
                    # List of (board_tuple, current_player) states seen so far.
                    # Use this to detect and avoid 3-fold repetition.
                    # Reset when transitioning from placement to movement phase.
            }

        feedback : dict or None
            None on first attempt. On retries after an invalid move:
            {
                "error_code": str,
                "error_message": str,
                "attempted_move": ...,
                "attempt_number": int,
            }

        Returns:
        --------
        During placement phase:
            int - the spot number (0-23) to place your piece

        During movement phase:
            tuple[int, int] - (from_spot, to_spot) to slide your piece
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            
            if not empty_spots:
                return 0
                
            # Evaluate all possible placements
            best_score = -float('inf')
            best_spots = []
            
            for spot in empty_spots:
                score = self._evaluate_placement(board, spot, color)
                if score > best_score:
                    best_score = score
                    best_spots = [spot]
                elif score == best_score:
                    best_spots.append(spot)
                    
            # If all placements are bad (e.g., all lead to suicide), pick randomly
            if best_score == -1000:
                return random.choice(empty_spots)
                    
            return random.choice(best_spots)
        else:
            # Movement phase
            moves = []
            for spot in range(24):
                if board[spot] != color:
                    continue
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
                        
            if not moves:
                # No legal moves - should not happen in normal play, but return something
                return (0, 1) if 1 in ADJACENCY[0] and board[1] == '' else (0, 0)
                
            # Evaluate all possible moves
            best_score = -float('inf')
            best_moves = []
            
            for move in moves:
                score = self._evaluate_move(board, move[0], move[1], color)
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
                    
            # If all moves are terrible, pick randomly
            if best_score == -1000:
                return random.choice(moves)
                    
            return random.choice(best_moves)
