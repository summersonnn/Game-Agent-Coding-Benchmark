"""
Agent Code: A8-SurroundMorris
Model: minimax/minimax-m2.1@preset/fp8
Run: 3
Generated: 2026-02-09 20:38:45
"""



import random

class SurroundMorrisAgent:
    """
    Agent for Surround Morris game.
    """
    def __init__(self, name: str, color: str):
        """
        Initialize the agent.
        
        Parameters:
        -----------
        name : str
            Agent name
        color : str
            Agent color: 'B' or 'W'
        """
        self.name = name
        self.color = color

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Determine and return the next move.
        
        Parameters:
        -----------
        state : dict
            Current game state
        feedback : dict or None
            Feedback from previous invalid move attempt
            
        Returns:
        --------
        int or tuple[int, int]
            Placement spot or (from_spot, to_spot) movement
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        history = state.get("history", [])
        
        if phase == "placement":
            return self._placement_move(board, color, opp)
        else:
            return self._movement_move(board, color, opp, history)

    def _placement_move(self, board: list[str], color: str, opp: str) -> int:
        """
        Determine placement move during placement phase.
        
        Strategy:
        - Avoid spots that will be immediately captured (suicide)
        - Prefer central positions (crossroads) for better influence
        - Avoid corners when possible as they're easier to capture
        """
        scores = []
        for spot in range(24):
            if board[spot] != '':
                continue
                
            neighbors = ADJACENCY[spot]
            empty_neighbors = 0
            opponent_neighbors = 0
            friendly_neighbors = 0
            
            for neighbor in neighbors:
                if board[neighbor] == '':
                    empty_neighbors += 1
                elif board[neighbor] == opp:
                    opponent_neighbors += 1
                else:  # Our own piece
                    friendly_neighbors += 1
            
            total_neighbors = len(neighbors)
            
            # Check if this spot would be captured immediately
            if empty_neighbors == 0:
                # Captured if opponent neighbors > friendly neighbors
                if opponent_neighbors > friendly_neighbors:
                    score = -1000  # Avoid suicide
                else:
                    score = 10
            else:
                score = 10  # Safe spot
            
            # Strategic bonuses/penalties
            if spot in [4, 10, 13, 19]:  # Crossroads (most influential)
                score += 5
            elif spot in [0, 2, 21, 23]:  # Corners (easiest to capture)
                score -= 2
            elif spot in [1, 3, 5, 8, 9, 11, 12, 14, 15, 17, 18, 20, 22]:  # T-junctions
                score += 0  # Neutral
                
            scores.append((score, spot))
        
        # Sort by score descending and pick from best
        scores.sort(key=lambda x: x[0], reverse=True)
        best_score = scores[0][0]
        best_spots = [spot for score, spot in scores if score == best_score]
        return random.choice(best_spots)

    def _movement_move(self, board: list[str], color: str, opp: str, history: list[tuple]) -> tuple[int, int]:
        """
        Determine movement move during movement phase.
        
        Strategy:
        - Simulate each legal move and its consequences
        - Prioritize moves that capture opponent pieces
        - Avoid moves that lead to self-capture (friendly fire)
        - Look for checkmate opportunities
        - Avoid 3-fold repetition when winning
        """
        # Generate all legal moves
        legal_moves = []
        for from_spot in range(24):
            if board[from_spot] != color:
                continue
            for to_spot in ADJACENCY[from_spot]:
                if board[to_spot] == '':
                    legal_moves.append((from_spot, to_spot))
        
        if not legal_moves:
            # No legal moves = checkmate, return dummy move
            return (0, 0)
        
        best_score = -float('inf')
        best_moves = []
        
        for from_spot, to_spot in legal_moves:
            # Simulate the move
            new_board = board.copy()
            new_board[to_spot] = color
            new_board[from_spot] = ''
            
            # Simulate capture phase
            new_board = self._simulate_capture(new_board, to_spot, color)
            
            # Check for 3-fold repetition
            state_after_move = (tuple(new_board), opp)
            repetition_count = sum(1 for board_tuple, player in history 
                                 if board_tuple == state_after_move[0] and player == state_after_move[1])
            
            our_count = new_board.count(color)
            opp_count = new_board.count(opp)
            
            if repetition_count >= 2:
                # This move would cause 3-fold repetition (draw)
                if our_count > opp_count:
                    score = -1000  # Bad: we were winning
                elif our_count < opp_count:
                    score = 1000   # Good: we were losing, draw is acceptable
                else:
                    score = 0       # Neutral: even position
            else:
                # Check if opponent has any legal moves (mate opportunity)
                if not self._has_legal_moves(new_board, opp):
                    score = 1000  # Checkmate!
                else:
                    # Score based on piece advantage
                    score = our_count - opp_count
            
            if score > best_score:
                best_score = score
                best_moves = [(from_spot, to_spot)]
            elif score == best_score:
                best_moves.append((from_spot, to_spot))
        
        return random.choice(best_moves)

    def _simulate_capture(self, board: list[str], active_spot: int, active_player: str) -> list[str]:
        """
        Simulate the capture phase after a move.
        
        Order:
        1. Check active piece for suicide
        2. Check all friendly pieces for capture
        3. Re-check all enemy pieces for capture
        """
        # Step 1: Check active piece for suicide
        if self._is_captured(active_spot, board):
            board[active_spot] = ''
            return board
        
        # Step 2: Check all friendly pieces for capture
        captured_friendly = []
        for spot in range(24):
            if board[spot] == active_player and self._is_captured(spot, board):
                captured_friendly.append(spot)
        
        for spot in captured_friendly:
            board[spot] = ''
        
        # Step 3: Re-check all enemy pieces for capture
        enemy = 'B' if active_player == 'W' else 'W'
        captured_enemy = []
        for spot in range(24):
            if board[spot] == enemy and self._is_captured(spot, board):
                captured_enemy.append(spot)
        
        for spot in captured_enemy:
            board[spot] = ''
        
        return board

    def _is_captured(self, spot: int, board: list[str]) -> bool:
        """
        Check if piece at spot is captured.
        
        Capture condition:
        - 0 empty adjacent spots AND
        - opponent neighbors > friendly neighbors
        """
        if board[spot] == '':
            return False
            
        neighbors = ADJACENCY[spot]
        empty_neighbors = 0
        opponent_neighbors = 0
        friendly_neighbors = 0
        
        for neighbor in neighbors:
            if board[neighbor] == '':
                empty_neighbors += 1
            elif board[neighbor] == board[spot]:
                friendly_neighbors += 1
            else:
                opponent_neighbors += 1
        
        return empty_neighbors == 0 and opponent_neighbors > friendly_neighbors

    def _has_legal_moves(self, board: list[str], color: str) -> bool:
        """
        Check if player has any legal moves.
        """
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        return True
        return False
