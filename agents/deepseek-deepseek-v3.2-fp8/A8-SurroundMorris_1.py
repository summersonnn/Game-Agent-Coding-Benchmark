"""
Agent Code: A8-SurroundMorris
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 1
Generated: 2026-02-09 18:53:48
"""

import random
from copy import deepcopy

class SurroundMorrisAgent:
    """
    Strategic agent for Surround Morris game.
    """
    
    def __init__(self, name: str, color: str):
        """
        Initialize your agent.
        """
        self.name = name
        self.color = color
        self.opponent_color = 'W' if color == 'B' else 'B'
        self.spot_values = self._calculate_spot_values()
        
    def _calculate_spot_values(self):
        """
        Calculate strategic values for each board position.
        Higher values indicate more important positions.
        """
        # Define position importance based on connectivity and strategic value
        values = {}
        
        # Crossroads (4 neighbors) - most valuable
        crossroads = [4, 10, 13, 19]
        for spot in crossroads:
            values[spot] = 4.0
            
        # T-junctions (3 neighbors) - medium value
        tjunctions = [1, 3, 5, 6, 8, 9, 14, 15, 17, 18, 20, 22]
        for spot in tjunctions:
            values[spot] = 2.5
            
        # Corners (2 neighbors) - low value (easy to trap)
        corners = [0, 2, 21, 23]
        for spot in corners:
            values[spot] = 1.5
            
        # Edge midpoints (3 neighbors but less central)
        edges = [7, 11, 12, 16]
        for spot in edges:
            values[spot] = 2.0
            
        return values
    
    def _get_adjacent_empty_spots(self, board, spot):
        """Get empty adjacent spots for a given position."""
        return [n for n in ADJACENCY[spot] if board[n] == '']
    
    def _get_neighbor_counts(self, board, spot, color):
        """Count friendly, opponent, and empty neighbors."""
        if board[spot] == '':
            return 0, 0, 0
            
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
        """
        Check if placing/moving to spot would cause immediate capture.
        """
        # Temporarily place piece
        temp_board = board[:]
        temp_board[spot] = color
        
        friendly, opponent, empty = self._get_neighbor_counts(temp_board, spot, color)
        
        # Check suicide condition (active piece first)
        if empty == 0 and opponent > friendly:
            return True
            
        return False
    
    def _evaluate_position(self, board, color):
        """
        Evaluate board position from perspective of given color.
        Returns a score where higher is better for the color.
        """
        score = 0
        opponent = 'W' if color == 'B' else 'B'
        
        # Material count (pieces on board)
        material_score = (board.count(color) - board.count(opponent)) * 100
        
        # Position control
        position_score = 0
        for i in range(24):
            if board[i] == color:
                position_score += self.spot_values.get(i, 1.0)
            elif board[i] == opponent:
                position_score -= self.spot_values.get(i, 1.0)
        
        # Mobility (empty adjacent spots)
        mobility_score = 0
        for i in range(24):
            if board[i] == color:
                empty_neighbors = len(self._get_adjacent_empty_spots(board, i))
                mobility_score += empty_neighbors * 3
            elif board[i] == opponent:
                empty_neighbors = len(self._get_adjacent_empty_spots(board, i))
                mobility_score -= empty_neighbors * 2
        
        # Threat assessment (pieces that could be captured)
        threat_score = 0
        for i in range(24):
            if board[i] == color:
                friendly, opponent_count, empty = self._get_neighbor_counts(board, i, color)
                if empty == 0 and opponent_count > friendly:
                    threat_score -= 50  # Our piece is threatened
            elif board[i] == opponent:
                opponent_friendly, my_count, empty = self._get_neighbor_counts(board, i, opponent)
                if empty == 0 and my_count > opponent_friendly:
                    threat_score += 40  # Opponent piece is threatened
        
        # Control of crossroads
        crossroads = [4, 10, 13, 19]
        crossroad_score = 0
        for spot in crossroads:
            if board[spot] == color:
                crossroad_score += 15
            elif board[spot] == opponent:
                crossroad_score -= 10
        
        # Avoid repetition penalty
        repetition_penalty = 0
        # Already handled in main move selection
        
        total_score = (
            material_score +
            position_score * 5 +
            mobility_score +
            threat_score +
            crossroad_score
        )
        
        return total_score
    
    def _simulate_move(self, board, move, color, phase):
        """
        Simulate a move and return resulting board.
        """
        new_board = board[:]
        
        if phase == "placement":
            spot = move
            new_board[spot] = color
            
            # Apply capture rules (simplified simulation)
            # Active piece suicide check
            friendly, opponent, empty = self._get_neighbor_counts(new_board, spot, color)
            if empty == 0 and opponent > friendly:
                new_board[spot] = ''  # Suicide
                return new_board
            
            # Check for other captures (simplified - doesn't handle self-harm priority perfectly)
            # This is a heuristic approximation
            for i in range(24):
                if new_board[i] != '' and new_board[i] != color:  # Only check opponent pieces
                    opp = new_board[i]
                    f, o, e = self._get_neighbor_counts(new_board, i, opp)
                    if e == 0 and o > f:
                        new_board[i] = ''
                        
        else:  # movement
            from_spot, to_spot = move
            new_board[from_spot] = ''
            new_board[to_spot] = color
            
            # Apply capture rules (simplified simulation)
            # Active piece suicide check
            friendly, opponent, empty = self._get_neighbor_counts(new_board, to_spot, color)
            if empty == 0 and opponent > friendly:
                new_board[to_spot] = ''  # Suicide
                return new_board
            
            # Simplified capture sweep (heuristic)
            # Check our pieces first (self-harm priority)
            for i in range(24):
                if new_board[i] == color:
                    f, o, e = self._get_neighbor_counts(new_board, i, color)
                    if e == 0 and o > f:
                        new_board[i] = ''
            
            # Then check opponent pieces
            for i in range(24):
                if new_board[i] == self.opponent_color:
                    f, o, e = self._get_neighbor_counts(new_board, i, self.opponent_color)
                    if e == 0 and o > f:
                        new_board[i] = ''
        
        return new_board
    
    def _get_placement_moves(self, board):
        """Get all possible placement moves."""
        return [i for i in range(24) if board[i] == '']
    
    def _get_movement_moves(self, board, color):
        """Get all possible movement moves."""
        moves = []
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
        return moves
    
    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Called each turn. Return your move based on the current game state.
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opponent = state["opponent_color"]
        history = state["history"]
        
        if phase == "placement":
            # Get all possible placements
            possible_moves = self._get_placement_moves(board)
            
            # Avoid suicide unless it's strategically advantageous
            safe_moves = []
            risky_moves = []
            
            for spot in possible_moves:
                if self._would_be_captured(board, spot, color):
                    risky_moves.append(spot)
                else:
                    safe_moves.append(spot)
            
            # Prefer safe moves
            if safe_moves:
                move_pool = safe_moves
            else:
                move_pool = possible_moves  # All moves if no safe ones
            
            # Evaluate each move
            best_score = -float('inf')
            best_moves = []
            
            for spot in move_pool:
                # Quick filter: avoid placing in opponent's strong positions early
                if board.count(color) < 4:  # Early game
                    opponent_adjacent = 0
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == opponent:
                            opponent_adjacent += 1
                    if opponent_adjacent >= 2:
                        continue  # Avoid placing between two opponents
                
                # Simulate move
                new_board = self._simulate_move(board, spot, color, phase)
                score = self._evaluate_position(new_board, color)
                
                # Bonus for controlling valuable spots
                score += self.spot_values.get(spot, 1.0) * 2
                
                # Bonus for creating threats
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == opponent:
                        f, o, e = self._get_neighbor_counts(new_board, neighbor, opponent)
                        if e == 0 and o > f:
                            score += 20  # We threaten this piece
                
                if score > best_score:
                    best_score = score
                    best_moves = [spot]
                elif abs(score - best_score) < 0.1:
                    best_moves.append(spot)
            
            # Choose randomly among best moves
            return random.choice(best_moves) if best_moves else random.choice(move_pool)
            
        else:  # Movement phase
            # Get all possible movements
            possible_moves = self._get_movement_moves(board, color)
            
            if not possible_moves:
                # No legal moves - we're mated (return any move, engine will handle loss)
                return (0, 1)
            
            # Check for immediate winning moves
            for from_spot, to_spot in possible_moves:
                # Simulate the move
                new_board = self._simulate_move(board, (from_spot, to_spot), color, phase)
                
                # Check if opponent has no pieces left
                if new_board.count(opponent) == 0:
                    return (from_spot, to_spot)
                
                # Check if we put opponent in mate
                opponent_moves = self._get_movement_moves(new_board, opponent)
                if not opponent_moves:
                    return (from_spot, to_spot)
            
            # Avoid moves that lead to repetition if we're winning
            current_eval = self._evaluate_position(board, color)
            avoid_repetition = current_eval > 20  # If we're winning, avoid draws
            
            # Evaluate each move
            best_score = -float('inf')
            best_moves = []
            
            for from_spot, to_spot in possible_moves:
                # Avoid suicide unless it captures many opponent pieces
                if self._would_be_captured(board, to_spot, color):
                    # Check if this suicide captures important opponent pieces
                    new_board = self._simulate_move(board, (from_spot, to_spot), color, phase)
                    opponent_pieces_before = board.count(opponent)
                    opponent_pieces_after = new_board.count(opponent)
                    if opponent_pieces_before - opponent_pieces_after < 2:
                        continue  # Suicide not worth it
                
                # Simulate move
                new_board = self._simulate_move(board, (from_spot, to_spot), color, phase)
                score = self._evaluate_position(new_board, color)
                
                # Penalize moving from valuable positions to less valuable ones
                from_value = self.spot_values.get(from_spot, 1.0)
                to_value = self.spot_values.get(to_spot, 1.0)
                if to_value < from_value * 0.7:
                    score -= 15
                
                # Bonus for capturing opponent pieces
                opponent_before = board.count(opponent)
                opponent_after = new_board.count(opponent)
                captures = opponent_before - opponent_after
                score += captures * 80
                
                # Penalty for losing our pieces
                our_before = board.count(color)
                our_after = new_board.count(color)
                losses = our_before - our_after
                score -= losses * 100
                
                # Bonus for improving mobility
                our_mobility_before = len(self._get_movement_moves(board, color))
                our_mobility_after = len(self._get_movement_moves(new_board, color))
                score += (our_mobility_after - our_mobility_before) * 5
                
                # Penalty for reducing opponent's mobility if it helps them avoid mate
                opponent_mobility_before = len(self._get_movement_moves(board, opponent))
                opponent_mobility_after = len(self._get_movement_moves(new_board, opponent))
                
                # Only penalize if we're not trying to mate them
                if opponent_mobility_after == 0:
                    score += 100  # We mated them!
                elif opponent_mobility_before < 4 and opponent_mobility_after < opponent_mobility_before:
                    # Be careful not to help opponent by reducing options when they're almost mated
                    score -= 20
                
                # Check for repetition
                if avoid_repetition:
                    board_tuple = tuple(new_board)
                    if (board_tuple, opponent) in history:
                        # This move would repeat a position
                        repetitions = history.count((board_tuple, opponent))
                        if repetitions >= 1:  # Would be 2nd occurrence
                            score -= 50 * (repetitions + 1)
                
                # Small random factor to avoid deterministic play
                score += random.uniform(0, 0.1)
                
                if score > best_score:
                    best_score = score
                    best_moves = [(from_spot, to_spot)]
                elif abs(score - best_score) < 0.1:
                    best_moves.append((from_spot, to_spot))
            
            # Choose randomly among best moves
            return random.choice(best_moves) if best_moves else random.choice(possible_moves)