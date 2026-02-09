"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-coder-next
Run: 2
Generated: 2026-02-09 19:15:26
"""

from collections import defaultdict

import random
from collections import defaultdict

# ADJACENCY is provided as a global variable at runtime, but we'll include it for completeness
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
        self.opponent_color = 'W' if color == 'B' else 'B'
        self.attempts = defaultdict(int)  # Track attempts per turn to avoid infinite loops

    def _count_neighbors(self, spot, board, color_to_count):
        """Count neighbors of a specific color at a spot."""
        count = 0
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == color_to_count:
                count += 1
        return count

    def _count_empty_neighbors(self, spot, board):
        """Count empty neighbors at a spot."""
        count = 0
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                count += 1
        return count

    def _is_captured(self, spot, board):
        """Check if a piece at spot should be captured."""
        piece = board[spot]
        if piece == '':
            return False
        
        empty_neighbors = self._count_empty_neighbors(spot, board)
        if empty_neighbors > 0:
            return False
        
        # Count friendlies and opponents
        friendly_neighbors = self._count_neighbors(spot, board, piece)
        opponent_neighbors = self._count_neighbors(spot, board, self.opponent_color if piece == self.color else self.color)
        
        return opponent_neighbors > friendly_neighbors

    def _get_legal_placements(self, board):
        """Get all legal placement spots."""
        return [i for i in range(24) if board[i] == '']

    def _get_legal_movements(self, board, color):
        """Get all legal movement moves for a color."""
        moves = []
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
        return moves

    def _simulate_move_and_check_captures(self, board, move, color):
        """
        Simulate a move and return which pieces would be captured.
        Returns a list of spots that would be captured (in order: active piece first, then others per rules).
        """
        new_board = board.copy()
        
        # Handle placement
        if isinstance(move, int):
            new_board[move] = color
            active_spot = move
        # Handle movement
        else:
            from_spot, to_spot = move
            new_board[to_spot] = color
            new_board[from_spot] = ''
            active_spot = to_spot
        
        captured_spots = []
        
        # Step 1: Check if active piece commits suicide
        if self._is_captured(active_spot, new_board):
            captured_spots.append(active_spot)
            return captured_spots  # Active piece dies, nothing else happens
        
        # Step 2: Universal capture sweep
        # Step 2a: Check all friendly pieces (same color as mover)
        friendly_spots = [i for i in range(24) if new_board[i] == color]
        for spot in friendly_spots:
            if spot != active_spot and self._is_captured(spot, new_board):
                captured_spots.append(spot)
        
        # Remove captured friendly pieces from board to re-evaluate enemy pieces
        temp_board = new_board.copy()
        for spot in captured_spots:
            temp_board[spot] = ''
        
        # Step 2b: Check all enemy pieces again
        enemy_spots = [i for i in range(24) if temp_board[i] != '' and temp_board[i] != color]
        for spot in enemy_spots:
            if self._is_captured(spot, temp_board):
                captured_spots.append(spot)
        
        return captured_spots

    def _get_captured_after_move(self, board, move, color):
        """Get list of spots captured after making the move."""
        return self._simulate_move_and_check_captures(board, move, color)

    def _evaluate_board(self, board):
        """Simple evaluation function for board state."""
        score = 0
        
        # Count pieces
        my_count = sum(1 for cell in board if cell == self.color)
        opp_count = sum(1 for cell in board if cell == self.opponent_color)
        score += (my_count - opp_count) * 10
        
        # Control central spots (crossroads: 4, 10, 13, 19)
        central_spots = [4, 10, 13, 19]
        my_center = sum(1 for spot in central_spots if board[spot] == self.color)
        opp_center = sum(1 for spot in central_spots if board[spot] == self.opponent_color)
        score += (my_center - opp_center) * 5
        
        # Check for potential captures
        for spot in range(24):
            if board[spot] == self.color:
                empty_neighbors = self._count_empty_neighbors(spot, board)
                if empty_neighbors == 0:
                    friendly_neighbors = self._count_neighbors(spot, board, self.color)
                    opp_neighbors = self._count_neighbors(spot, board, self.opponent_color)
                    if opp_neighbors > friendly_neighbors:
                        score -= 20  # My piece is about to be captured
            elif board[spot] == self.opponent_color:
                empty_neighbors = self._count_empty_neighbors(spot, board)
                if empty_neighbors == 0:
                    friendly_neighbors = self._count_neighbors(spot, board, self.opponent_color)
                    opp_neighbors = self._count_neighbors(spot, board, self.color)
                    if opp_neighbors > friendly_neighbors:
                        score += 20  # Opponent piece is about to be captured
        
        return score

    def _is_repetition(self, board_tuple, current_player, history):
        """Check if the current position has occurred 2+ times before."""
        count = 0
        for (board_t, player) in history:
            if board_t == board_tuple and player == current_player:
                count += 1
        return count >= 2  # 3 total occurrences (including current) means repetition

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Called each turn. Return your move based on the current game state.
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        # Track attempts per turn
        turn_key = tuple(board) + (color,)
        if feedback is not None:
            self.attempts[turn_key] += 1
        else:
            self.attempts[turn_key] = 1
        
        # Safety: if too many attempts, return random move
        if self.attempts[turn_key] > 3:
            if phase == "placement":
                empty = [i for i in range(24) if board[i] == '']
                return random.choice(empty) if empty else 0
            else:
                moves = self._get_legal_movements(board, color)
                return random.choice(moves) if moves else (0, 1)
        
        # Handle repetition check
        board_tuple = tuple(board)
        history = state.get("history", [])
        if phase == "movement" and self._is_repetition(board_tuple, color, history):
            # Try to avoid repetition by finding a different move
            pass  # We'll handle this in move selection below
        
        if phase == "placement":
            empty_spots = self._get_legal_placements(board)
            if not empty_spots:
                return 0
            
            # Try to find best placement
            best_spot = None
            best_score = float('-inf')
            
            for spot in empty_spots:
                # Check if suicide
                new_board = board.copy()
                new_board[spot] = color
                captured = self._simulate_move_and_check_captures(board, spot, color)
                
                # Suicide is usually bad
                if spot in captured:
                    score = -100
                else:
                    # Evaluate resulting board state
                    score = self._evaluate_board(new_board)
                    # Bonus for not dying
                    score += 10
                
                # Prefer central spots if scores are similar
                if spot in [4, 10, 13, 19]:
                    score += 3
                
                if score > best_score:
                    best_score = score
                    best_spot = spot
            
            # Fallback: random if no clear best
            if best_spot is None:
                best_spot = random.choice(empty_spots)
            
            return best_spot
        
        else:  # Movement phase
            moves = self._get_legal_movements(board, color)
            if not moves:
                return (0, 1)  # No moves - will lose, but return something valid
            
            # Check for mate (no moves) - but we already handled that with empty moves list
            
            # Try to find best movement
            best_move = None
            best_score = float('-inf')
            
            # First check if any move immediately captures opponent
            immediate_captures = []
            
            for move in moves:
                captured = self._get_captured_after_move(board, move, color)
                opp_captures = [s for s in captured if board[s] == opp]
                
                if opp_captures:
                    # Prefer moves that capture more enemy pieces
                    immediate_captures.append((move, len(opp_captures)))
            
            # If there are immediate captures, prefer those
            if immediate_captures:
                # Sort by number of captures descending
                immediate_captures.sort(key=lambda x: -x[1])
                # Among captures with same count, prefer those that don't cause self-capture
                for move, count in immediate_captures:
                    captured = self._get_captured_after_move(board, move, color)
                    if move[1] not in captured:  # Active piece survives
                        best_move = move
                        break
                
                if best_move is None:
                    # If all capture moves kill self, pick one that kills most enemies but doesn't kill self
                    for move, count in immediate_captures:
                        captured = self._get_captured_after_move(board, move, color)
                        if move[1] in captured:
                            # Check if enemy pieces also die - if so, might be worth it
                            if len([s for s in captured if board[s] == opp]) > 0:
                                best_move = move
                                break
                    if best_move is None:
                        # If all captures kill self and no enemies die, pick random capture
                        best_move = immediate_captures[0][0]
            else:
                # No immediate captures - evaluate moves
                for move in moves:
                    # Simulate move
                    new_board = board.copy()
                    from_spot, to_spot = move
                    new_board[to_spot] = color
                    new_board[from_spot] = ''
                    
                    # Check if active piece survives
                    captured = self._get_captured_after_move(board, move, color)
                    active_survives = to_spot not in captured
                    
                    # Check for friendly fire
                    friendly_captured = [s for s in captured if board[s] == color]
                    enemy_captured = [s for s in captured if board[s] == opp]
                    
                    # Score calculation
                    score = self._evaluate_board(new_board)
                    
                    # Bonus for active piece survival
                    if active_survives:
                        score += 5
                    
                    # Penalty for losing friendly pieces
                    score -= len(friendly_captured) * 10
                    
                    # Bonus for capturing enemies
                    score += len(enemy_captured) * 15
                    
                    # Prefer moves that don't block other friendly pieces
                    # Check if the move opens up space for other pieces
                    # This is complex, so we'll stick with basic heuristics
                    
                    if score > best_score:
                        best_score = score
                        best_move = move
                
                # If best_move is still None, pick random
                if best_move is None:
                    best_move = random.choice(moves)
            
            # Avoid repetition if possible
            if best_move:
                # Try to find alternative moves if current best leads to repetition
                board_tuple = tuple(board)
                history = state.get("history", [])
                
                # Try to find a non-repeating move with similar score
                for move in moves:
                    if move == best_move:
                        continue
                    
                    new_board = board.copy()
                    from_spot, to_spot = move
                    new_board[to_spot] = color
                    new_board[from_spot] = ''
                    new_board_tuple = tuple(new_board)
                    
                    if not self._is_repetition(new_board_tuple, opp, history):
                        # Check if this move is almost as good
                        move_score = self._evaluate_board(new_board)
                        if move_score >= best_score - 2:  # Small tolerance
                            best_move = move
                            break
            
            return best_move
