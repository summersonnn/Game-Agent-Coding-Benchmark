"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-coder@preset/fp8
Run: 1
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
            # Find empty spots and pick one strategically
            empty_spots = [i for i in range(24) if board[i] == '']
            
            # Prioritize center-heavy spots with high connectivity
            priority_spots = [4, 10, 13, 19]  # Crossroads
            secondary_spots = [1, 3, 5, 7, 11, 12, 15, 16, 17, 18, 20, 22]
            corner_spots = [0, 2, 6, 8, 9, 14, 21, 23]

            # Try to find best possible non-suicidal placement
            for spot_list in [priority_spots, secondary_spots, corner_spots]:
                candidates = [s for s in spot_list if s in empty_spots]
                if candidates:
                    # Simulate placing the piece here and check if it's safe
                    for candidate in candidates:
                        temp_board = board[:]
                        temp_board[candidate] = color
                        if not self._would_be_suicidal(candidate, temp_board):
                            return candidate
            
            # Fallback: choose any legal move even if suicidal
            return random.choice(empty_spots) if empty_spots else 0

        else: # Movement phase
            # Get all legal moves
            legal_moves = self._get_legal_moves(board, color)
            
            if not legal_moves:
                # Mated; make arbitrary move since it'll be flagged anyway
                return (0, 1)
                
            # Evaluate potential captures or threats
            capture_moves = []
            escape_moves = []
            positional_moves = []

            for from_spot, to_spot in legal_moves:
                # Simulate the move
                temp_board = board[:]
                temp_board[from_spot] = ''
                temp_board[to_spot] = color
                
                # Check if this move results in any capture (including opponent)
                captured_opponents = self._find_captures(temp_board, opp)
                captured_friends = self._find_captures(temp_board, color)
                
                # Avoid moves that result in more friendly captures than enemy captures
                net_gain = len(captured_opponents) - len(captured_friends)
                
                if net_gain > 0:
                    capture_moves.append(((from_spot, to_spot), net_gain))
                elif self._would_improve_position(from_spot, to_spot, board, color):
                    positional_moves.append((from_spot, to_spot))
                elif self._is_escape_move(from_spot, to_spot, board, color):
                    escape_moves.append((from_spot, to_spot))

            # Sort capture moves by effectiveness
            if capture_moves:
                capture_moves.sort(key=lambda x: x[1], reverse=True)
                return capture_moves[0][0]
                
            # Prefer escape moves over positional ones
            if escape_moves:
                return random.choice(escape_moves)
                
            if positional_moves:
                return random.choice(positional_moves)
                
            # Last resort: random legal move
            return random.choice(legal_moves)

    def _get_legal_moves(self, board, color):
        """Generate all legal moves for a given player."""
        moves = []
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
        return moves
        
    def _would_be_suicidal(self, spot, board):
        """Check if placing a piece at spot would cause immediate suicide."""
        return self._is_captured(spot, board)
        
    def _is_captured(self, spot, board):
        """Check if a piece at spot is captured under Overwhelm rules."""
        if board[spot] == '':
            return False
            
        color = board[spot]
        neighbors = ADJACENCY[spot]
        empty_count = 0
        friendly_count = 0
        opponent_count = 0
        
        for n in neighbors:
            if board[n] == '':
                empty_count += 1
            elif board[n] == color:
                friendly_count += 1
            else:
                opponent_count += 1
                
        # Must be completely surrounded and outgunned
        return empty_count == 0 and opponent_count > friendly_count
    
    def _find_captures(self, board, target_color):
        """Find all pieces of target_color that are capturable."""
        captured = []
        for i in range(24):
            if board[i] == target_color and self._is_captured(i, board):
                captured.append(i)
        return captured
        
    def _would_improve_position(self, from_spot, to_spot, board, color):
        """Heuristic to determine if a move improves position"""
        # Simple heuristic: moving towards central spots
        central_spots = {4, 10, 13, 19}
        distance_before = min(abs(from_spot - cs) for cs in central_spots)
        distance_after = min(abs(to_spot - cs) for cs in central_spots)
        return distance_after < distance_before
    
    def _is_escape_move(self, from_spot, to_spot, board, color):
        """Detect if the move provides escape route from a tight spot"""
        old_neighbors = ADJACENCY[from_spot]
        new_neighbors = ADJACENCY[to_spot]
        
        # Count how many more escape routes we'd have
        old_empties = sum(1 for n in old_neighbors if board[n] == '')
        new_empties = sum(1 for n in new_neighbors if board[n] == '') + 1  # Including new spot
        
        return new_empties > old_empties
