"""
Agent Code: A8-SurroundMorris
Model: xiaomi/mimo-v2-flash
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
        self.opponent_color = 'W' if color == 'B' else 'B'
        
        # Define adjacency graph (same as provided in the problem)
        self.ADJACENCY = {
            0: [1, 9],       1: [0, 2, 4],     2: [1, 14],
            3: [4, 10],      4: [1, 3, 5, 7],  5: [4, 13],
            6: [7, 11],      7: [4, 6, 8],     8: [7, 12],
            9: [0, 10, 21],  10: [3, 9, 11, 18], 11: [6, 10, 15],
            12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
            15: [11, 16],    16: [15, 17, 19],  17: [12, 16],
            18: [10, 19],    19: [16, 18, 20, 22], 20: [13, 19],
            21: [9, 22],     22: [19, 21, 23],  23: [14, 22],
        }
        
        # Strategic positions (central and corners)
        self.CENTRAL = [4, 10, 13, 19]
        self.CORNERS = [0, 2, 6, 8, 15, 17, 21, 23]
        self.T_JUNCTIONS = [1, 3, 5, 7, 12, 14, 16, 18, 9, 11, 20, 22]

    def is_captured(self, board, spot, color):
        """Check if a piece at spot would be captured."""
        if board[spot] != color:
            return False
            
        empty_neighbors = 0
        friendly_neighbors = 0
        opponent_neighbors = 0
        
        for neighbor in self.ADJACENCY[spot]:
            if board[neighbor] == '':
                empty_neighbors += 1
            elif board[neighbor] == color:
                friendly_neighbors += 1
            else:
                opponent_neighbors += 1
                
        return empty_neighbors == 0 and opponent_neighbors > friendly_neighbors

    def simulate_move(self, board, move, mover_color):
        """Simulate a move and apply capture rules."""
        new_board = board[:]
        from_spot, to_spot = move
        
        # Make the move
        new_board[to_spot] = mover_color
        new_board[from_spot] = ''
        
        # Step 1: Check active piece for suicide
        if self.is_captured(new_board, to_spot, mover_color):
            new_board[to_spot] = ''
            return new_board
            
        # Step 2: Universal capture sweep
        opponent_color = self.opponent_color if mover_color == self.color else self.color
        
        # Step 2a: Remove friendly pieces first
        friendly_to_remove = []
        for spot in range(24):
            if new_board[spot] == mover_color and self.is_captured(new_board, spot, mover_color):
                friendly_to_remove.append(spot)
        for spot in friendly_to_remove:
            new_board[spot] = ''
            
        # Step 2b: Remove enemy pieces
        enemy_to_remove = []
        for spot in range(24):
            if new_board[spot] == opponent_color and self.is_captured(new_board, spot, opponent_color):
                enemy_to_remove.append(spot)
        for spot in enemy_to_remove:
            new_board[spot] = ''
            
        return new_board

    def generate_moves(self, board, color):
        """Generate all legal moves for the given color."""
        moves = []
        for spot in range(24):
            if board[spot] == color:
                for neighbor in self.ADJACENCY[spot]:
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
        return moves

    def evaluate_board(self, board, color):
        """Evaluate the board position from the perspective of the given color."""
        opponent_color = self.opponent_color if color == self.color else self.color
        
        our_pieces = board.count(color)
        opp_pieces = board.count(opponent_color)
        
        # Terminal conditions
        if our_pieces == 0:
            return -10000
        if opp_pieces == 0:
            return 10000
            
        # Material advantage
        material = (our_pieces - opp_pieces) * 100
        
        # Mobility: number of legal moves available
        our_moves = len(self.generate_moves(board, color))
        opp_moves = len(self.generate_moves(board, opponent_color))
        mobility = (our_moves - opp_moves) * 2
        
        # Positional value: control of central positions
        central_control = 0
        for spot in self.CENTRAL:
            if board[spot] == color:
                central_control += 5
            elif board[spot] == opponent_color:
                central_control -= 5
                
        # Safety: number of empty neighbors for our pieces
        our_safety = 0
        opp_safety = 0
        for spot in range(24):
            if board[spot] == color:
                empty_neighbors = sum(1 for n in self.ADJACENCY[spot] if board[n] == '')
                our_safety += empty_neighbors
            elif board[spot] == opponent_color:
                empty_neighbors = sum(1 for n in self.ADJACENCY[spot] if board[n] == '')
                opp_safety += empty_neighbors
        safety = (our_safety - opp_safety) * 0.5
        
        return material + mobility + central_control + safety

    def minimax(self, board, depth, alpha, beta, maximizing_player, current_turn_color):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return self.evaluate_board(board, self.color)
            
        moves = self.generate_moves(board, current_turn_color)
        
        # Check for mate (no legal moves)
        if len(moves) == 0:
            if current_turn_color == self.color:
                return -10000  # We are mated
            else:
                return 10000   # Opponent is mated
                
        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                new_board = self.simulate_move(board, move, current_turn_color)
                next_turn = self.opponent_color if current_turn_color == self.color else self.color
                eval_score = self.minimax(new_board, depth-1, alpha, beta, False, next_turn)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = self.simulate_move(board, move, current_turn_color)
                next_turn = self.opponent_color if current_turn_color == self.color else self.color
                eval_score = self.minimax(new_board, depth-1, alpha, beta, True, next_turn)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate_placement(self, board, spot, color):
        """Evaluate a placement move."""
        # Check for suicide
        empty_neighbors = 0
        friendly_neighbors = 0
        opponent_neighbors = 0
        
        for neighbor in self.ADJACENCY[spot]:
            if board[neighbor] == '':
                empty_neighbors += 1
            elif board[neighbor] == color:
                friendly_neighbors += 1
            else:
                opponent_neighbors += 1
                
        # Heavy penalty for suicide
        if empty_neighbors == 0 and opponent_neighbors > friendly_neighbors:
            return -10000
            
        # Prefer central positions
        if spot in self.CENTRAL:
            base_score = 20
        elif spot in self.T_JUNCTIONS:
            base_score = 10
        else:  # corners
            base_score = 5
            
        # Bonus for having empty neighbors
        base_score += empty_neighbors * 2
        
        # Bonus for blocking opponent clusters
        opponent_adjacent = opponent_neighbors
        base_score += opponent_adjacent * 1
        
        # Bonus for building our clusters
        friendly_adjacent = friendly_neighbors
        base_score += friendly_adjacent * 1
        
        return base_score

    def make_move(self, state, feedback=None):
        """
        Called each turn. Return your move based on the current game state.
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        
        if phase == "placement":
            # Placement phase
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0  # Should not happen
                
            # Evaluate each empty spot
            best_score = -float('inf')
            best_spot = empty_spots[0]
            
            for spot in empty_spots:
                score = self.evaluate_placement(board, spot, color)
                if score > best_score:
                    best_score = score
                    best_spot = spot
                    
            return best_spot
            
        else:
            # Movement phase
            moves = self.generate_moves(board, color)
            if not moves:
                # No legal moves - should not happen if game engine works correctly
                return (0, 1)
                
            # Use minimax to evaluate moves
            best_move = None
            best_value = -float('inf')
            
            for move in moves:
                new_board = self.simulate_move(board, move, color)
                # Check for repetition in history
                new_board_tuple = tuple(new_board)
                new_state = (new_board_tuple, self.opponent_color)
                repetition_count = state["history"].count(new_state)
                
                if repetition_count >= 2:
                    # This would cause a draw - avoid if we're ahead, seek if behind
                    our_pieces = new_board.count(color)
                    opp_pieces = new_board.count(self.opponent_color)
                    if our_pieces > opp_pieces:
                        value = -5000  # Avoid draw when ahead
                    elif our_pieces < opp_pieces:
                        value = 5000   # Seek draw when behind
                    else:
                        value = 0
                else:
                    # Normal minimax evaluation
                    value = self.minimax(new_board, 2, -float('inf'), float('inf'), False, self.opponent_color)
                
                if value > best_value:
                    best_value = value
                    best_move = move
                    
            return best_move if best_move else moves[0]
