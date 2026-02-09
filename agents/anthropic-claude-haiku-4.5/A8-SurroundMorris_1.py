"""
Agent Code: A8-SurroundMorris
Model: anthropic/claude-haiku-4.5
Run: 1
Generated: 2026-02-09 19:15:26
"""



import random

class SurroundMorrisAgent:
    """
    Strategic agent for Surround Morris.
    
    Strategy:
    - Maximize enemy captures while avoiding friendly fire
    - Control central board positions (crossroads and key T-junctions)
    - Prevent suicide moves (piece with no escape routes surrounded by enemies)
    - Maintain piece connectivity and safety
    - Avoid 3-fold repetition when disadvantageous
    """
    
    # Strategic positioning zones
    CENTRAL_SPOTS = [4, 10, 13, 19, 7, 16]    # Crossroads & inner T-junctions
    VALUABLE_SPOTS = [1, 3, 5, 9, 11, 14, 12, 18, 20, 22]  # Outer T-junctions
    
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
    
    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Main decision function. Routes to placement or movement handler.
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        if phase == "placement":
            return self._placement_move(board, color, opp)
        else:
            return self._movement_move(state, color, opp)
    
    # ==================== PLACEMENT PHASE ====================
    
    def _placement_move(self, board, color, opp):
        """Choose best spot to place a piece."""
        empty = [i for i in range(24) if board[i] == '']
        if not empty:
            return 0
        
        best_spot = empty[0]
        best_score = self._score_placement(empty[0], board, color, opp)
        
        for spot in empty[1:]:
            score = self._score_placement(spot, board, color, opp)
            if score > best_score:
                best_score = score
                best_spot = spot
        
        return best_spot
    
    def _score_placement(self, spot, board, color, opp):
        """Evaluate quality of a placement spot."""
        # Suicide placements are terrible
        if self._is_captured(spot, color, board):
            return float('-inf')
        
        score = 0.0
        
        # Prefer central positions for board control
        if spot in self.CENTRAL_SPOTS:
            score += 20.0
        elif spot in self.VALUABLE_SPOTS:
            score += 10.0
        
        # Bonus for building clusters with friendly pieces
        neighbors = ADJACENCY[spot]
        friend_count = sum(1 for n in neighbors if board[n] == color)
        enemy_count = sum(1 for n in neighbors if board[n] == opp)
        
        score += friend_count * 4.0
        score -= enemy_count * 2.0
        
        return score
    
    # ==================== MOVEMENT PHASE ====================
    
    def _movement_move(self, state, color, opp):
        """Choose best piece movement."""
        board = state["board"]
        history = state["history"]
        
        # Gather all legal moves
        moves = []
        for src in range(24):
            if board[src] != color:
                continue
            for dst in ADJACENCY[src]:
                if board[dst] == '':
                    moves.append((src, dst))
        
        if not moves:
            return (0, 1)  # Mated (shouldn't reach here normally)
        
        # Score each move
        best_move = moves[0]
        best_score = self._score_movement(moves[0], board, color, opp, history)
        
        for move in moves[1:]:
            score = self._score_movement(move, board, color, opp, history)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _score_movement(self, move, board, color, opp, history):
        """Evaluate a movement move."""
        src, dst = move
        
        # Simulate the move
        sim_board = list(board)
        sim_board[src] = ''
        sim_board[dst] = color
        
        score = 0.0
        
        # ===== STEP 1: Check Active Piece Suicide =====
        if self._is_captured(dst, color, sim_board):
            return float('-inf')
        
        # ===== STEP 2: Simulate Capture Sequence =====
        # Remove friendly pieces that would be captured
        temp_board = list(sim_board)
        friendly_losses = 0
        
        for spot in range(24):
            if temp_board[spot] == color and self._is_captured(spot, color, temp_board):
                friendly_losses += 1
                temp_board[spot] = ''
        
        # Count enemy pieces that would be captured (with updated board)
        enemy_gains = 0
        for spot in range(24):
            if temp_board[spot] == opp and self._is_captured(spot, opp, temp_board):
                enemy_gains += 1
        
        # Score captures
        score += enemy_gains * 50.0      # Enemy kills are valuable
        score -= friendly_losses * 60.0  # Friendly fire is costly
        
        # ===== STEP 3: Position Value =====
        if dst in self.CENTRAL_SPOTS:
            score += 8.0
        elif dst in self.VALUABLE_SPOTS:
            score += 3.0
        
        # ===== STEP 4: Piece Safety =====
        # Penalize moves that block own pieces without escape
        blocked_pieces = 0
        for spot in range(24):
            if sim_board[spot] == color and spot != dst:
                empty_neighbors = sum(1 for n in ADJACENCY[spot] if sim_board[n] == '')
                if empty_neighbors == 0:
                    blocked_pieces += 1
        
        score -= blocked_pieces * 4.0
        
        # ===== STEP 5: Avoid Repetition =====
        board_state = tuple(sim_board)
        repeat_count = sum(
            1 for h_board, h_player in history
            if h_board == board_state and h_player == color
        )
        
        if repeat_count >= 2:
            score -= 300.0
        
        return score
    
    # ==================== CAPTURE DETECTION ====================
    
    def _is_captured(self, spot, color, board):
        """
        Check if a piece would be captured (overwhelmed).
        Requires: (1) no empty neighbors AND (2) more enemies than friendlies
        """
        neighbors = ADJACENCY[spot]
        
        # Count neighbor types
        empty_count = sum(1 for n in neighbors if board[n] == '')
        
        # If piece has escape route, it's safe
        if empty_count > 0:
            return False
        
        # Completely surrounded: check enemy dominance
        friendly_count = sum(1 for n in neighbors if board[n] == color)
        enemy_count = sum(1 for n in neighbors if board[n] != color and board[n] != '')
        
        return enemy_count > friendly_count
