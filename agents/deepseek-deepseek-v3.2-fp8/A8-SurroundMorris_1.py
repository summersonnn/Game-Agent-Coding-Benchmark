"""
Agent Code: A8-SurroundMorris
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 1
Generated: 2026-02-09 18:54:48
"""

from typing import List, Tuple, Dict, Optional
import math

class SurroundMorrisAgent:
    """
    Smart agent for Surround Morris game.
    Uses minimax with alpha-beta pruning and heuristic evaluation.
    """
    
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opponent_color = 'W' if color == 'B' else 'B'
        
        # Position values based on strategic importance
        self.position_values = {
            4: 3.0, 10: 3.0, 13: 3.0, 19: 3.0,  # Crossroads - most valuable
            1: 2.0, 3: 2.0, 5: 2.0, 7: 2.0,     # T-junctions
            9: 2.0, 11: 2.0, 12: 2.0, 14: 2.0,
            15: 2.0, 17: 2.0, 18: 2.0, 20: 2.0,
            21: 2.0, 23: 2.0,
            0: 1.5, 2: 1.5, 6: 1.5, 8: 1.5,     # Corners - easier to trap
            16: 1.5, 22: 1.5
        }
        
        # Search depth - adjust based on performance
        self.placement_depth = 3
        self.movement_depth = 3
        
        # Transposition table for caching evaluations
        self.transposition_table = {}
        
    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Make a move based on the current game state.
        """
        board = state["board"]
        phase = state["phase"]
        
        if phase == "placement":
            # Get all legal placements (all empty spots)
            legal_moves = [i for i in range(24) if board[i] == '']
            
            # If few pieces left or first few moves, use simpler evaluation
            if len(legal_moves) > 18 or state["pieces_in_hand"][self.color] >= 6:
                # Early game - prioritize strategic positions
                return self._choose_best_placement(state, legal_moves)
            else:
                # Mid-late placement - use minimax
                best_move = self._minimax_placement(state, depth=self.placement_depth)
                return best_move if best_move is not None else legal_moves[0]
                
        else:  # Movement phase
            # Get all legal movements
            legal_moves = []
            for spot in range(24):
                if board[spot] == self.color:
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == '':
                            legal_moves.append((spot, neighbor))
            
            if not legal_moves:
                # No legal moves - shouldn't happen as game would end
                return (0, 1) if 0 < 24 and 1 < 24 else legal_moves[0] if legal_moves else (0, 1)
            
            # Use minimax for movement
            best_move = self._minimax_movement(state, depth=self.movement_depth)
            return best_move if best_move is not None else legal_moves[0]
    
    def _choose_best_placement(self, state: dict, legal_moves: List[int]) -> int:
        """
        Choose placement based on heuristic evaluation.
        Prioritizes central positions and avoids immediate capture.
        """
        board = state["board"]
        best_score = -float('inf')
        best_move = legal_moves[0]
        
        for move in legal_moves:
            # Simulate placement
            new_board = board.copy()
            new_board[move] = self.color
            
            # Check if this move would cause suicide
            if self._is_captured(move, new_board, self.color):
                # Suicide is bad unless it achieves something special
                score = -1000
            else:
                # Evaluate position
                score = self._evaluate_board(new_board, self.color)
                
                # Add position value
                score += self.position_values.get(move, 1.0)
                
                # Check if this threatens opponent pieces
                for neighbor in ADJACENCY[move]:
                    if new_board[neighbor] == self.opponent_color:
                        # Count how many opponent neighbors this piece has
                        opp_neighbors = sum(1 for n in ADJACENCY[neighbor] 
                                          if new_board[n] == self.opponent_color)
                        empty_neighbors = sum(1 for n in ADJACENCY[neighbor] 
                                            if new_board[n] == '')
                        friendly_neighbors = sum(1 for n in ADJACENCY[neighbor] 
                                               if new_board[n] == self.color)
                        
                        # If opponent piece is now surrounded or close to being surrounded
                        if empty_neighbors == 0 and friendly_neighbors > opp_neighbors:
                            score += 5.0  # Threat bonus
                        elif empty_neighbors == 1 and friendly_neighbors >= opp_neighbors:
                            score += 2.0  # Potential threat
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _minimax_placement(self, state: dict, depth: int) -> Optional[int]:
        """
        Minimax search for placement phase.
        """
        board = state["board"]
        legal_moves = [i for i in range(24) if board[i] == '']
        
        if not legal_moves:
            return None
        
        best_score = -float('inf')
        best_move = legal_moves[0]
        alpha = -float('inf')
        beta = float('inf')
        
        for move in legal_moves:
            # Simulate move
            new_state = self._simulate_placement(state, move)
            
            # Evaluate with minimax
            score = self._minimax(new_state, depth-1, False, alpha, beta)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        return best_move
    
    def _minimax_movement(self, state: dict, depth: int) -> Optional[Tuple[int, int]]:
        """
        Minimax search for movement phase.
        """
        board = state["board"]
        legal_moves = []
        for spot in range(24):
            if board[spot] == self.color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        legal_moves.append((spot, neighbor))
        
        if not legal_moves:
            return None
        
        best_score = -float('inf')
        best_move = legal_moves[0]
        alpha = -float('inf')
        beta = float('inf')
        
        for move in legal_moves:
            # Simulate move
            new_state = self._simulate_movement(state, move)
            
            # Evaluate with minimax
            score = self._minimax(new_state, depth-1, False, alpha, beta)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        return best_move
    
    def _minimax(self, state: dict, depth: int, maximizing: bool, 
                 alpha: float, beta: float) -> float:
        """
        Minimax algorithm with alpha-beta pruning.
        """
        # Check terminal conditions
        terminal_score = self._check_terminal(state)
        if terminal_score is not None:
            return terminal_score
        
        if depth == 0:
            return self._evaluate_state(state)
        
        board = state["board"]
        phase = state["phase"]
        current_player = state["your_color"] if maximizing else state["opponent_color"]
        
        if phase == "placement":
            legal_moves = [i for i in range(24) if board[i] == '']
            if not legal_moves:
                return self._evaluate_state(state)
            
            if maximizing:
                max_eval = -float('inf')
                for move in legal_moves:
                    new_state = self._simulate_placement(state, move)
                    eval_score = self._minimax(new_state, depth-1, False, alpha, beta)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
                return max_eval
            else:
                min_eval = float('inf')
                for move in legal_moves:
                    new_state = self._simulate_placement(state, move)
                    eval_score = self._minimax(new_state, depth-1, True, alpha, beta)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
                return min_eval
        else:  # Movement phase
            legal_moves = []
            for spot in range(24):
                if board[spot] == current_player:
                    for neighbor in ADJACENCY[spot]:
                        if board[neighbor] == '':
                            legal_moves.append((spot, neighbor))
            
            if not legal_moves:  # Stalemate
                return -7 if maximizing else 7
            
            if maximizing:
                max_eval = -float('inf')
                for move in legal_moves:
                    new_state = self._simulate_movement(state, move)
                    eval_score = self._minimax(new_state, depth-1, False, alpha, beta)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
                return max_eval
            else:
                min_eval = float('inf')
                for move in legal_moves:
                    new_state = self._simulate_movement(state, move)
                    eval_score = self._minimax(new_state, depth-1, True, alpha, beta)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
                return min_eval
    
    def _simulate_placement(self, state: dict, spot: int) -> dict:
        """
        Simulate a placement move and return new state.
        """
        board = state["board"].copy()
        board[spot] = self.color if state["your_color"] == self.color else self.opponent_color
        
        # Apply capture rules
        board = self._apply_captures(board, spot, state["your_color"])
        
        # Create new state
        new_state = state.copy()
        new_state["board"] = board
        new_state["pieces_in_hand"] = state["pieces_in_hand"].copy()
        new_state["pieces_on_board"] = state["pieces_on_board"].copy()
        
        player = state["your_color"]
        new_state["pieces_in_hand"][player] -= 1
        new_state["pieces_on_board"][player] = sum(1 for p in board if p == player)
        new_state["pieces_on_board"][self.opponent_color if player == self.color else self.color] = \
            sum(1 for p in board if p == (self.opponent_color if player == self.color else self.color))
        
        # Switch player
        new_state["your_color"], new_state["opponent_color"] = \
            new_state["opponent_color"], new_state["your_color"]
        
        # Check if placement phase is over
        if new_state["pieces_in_hand"]["B"] == 0 and new_state["pieces_in_hand"]["W"] == 0:
            new_state["phase"] = "movement"
        
        return new_state
    
    def _simulate_movement(self, state: dict, move: Tuple[int, int]) -> dict:
        """
        Simulate a movement move and return new state.
        """
        from_spot, to_spot = move
        board = state["board"].copy()
        player = state["your_color"]
        
        # Move the piece
        board[to_spot] = board[from_spot]
        board[from_spot] = ''
        
        # Apply capture rules
        board = self._apply_captures(board, to_spot, player)
        
        # Create new state
        new_state = state.copy()
        new_state["board"] = board
        new_state["pieces_on_board"] = {
            "B": sum(1 for p in board if p == "B"),
            "W": sum(1 for p in board if p == "W")
        }
        new_state["move_count"] = state["move_count"] + 1
        
        # Switch player
        new_state["your_color"], new_state["opponent_color"] = \
            new_state["opponent_color"], new_state["your_color"]
        
        return new_state
    
    def _apply_captures(self, board: List[str], moved_spot: int, mover_color: str) -> List[str]:
        """
        Apply capture rules after a move.
        Returns new board after captures.
        """
        board_copy = board.copy()
        opponent_color = 'W' if mover_color == 'B' else 'B'
        
        # Step 1: Check if moved piece is captured (suicide)
        if board_copy[moved_spot] == mover_color:
            if self._is_captured(moved_spot, board_copy, mover_color):
                board_copy[moved_spot] = ''
                return board_copy  # Suicide - no further captures
        
        # Step 2a: Remove overwhelmed friendly pieces
        friendly_to_remove = []
        for spot in range(24):
            if board_copy[spot] == mover_color:
                if self._is_captured(spot, board_copy, mover_color):
                    friendly_to_remove.append(spot)
        
        for spot in friendly_to_remove:
            board_copy[spot] = ''
        
        # Step 2b: Remove overwhelmed enemy pieces
        enemy_to_remove = []
        for spot in range(24):
            if board_copy[spot] == opponent_color:
                if self._is_captured(spot, board_copy, opponent_color):
                    enemy_to_remove.append(spot)
        
        for spot in enemy_to_remove:
            board_copy[spot] = ''
        
        return board_copy
    
    def _is_captured(self, spot: int, board: List[str], color: str) -> bool:
        """
        Check if piece at spot is captured according to rules.
        """
        if board[spot] != color:
            return False
        
        empty_neighbors = 0
        friendly_neighbors = 0
        opponent_neighbors = 0
        
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty_neighbors += 1
            elif board[neighbor] == color:
                friendly_neighbors += 1
            else:
                opponent_neighbors += 1
        
        # Capture condition: zero empty neighbors AND more opponent neighbors than friendly
        return empty_neighbors == 0 and opponent_neighbors > friendly_neighbors
    
    def _check_terminal(self, state: dict) -> Optional[float]:
        """
        Check for terminal game states.
        Returns score if terminal, None otherwise.
        """
        board = state["board"]
        pieces_on_board = state["pieces_on_board"]
        phase = state["phase"]
        
        # Check elimination
        if pieces_on_board[self.color] == 0:
            return -1000  # We lose
        if pieces_on_board[self.opponent_color] == 0:
            return 1000  # We win
