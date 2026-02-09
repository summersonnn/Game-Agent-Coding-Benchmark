"""
Agent Code: A8-SurroundMorris
Model: minimax/minimax-m2.1@preset/fp8
Run: 2
Generated: 2026-02-09 19:15:26
"""



import random

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
        # Precompute spot weights based on number of neighbors (degree)
        self.spot_weights = [len(ADJACENCY[i]) for i in range(24)]

    def would_be_captured(self, spot, board, color):
        """
        Check if a piece at the given spot would be captured under the current board state.
        
        A piece is captured if:
        - It has zero empty adjacent spots (completely blocked)
        - The number of adjacent opponents is strictly greater than adjacent friendlies
        """
        neighbors = ADJACENCY[spot]
        empty_neighbors = 0
        friendly_neighbors = 0
        opponent_neighbors = 0
        
        for neighbor in neighbors:
            if board[neighbor] == '':
                empty_neighbors += 1
            elif board[neighbor] == color:
                friendly_neighbors += 1
            else:
                opponent_neighbors += 1
                
        return (empty_neighbors == 0) and (opponent_neighbors > friendly_neighbors)

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
            # Find empty spots
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0  # Should not happen, but safety fallback
                
            safe_spots = []
            suicide_spots = []
            
            for spot in empty_spots:
                # Simulate placing our piece at this spot
                board_after = board[:]
                board_after[spot] = color
                
                if self.would_be_captured(spot, board_after, color):
                    suicide_spots.append(spot)
                else:
                    safe_spots.append(spot)
            
            if safe_spots:
                # Choose the safe spot with the highest weight (most influential)
                best_spot = max(safe_spots, key=lambda s: self.spot_weights[s])
                return best_spot
            else:
                # All spots result in suicide - choose one with highest weight anyway
                if suicide_spots:
                    return max(suicide_spots, key=lambda s: self.spot_weights[s])
                else:
                    return 0  # Fallback
                    
        else:  # movement phase
            # Find all legal moves: from our pieces to adjacent empty spots
            moves = []
            for from_spot in range(24):
                if board[from_spot] != color:
                    continue
                for to_spot in ADJACENCY[from_spot]:
                    if board[to_spot] == '':
                        moves.append((from_spot, to_spot))
            
            if not moves:
                # No legal moves - should not happen as game should have ended
                return (0, 1)
            
            # Build state count for repetition detection
            state_count = {}
            for (hist_board, hist_player) in state["history"]:
                key = (hist_board, hist_player)
                state_count[key] = state_count.get(key, 0) + 1
            
            best_move = None
            best_score = -10**9
            
            for move in moves:
                from_spot, to_spot = move
                
                # Simulate the move
                board1 = board[:]
                board1[from_spot] = ''
                board1[to_spot] = color
                
                # Step 1: Check if active piece is captured (suicide)
                if self.would_be_captured(to_spot, board1, color):
                    pieces_lost = 1
                    pieces_gained = 0
                    # Active piece dies immediately
                    board_after = board1[:]
                    board_after[to_spot] = ''
                else:
                    # Step 2a: Check all friendly pieces for capture
                    captured_friendly = []
                    for spot in range(24):
                        if board1[spot] == color:
                            if self.would_be_captured(spot, board1, color):
                                captured_friendly.append(spot)
                    
                    board2 = board1[:]
                    for spot in captured_friendly:
                        board2[spot] = ''
                    
                    # Step 2b: Check enemy pieces for capture
                    captured_enemy = []
                    for spot in range(24):
                        if board2[spot] == opp:
                            if self.would_be_captured(spot, board2, opp):
                                captured_enemy.append(spot)
                    
                    pieces_lost = len(captured_friendly)
                    pieces_gained = len(captured_enemy)
                    
                    # Remove captured enemy pieces
                    board_after = board2[:]
                    for spot in captured_enemy:
                        board_after[spot] = ''
                
                # Check for 3-fold repetition
                state_after = (tuple(board_after), opp)
                count = state_count.get(state_after, 0)
                
                if count >= 2:
                    # This move would cause 3-fold repetition -> draw
                    our_pieces = board_after.count(color)
                    opp_pieces = board_after.count(opp)
                    score = (our_pieces + opp_pieces) / 2
                else:
                    score = pieces_gained - pieces_lost
                
                # Choose move with highest score, break ties by destination spot weight
                if best_move is None:
                    best_move = move
                    best_score = score
                else:
                    if score > best_score:
                        best_move = move
                        best_score = score
                    elif score == best_score:
                        # Prefer moves to more influential spots
                        if self.spot_weights[to_spot] > self.spot_weights[best_move[1]]:
                            best_move = move
            
            return best_move
