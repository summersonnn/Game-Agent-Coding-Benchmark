"""
Agent Code: A8-SurroundMorris
Model: anthropic/claude-sonnet-4.5
Run: 1
Generated: 2026-02-09 19:15:26
"""



import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        """Initialize the agent."""
        self.name = name
        self.color = color
        self.opponent_color = 'W' if color == 'B' else 'B'
    
    def make_move(self, state: dict, feedback: dict | None = None):
        """Main entry point for making a move."""
        phase = state["phase"]
        
        if phase == "placement":
            return self.make_placement(state)
        else:
            return self.make_movement(state)
    
    def make_placement(self, state):
        """Choose where to place a piece during placement phase."""
        board = state["board"]
        empty = [i for i in range(24) if board[i] == '']
        
        if not empty:
            return 0
        
        # Score and select best placement
        best_score = -float('inf')
        best_spot = empty[0]
        
        for spot in empty:
            score = self.score_placement(spot, board, state)
            if score > best_score:
                best_score = score
                best_spot = spot
        
        return best_spot
    
    def score_placement(self, spot, board, state):
        """Evaluate a placement move."""
        # Simulate placement
        test_board = list(board)
        test_board[spot] = self.color
        result_board = self.apply_captures(spot, test_board, self.color)
        
        # Suicide check
        if result_board[spot] == '':
            return -10000
        
        # Count material changes
        our_before = sum(1 for p in board if p == self.color)
        our_after = sum(1 for p in result_board if p == self.color)
        opp_before = sum(1 for p in board if p == self.opponent_color)
        opp_after = sum(1 for p in result_board if p == self.opponent_color)
        
        score = 0
        score += (opp_before - opp_after) * 1000  # Captures
        score -= (our_before - our_after) * 1000  # Losses
        
        # Position value (prefer crossroads and T-junctions)
        num_neighbors = len(ADJACENCY[spot])
        if num_neighbors == 4:
            score += 100
        elif num_neighbors == 3:
            score += 50
        
        # Mobility (empty neighbors)
        empty_neighbors = sum(1 for n in ADJACENCY[spot] if result_board[n] == '')
        score += empty_neighbors * 10
        
        # Offensive potential
        opp_neighbors = sum(1 for n in ADJACENCY[spot] if result_board[n] == self.opponent_color)
        score += opp_neighbors * 5
        
        # Evaluate board threats
        score += self.evaluate_threats(result_board) * 10
        
        return score
    
    def make_movement(self, state):
        """Choose which piece to move during movement phase."""
        board = state["board"]
        history = state.get("history", [])
        
        # Get all legal moves
        moves = []
        for spot in range(24):
            if board[spot] != self.color:
                continue
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    moves.append((spot, neighbor))
        
        if not moves:
            return (0, 1)
        
        # Count pieces for repetition logic
        our_pieces = sum(1 for p in board if p == self.color)
        opp_pieces = sum(1 for p in board if p == self.opponent_color)
        
        # Score and select best move
        best_score = -float('inf')
        best_move = moves[0]
        
        for move in moves:
            score = self.score_movement(move, board, state)
            
            # Avoid repetition when ahead
            if our_pieces > opp_pieces and history:
                from_spot, to_spot = move
                test_board = list(board)
                test_board[from_spot] = ''
                test_board[to_spot] = self.color
                result_board = self.apply_captures(to_spot, test_board, self.color)
                
                board_tuple = tuple(result_board)
                count = sum(1 for (b, p) in history if b == board_tuple and p == self.opponent_color)
                if count >= 2:
                    score -= 5000  # Would cause 3-fold repetition
                elif count >= 1:
                    score -= 500   # Getting close to repetition
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def score_movement(self, move, board, state):
        """Evaluate a movement."""
        from_spot, to_spot = move
        
        # Simulate move
        test_board = list(board)
        test_board[from_spot] = ''
        test_board[to_spot] = self.color
        result_board = self.apply_captures(to_spot, test_board, self.color)
        
        # Suicide check
        if result_board[to_spot] == '':
            return -10000
        
        # Count material changes
        our_before = sum(1 for p in board if p == self.color)
        our_after = sum(1 for p in result_board if p == self.color)
        opp_before = sum(1 for p in board if p == self.opponent_color)
        opp_after = sum(1 for p in result_board if p == self.opponent_color)
        
        score = 0
        score += (opp_before - opp_after) * 1000  # Captures
        score -= (our_before - our_after) * 1000  # Losses
        
        # Win conditions
        if opp_after == 0:
            score += 100000  # Elimination
        if self.has_no_moves(result_board, self.opponent_color):
            score += 50000   # Mate
        
        # Mobility (keep escape routes)
        empty_neighbors = sum(1 for n in ADJACENCY[to_spot] if result_board[n] == '')
        score += empty_neighbors * 20
        
        # Position value
        if len(ADJACENCY[to_spot]) == 4:
            score += 50
        elif len(ADJACENCY[to_spot]) == 3:
            score += 30
        
        # Offensive positioning
        opp_neighbors = sum(1 for n in ADJACENCY[to_spot] if result_board[n] == self.opponent_color)
        score += opp_neighbors * 10
        
        # Threat evaluation
        score += self.evaluate_threats(result_board) * 10
        
        return score
    
    def evaluate_threats(self, board):
        """Evaluate threats on the board (positive = good for us)."""
        threat_score = 0
        
        for spot in range(24):
            if board[spot] == '':
                continue
            
            empty_count = sum(1 for n in ADJACENCY[spot] if board[n] == '')
            friendly_count = sum(1 for n in ADJACENCY[spot] if board[n] == board[spot])
            opponent_count = len(ADJACENCY[spot]) - empty_count - friendly_count
            
            if board[spot] == self.opponent_color:
                if empty_count == 1 and opponent_count > friendly_count:
                    threat_score += 5  # Opponent threatened
                elif empty_count == 0 and opponent_count > friendly_count:
                    threat_score += 10  # Opponent would be captured
            elif board[spot] == self.color:
                if empty_count == 1 and opponent_count > friendly_count:
                    threat_score -= 5  # Our piece threatened
                elif empty_count == 0 and opponent_count > friendly_count:
                    threat_score -= 10  # Our piece would be captured
        
        return threat_score
    
    def apply_captures(self, active_spot, board, active_color):
        """Apply capture logic following 'Suicide First, Self-Harm Priority'."""
        result_board = list(board)
        
        # Step 1: Suicide check (active piece dies first)
        if self.is_captured_at(active_spot, result_board):
            result_board[active_spot] = ''
            return result_board
        
        # Step 2a: Remove friendly pieces (self-harm priority)
        for spot in range(24):
            if spot != active_spot and result_board[spot] == active_color:
                if self.is_captured_at(spot, result_board):
                    result_board[spot] = ''
        
        # Step 2b: Remove enemy pieces
        opponent_color = 'W' if active_color == 'B' else 'B'
        for spot in range(24):
            if result_board[spot] == opponent_color:
                if self.is_captured_at(spot, result_board):
                    result_board[spot] = ''
        
        return result_board
    
    def is_captured_at(self, spot, board):
        """Check if piece at spot is captured (overwhelmed)."""
        if board[spot] == '':
            return False
        
        color = board[spot]
        empty_count = 0
        friendly_count = 0
        opponent_count = 0
        
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty_count += 1
            elif board[neighbor] == color:
                friendly_count += 1
            else:
                opponent_count += 1
        
        # Capture: zero empty AND more opponents than friendlies
        return empty_count == 0 and opponent_count > friendly_count
    
    def has_no_moves(self, board, color):
        """Check if player has no legal moves (mated)."""
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        return False
        return True
