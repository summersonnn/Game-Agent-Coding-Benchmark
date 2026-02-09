"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-09 19:15:26
"""



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

    def spot_value(self, spot: int) -> int:
        """Calculate positional value of a spot based on adjacency count."""
        n = len(ADJACENCY[spot])
        if n == 4:
            return 10
        elif n == 3:
            return 7
        else:  # n == 2
            return 3

    def is_captured(self, spot: int, board: list[str], color: str) -> bool:
        """Check if piece at spot meets capture conditions: zero empty neighbors and opponent > friendly neighbors."""
        if board[spot] != color:
            return False
            
        empty_count = 0
        opp_count = 0
        friendly_count = 0
        
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty_count += 1
            elif board[neighbor] == color:
                friendly_count += 1
            else:
                opp_count += 1
                
        return (empty_count == 0) and (opp_count > friendly_count)

    def is_suicidal_placement(self, board: list[str], spot: int, color: str, opp: str) -> bool:
        """Check if placing at spot would cause immediate suicide (step1 capture)."""
        empty_count = 0
        opp_count = 0
        friendly_count = 0
        
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty_count += 1
            elif board[neighbor] == opp:
                opp_count += 1
            elif board[neighbor] == color:
                friendly_count += 1
                
        return (empty_count == 0) and (opp_count > friendly_count)

    def simulate_placement_net_gain(self, board: list[str], spot: int, color: str, opp: str) -> int:
        """Simulate capture effects after non-suicidal placement and return net_gain (enemy_captured - friendly_captured)."""
        board_temp = list(board)
        board_temp[spot] = color
        
        # Step 2a: Check all friendly pieces for capture
        friendly_captured = []
        for s in range(24):
            if board_temp[s] == color:
                if self.is_captured(s, board_temp, color):
                    friendly_captured.append(s)
        
        # Remove captured friendly pieces
        for s in friendly_captured:
            board_temp[s] = ''
        
        # Step 2b: Check enemy pieces for capture
        enemy_captured = []
        for s in range(24):
            if board_temp[s] == opp:
                if self.is_captured(s, board_temp, opp):
                    enemy_captured.append(s)
        
        return len(enemy_captured) - len(friendly_captured)

    def simulate_movement_net_gain(self, board: list[str], from_spot: int, to_spot: int, color: str, opp: str) -> int:
        """Simulate capture effects after movement and return net_gain (enemy_captured - friendly_captured), or -1 for step1 suicide."""
        board_temp = list(board)
        board_temp[from_spot] = ''
        board_temp[to_spot] = color
        
        # Step 1: Check if moved piece is captured
        if self.is_captured(to_spot, board_temp, color):
            return -1
        
        # Step 2a: Check all friendly pieces for capture
        friendly_captured = []
        for s in range(24):
            if board_temp[s] == color:
                if self.is_captured(s, board_temp, color):
                    friendly_captured.append(s)
        
        # Remove captured friendly pieces
        for s in friendly_captured:
            board_temp[s] = ''
        
        # Step 2b: Check enemy pieces for capture
        enemy_captured = []
        for s in range(24):
            if board_temp[s] == opp:
                if self.is_captured(s, board_temp, opp):
                    enemy_captured.append(s)
        
        return len(enemy_captured) - len(friendly_captured)

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Called each turn. Return your move based on the current game state.
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]

        # Handle retries after invalid moves
        if feedback is not None:
            if phase == "placement":
                empty = [i for i in range(24) if board[i] == '']
                return empty[0] if empty else 0
            else:
                for spot in range(24):
                    if board[spot] == color:
                        for neighbor in ADJACENCY[spot]:
                            if board[neighbor] == '':
                                return (spot, neighbor)
                return (0, 1)

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0
                
            non_suicidal = []
            suicidal = []
            for spot in empty_spots:
                if self.is_suicidal_placement(board, spot, color, opp):
                    suicidal.append(spot)
                else:
                    non_suicidal.append(spot)
            
            candidates = non_suicidal if non_suicidal else suicidal
            best_score = -10**9
            best_move = None
            
            for spot in candidates:
                if spot in non_suicidal:
                    net_gain = self.simulate_placement_net_gain(board, spot, color, opp)
                    score = self.spot_value(spot) + 100 * (1 + net_gain)
                else:
                    score = 0  # Suicidal move: no positional gain, net material change 0
                
                if score > best_score:
                    best_score = score
                    best_move = spot
                    
            return best_move
            
        else:  # Movement phase
            legal_moves = []
            for spot in range(24):
                if board[spot] == color:
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == '':
                            legal_moves.append((spot, neighbor))
            
            if not legal_moves:
                return (0, 1)  # Should not occur per rules, but fallback
                
            best_score = -10**9
            best_move = None
            for move in legal_moves:
                from_spot, to_spot = move
                net_gain = self.simulate_movement_net_gain(board, from_spot, to_spot, color, opp)
                
                if net_gain == -1:  # Step1 suicide
                    score = -100
                else:
                    score = self.spot_value(to_spot) + 100 * net_gain
                
                if score > best_score:
                    best_score = score
                    best_move = move
                    
            return best_move
