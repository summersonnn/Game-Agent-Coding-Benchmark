"""
Agent Code: A8-SurroundMorris
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-09 19:15:26
"""



import random


class SurroundMorrisAgent:
    """
    Intelligent agent for Surround Morris game.
    
    Strategy:
    - Placement: Control central positions (crossroads), cluster with friendly pieces,
      avoid immediate captures (suicide).
    - Movement: Capture opponent pieces, avoid friendly fire, maintain safety with
      escape routes, prefer central positions.
    """
    
    def __init__(self, name: str, color: str):
        """
        Initialize the agent.
        
        Parameters:
        -----------
        name : str
            Agent name
        color : str
            'B' (Black) or 'W' (White)
        """
        self.name = name
        self.color = color
    
    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Return a move based on the current game state.
        
        Parameters:
        -----------
        state : dict
            Current game state including board, phase, pieces, etc.
        feedback : dict | None
            Error feedback if previous attempt was invalid
        
        Returns:
        --------
        int or tuple[int, int]
            Placement: spot number (0-23)
            Movement: (from_spot, to_spot)
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opponent_color = state["opponent_color"]
        
        if phase == "placement":
            return self._place_piece(board, color, opponent_color)
        else:
            return self._move_piece(board, color, opponent_color)
    
    def _place_piece(self, board, color, opponent_color):
        """Choose a spot to place a piece during placement phase."""
        empty_spots = [i for i in range(24) if board[i] == '']
        
        if not empty_spots:
            return 0
        
        # Prefer non-suicide placements
        safe_placements = []
        for spot in empty_spots:
            test_board = board[:]
            test_board[spot] = color
            
            if not self._is_piece_captured(spot, test_board, color, opponent_color):
                score = self._score_placement(spot, board, color, opponent_color)
                safe_placements.append((spot, score))
        
        # If no safe placements, try all anyway (suicide is legal)
        if not safe_placements:
            safe_placements = [
                (spot, self._score_placement(spot, board, color, opponent_color))
                for spot in empty_spots
            ]
        
        best_spot = max(safe_placements, key=lambda x: x[1])[0]
        return best_spot
    
    def _score_placement(self, spot, board, color, opponent_color):
        """Evaluate strategic value of a placement spot."""
        score = 0
        neighbors = ADJACENCY[spot]
        
        # Prefer central positions (high degree)
        degree = len(neighbors)
        if degree == 4:
            score += 10  # Crossroad
        elif degree == 3:
            score += 5   # T-junction
        elif degree == 2:
            score += 1   # Corner
        
        # Clustering bonus
        friendly_neighbors = sum(1 for n in neighbors if board[n] == color)
        score += friendly_neighbors * 3
        
        # Avoid dense enemy clusters
        opponent_neighbors = sum(1 for n in neighbors if board[n] == opponent_color)
        score -= opponent_neighbors * 2
        
        return score
    
    def _move_piece(self, board, color, opponent_color):
        """Choose a piece to move and where to move it during movement phase."""
        legal_moves = []
        
        # Generate all legal moves
        for spot in range(24):
            if board[spot] != color:
                continue
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    legal_moves.append((spot, neighbor))
        
        if not legal_moves:
            return (0, 1)  # Dummy move; engine will detect mate
        
        # Score and return best move
        best_move = legal_moves[0]
        best_score = float('-inf')
        
        for from_spot, to_spot in legal_moves:
            score = self._score_movement(board, from_spot, to_spot, color, opponent_color)
            if score > best_score:
                best_score = score
                best_move = (from_spot, to_spot)
        
        return best_move
    
    def _score_movement(self, board, from_spot, to_spot, color, opponent_color):
        """Evaluate a movement."""
        # Simulate the move
        test_board = board[:]
        test_board[from_spot] = ''
        test_board[to_spot] = color
        
        # Never make a suicide move
        if self._is_piece_captured(to_spot, test_board, color, opponent_color):
            return float('-inf')
        
        score = 0
        
        # Analyze impact on friendly pieces
        for spot in range(24):
            if spot == to_spot or test_board[spot] != color:
                continue
            
            was_safe = not self._is_piece_captured(spot, board, color, opponent_color)
            is_safe = not self._is_piece_captured(spot, test_board, color, opponent_color)
            
            if was_safe and not is_safe:
                # We just harmed a friendly piece (friendly fire)
                score -= 8
            elif not was_safe and is_safe:
                # We just freed a friendly piece
                score += 2
        
        # Analyze impact on opponent pieces
        for spot in range(24):
            if test_board[spot] != opponent_color:
                continue
            
            was_captured = self._is_piece_captured(spot, board, opponent_color, color)
            is_captured = self._is_piece_captured(spot, test_board, opponent_color, color)
            
            if not was_captured and is_captured:
                # We just captured an opponent
                score += 15
        
        # Positional bonuses
        if to_spot in {4, 7, 10, 11, 13, 16, 19}:
            score += 1  # Central positions
        
        empty_neighbors = sum(1 for n in ADJACENCY[to_spot] if test_board[n] == '')
        if empty_neighbors > 0:
            score += 0.5  # Escape routes
        else:
            score -= 1  # Penalty for complete blockade
        
        # Small random tiebreaker
        score += random.random() * 0.01
        
        return score
    
    def _is_piece_captured(self, spot, board, color, opponent_color):
        """
        Check if a piece at spot is captured.
        
        Captured if:
        1. No empty neighbors (completely blocked)
        2. opponent_neighbors > friendly_neighbors
        """
        neighbors = ADJACENCY[spot]
        
        # Empty neighbor = safe
        empty_count = sum(1 for n in neighbors if board[n] == '')
        if empty_count > 0:
            return False
        
        # No escape - check neighbor balance
        friendly_count = sum(1 for n in neighbors if board[n] == color)
        opponent_count = sum(1 for n in neighbors if board[n] == opponent_color)
        
        return opponent_count > friendly_count
