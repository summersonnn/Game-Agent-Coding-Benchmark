"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-max
Run: 1
Generated: 2026-02-09 18:54:48
"""



import random

# ADJACENCY is provided as a global variable at runtime
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
        """Count friendly and opponent neighbors for a given spot."""
        friendly = 0
        opponent = 0
        empty = 0
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty += 1
            elif board[neighbor] == color:
                friendly += 1
            else:
                opponent += 1
        return friendly, opponent, empty

    def _would_be_captured(self, board, spot, color):
        """Check if a piece at spot would be captured."""
        if board[spot] == '':
            return False
        friendly, opponent, empty = self._count_neighbors(board, spot, color)
        return empty == 0 and opponent > friendly

    def _simulate_move(self, board, from_spot, to_spot, color):
        """Simulate a move and return the resulting board."""
        new_board = board.copy()
        new_board[to_spot] = color
        new_board[from_spot] = ''
        return new_board

    def _simulate_placement(self, board, spot, color):
        """Simulate a placement and return the resulting board."""
        new_board = board.copy()
        new_board[spot] = color
        return new_board

    def _get_capture_after_move(self, board, color, opp, active_spot=None):
        """Simulate the capture process after a move."""
        # Make a copy to work with
        new_board = board.copy()
        
        # Step 1: Check active piece suicide
        if active_spot is not None and new_board[active_spot] == color:
            if self._would_be_captured(new_board, active_spot, color):
                # Active piece dies immediately
                new_board[active_spot] = ''
                return new_board
        
        # Step 2: Universal capture sweep with self-harm priority
        # Step 2a: Remove all friendly pieces that are overwhelmed
        friendly_to_remove = []
        for spot in range(24):
            if new_board[spot] == color and self._would_be_captured(new_board, spot, color):
                friendly_to_remove.append(spot)
        
        for spot in friendly_to_remove:
            new_board[spot] = ''
        
        # Step 2b: Check enemy pieces after friendly removals
        enemy_to_remove = []
        for spot in range(24):
            if new_board[spot] == opp and self._would_be_captured(new_board, spot, opp):
                enemy_to_remove.append(spot)
        
        for spot in enemy_to_remove:
            new_board[spot] = ''
            
        return new_board

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
        history = state["history"]

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            
            # Score empty spots based on strategic value
            spot_scores = {}
            for spot in empty_spots:
                # Base score by position type (crossroad > T-junction > corner)
                neighbors = len(ADJACENCY[spot])
                base_score = neighbors  # 4 for crossroads, 3 for T-junctions, 2 for corners
                
                # Bonus for central positions
                if spot in [4, 7, 10, 13, 16, 19]:  # Central spots
                    base_score += 2
                
                # Check if placing here would cause immediate suicide
                test_board = self._simulate_placement(board, spot, color)
                if self._would_be_captured(test_board, spot, color):
                    base_score -= 10  # Heavy penalty for suicide
                
                # Check if this placement could threaten opponent pieces
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == opp:
                        # Simulate placement and see if opponent piece becomes capturable
                        test_board = self._simulate_placement(board, spot, color)
                        if self._would_be_captured(test_board, neighbor, opp):
                            base_score += 3
                
                spot_scores[spot] = base_score
            
            # Choose the highest scoring spot, with some randomness to avoid repetition
            if spot_scores:
                max_score = max(spot_scores.values())
                best_spots = [spot for spot, score in spot_scores.items() if score >= max_score - 1]
                return random.choice(best_spots)
            else:
                return random.choice(empty_spots) if empty_spots else 0
                
        else:  # movement phase
            # Get all legal moves
            legal_moves = []
            for spot in range(24):
                if board[spot] == color:
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == '':
                            legal_moves.append((spot, neighbor))
            
            if not legal_moves:
                # No legal moves - should not happen in normal play, but return something
                return (0, 1)
            
            # Score each move
            move_scores = {}
            for from_spot, to_spot in legal_moves:
                # Simulate the move
                test_board = self._simulate_move(board, from_spot, to_spot, color)
                
                # Check if active piece would commit suicide
                if self._would_be_captured(test_board, to_spot, color):
                    move_scores[(from_spot, to_spot)] = -100
                    continue
                
                # Simulate full capture process
                result_board = self._get_capture_after_move(test_board, color, opp, to_spot)
                
                # Calculate score based on board state after captures
                my_pieces = sum(1 for p in result_board if p == color)
                opp_pieces = sum(1 for p in result_board if p == opp)
                score = my_pieces - opp_pieces
                
                # Bonus for capturing opponent pieces
                captured_opp = state["pieces_on_board"][opp] - opp_pieces
                score += captured_opp * 5
                
                # Penalty for losing our own pieces
                lost_mine = state["pieces_on_board"][color] - my_pieces
                score -= lost_mine * 10
                
                # Bonus for controlling central positions
                central_spots = [4, 7, 10, 13, 16, 19]
                for spot in central_spots:
                    if result_board[spot] == color:
                        score += 1
                
                # Check for repetition - avoid if we're ahead
                board_tuple = tuple(result_board)
                repetition_count = sum(1 for hist_board, _ in history if hist_board == board_tuple)
                if repetition_count >= 2:  # Would be 3rd occurrence
                    if my_pieces > opp_pieces:
                        score -= 20  # Avoid repetition when ahead
                    else:
                        score += 5   # Consider repetition when behind
                
                move_scores[(from_spot, to_spot)] = score
            
            # Choose the best move with some randomness
            if move_scores:
                max_score = max(move_scores.values())
                best_moves = [move for move, score in move_scores.items() if score >= max_score - 2]
                return random.choice(best_moves)
            else:
                return random.choice(legal_moves)
