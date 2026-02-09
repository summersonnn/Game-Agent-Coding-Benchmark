"""
Agent Code: A8-SurroundMorris
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-09 18:54:48
"""

from collections import defaultdict

import random
from collections import defaultdict

# Adjacency graph (provided in the problem)
ADJACENCY = {
    0: [1, 9], 1: [0, 2, 4], 2: [1, 14],
    3: [4, 10], 4: [1, 3, 5, 7], 5: [4, 13],
    6: [7, 11], 7: [4, 6, 8], 8: [7, 12],
    9: [0, 10, 21], 10: [3, 9, 11, 18], 11: [6, 10, 15],
    12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
    15: [11, 16], 16: [15, 17, 19], 17: [12, 16],
    18: [10, 19], 19: [16, 18, 20, 22], 20: [13, 19],
    21: [9, 22], 22: [19, 21, 23], 23: [14, 22],
}

class SurroundMorrisAgent:
    """
    A strategic agent for Surround Morris.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opponent_color = 'W' if color == 'B' else 'B'
        # We'll use a transposition table for caching positions
        self.transposition_table = {}
        # For reproducibility, we can set a random seed based on name
        random.seed(hash(name) % 10000)

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        pieces_on_board = state["pieces_on_board"]
        move_count = state["move_count"]
        history = state["history"]

        if phase == "placement":
            return self.placement_move(board, color, opp, pieces_in_hand, pieces_on_board, history)
        else:
            return self.movement_move(board, color, opp, pieces_on_board, move_count, history)

    # -------------------------------------------------------------------------
    # Placement phase logic
    # -------------------------------------------------------------------------
    def placement_move(self, board, color, opp, pieces_in_hand, pieces_on_board, history):
        # Get all empty spots
        empty_spots = [i for i in range(24) if board[i] == '']
        # If we have only one piece left to place, we might consider suicide only if it's advantageous (rare).
        # But generally, we avoid suicide.

        # Heuristic: evaluate each placement spot
        best_score = -float('inf')
        best_spots = []
        for spot in empty_spots:
            # Simulate placing the piece
            new_board = board.copy()
            new_board[spot] = color
            # Apply capture rule (only the placed piece might be captured immediately)
            # We need to simulate the capture rule for the placed piece.
            # If the placed piece is captured, it's a suicide move.
            # We can call a function that returns the board after capture.
            after_board, _ = self.simulate_captures_after_placement(new_board, spot, color, opp)
            # Evaluate the resulting position
            score = self.evaluate_board(after_board, color, opp, pieces_in_hand, pieces_on_board, is_placement=True)
            # Avoid suicide if possible (unless it's the only move or gives huge advantage)
            # We penalize suicide moves heavily.
            if after_board[spot] == '':
                # Our piece was captured (suicide)
                score -= 50  # heavy penalty
            # Also, avoid placing in a spot that allows opponent to easily capture next turn
            # We can look at opponent's possible placements and see if they can capture our piece.
            # For simplicity, we'll just use the current evaluation.

            # Check for repetition: if this position has occurred twice before, avoid it if we are ahead.
            board_tuple = tuple(after_board)
            if (board_tuple, opp) in history:
                count = history.count((board_tuple, opp))
                if count >= 2:
                    # This would be the third time -> draw. If we are ahead, we want to avoid.
                    my_pieces = pieces_on_board[color] - 1 if after_board[spot] == '' else pieces_on_board[color]
                    opp_pieces = pieces_on_board[opp]
                    if my_pieces > opp_pieces:
                        score -= 30  # avoid repetition when ahead

            if score > best_score:
                best_score = score
                best_spots = [spot]
            elif score == best_score:
                best_spots.append(spot)

        # Choose randomly among the best spots
        return random.choice(best_spots)

    # -------------------------------------------------------------------------
    # Movement phase logic
    # -------------------------------------------------------------------------
    def movement_move(self, board, color, opp, pieces_on_board, move_count, history):
        # Generate all legal moves
        legal_moves = []
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        legal_moves.append((spot, neighbor))
        if not legal_moves:
            # No legal moves - we are mated. Return a dummy move (shouldn't happen often)
            return (0, 1)  # arbitrary, but the game will end anyway.

        # If we are in a winning position (opponent has few pieces), we can play more aggressively.
        # Use minimax with alpha-beta pruning to a certain depth.
        # We'll use a depth of 2 for speed, but can adjust.
        depth = 2
        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        # Order moves heuristically to improve pruning
        ordered_moves = self.order_moves(board, legal_moves, color, opp)

        for move in ordered_moves:
            from_spot, to_spot = move
            new_board = board.copy()
            new_board[from_spot] = ''
            new_board[to_spot] = color
            # Apply capture rule after the move
            after_board, _ = self.simulate_captures_after_move(new_board, to_spot, color, opp)
            # Evaluate the position from the opponent's perspective (we'll negate later)
            score = -self.minimax(after_board, depth-1, opp, color, -beta, -alpha, move_count+1, history)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        # If no move found (shouldn't happen), pick a random legal move
        if best_move is None:
            return random.choice(legal_moves)
        return best_move

    def minimax(self, board, depth, color, opp, alpha, beta, move_count, history):
        # Terminal conditions:
        # 1. Check if the current player has no pieces on board (opponent wins)
        # 2. Check if the current player has no legal moves (mate)
        # 3. Depth == 0
        # We'll also consider draw by repetition and move limit.

        # First, check if the current player has no pieces
        if self.count_pieces(board, color) == 0:
            return -1000  # opponent wins -> very bad for current player
        if self.count_pieces(board, opp) == 0:
            return 1000   # current player wins -> very good

        # Check for mate (no legal moves)
        legal_moves = []
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        legal_moves.append((spot, neighbor))
        if not legal_moves:
            return -1000  # current player is mated -> very bad

        if depth == 0:
            return self.evaluate_board(board, color, opp, {'B':0, 'W':0}, 
                                       {'B':self.count_pieces(board, 'B'), 'W':self.count_pieces(board, 'W')}, 
                                       is_placement=False)

        # Generate moves for current player
        ordered_moves = self.order_moves(board, legal_moves, color, opp)
        best_score = -float('inf')
        for move in ordered_moves:
            from_spot, to_spot = move
            new_board = board.copy()
            new_board[from_spot] = ''
            new_board[to_spot] = color
            after_board, _ = self.simulate_captures_after_move(new_board, to_spot, color, opp)
            score = -self.minimax(after_board, depth-1, opp, color, -beta, -alpha, move_count+1, history)
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best_score

    # -------------------------------------------------------------------------
    # Helper functions for simulation and evaluation
    # -------------------------------------------------------------------------
    def simulate_captures_after_placement(self, board, placed_spot, color, opp):
        """Simulate capture rule after placement. Returns (new_board, captured_any)."""
        # Step 1: Check the placed piece for suicide
        if self.is_captured(board, placed_spot, color, opp):
            # Suicide: remove the placed piece and return
            new_board = board.copy()
            new_board[placed_spot] = ''
            return new_board, True

        # Step 2: Universal capture sweep with self-harm priority
        new_board = board.copy()
        # First, capture friendly pieces of the mover (color)
        captured_any = False
        for spot in range(24):
            if new_board[spot] == color and self.is_captured(new_board, spot, color, opp):
                new_board[spot] = ''
                captured_any = True
        # Then, capture opponent pieces
        for spot in range(24):
            if new_board[spot] == opp and self.is_captured(new_board, spot, opp, color):
                new_board[spot] = ''
                captured_any = True
        return new_board, captured_any

    def simulate_captures_after_move(self, board, moved_spot, color, opp):
        """Simulate capture rule after a move. Returns (new_board, captured_any)."""
        # Same logic as after placement, but the moved piece is at moved_spot.
        # Step 1: Check the moved piece for suicide
        if self.is_captured(board, moved_spot, color, opp):
            new_board = board.copy()
            new_board[moved_spot] = ''
            return new_board, True

        # Step 2: Universal capture sweep with self-harm priority
        new_board = board.copy()
        captured_any = False
        for spot in range(24):
            if new_board[spot] == color and self.is_captured(new_board, spot, color, opp):
                new_board[spot] = ''
                captured_any = True
        for spot in range(24):
            if new_board[spot] == opp and self.is_captured(new_board, spot, opp, color):
                new_board[spot] = ''
                captured_any = True
        return new_board, captured_any

    def is_captured(self, board, spot, color, opp):
        """Check if piece at spot is captured according to the rule."""
        if board[spot] != color:
            return False
        neighbors = ADJACENCY[spot]
        empty_count = 0
        friendly_count = 0
        opponent_count = 0
        for nb in neighbors:
            if board[nb] == '':
                empty_count += 1
            elif board[nb] == color:
                friendly_count += 1
            else:
                opponent_count += 1
        if empty_count == 0 and opponent_count > friendly_count:
            return True
        return False

    def evaluate_board(self, board, color, opp, pieces_in_hand, pieces_on_board, is_placement):
        """
        Heuristic evaluation of the board from the perspective of `color`.
        Higher is better.
        """
        score = 0

        # Material balance
        my_pieces = self.count_pieces(board, color)
        opp_pieces = self.count_pieces(board, opp)
        score += (my_pieces - opp_pieces) * 100

        # Mobility: number of legal moves
        my_mobility = self.count_mobility(board, color)
        opp_mobility = self.count_mobility(board, opp)
        score += (my_mobility - opp_mobility) * 10

        # Control of key positions
        key_spots = [4, 10, 13, 19]  # crossroads
        for spot in key_spots:
            if board[spot] == color:
                score += 5
            elif board[spot] == opp:
                score -= 5

        # Safety: pieces that are not in danger
        my_safe = 0
        opp_safe = 0
        for spot in range(24):
            if board[spot] == color:
                if not self.is_in_danger(board, spot, color, opp):
                    my_safe += 1
            elif board[spot] == opp:
                if not self.is_in_danger(board, spot, opp, color):
                    opp_safe += 1
        score += (my_safe - opp_safe) * 15

        # Threat: pieces that are in danger (opponent pieces that we can capture next move)
        # We can count opponent pieces that are surrounded by us and have no empty neighbors.
        # But note: they might be saved by their own pieces.
        # We'll count the number of opponent pieces that are captured by the rule.
        for spot in range(24):
            if board[spot] == opp and self.is_captured(board, spot, opp, color):
                score += 30  # bonus for each captured opponent piece (if we can capture next move)
            # Also, if our piece is captured, penalize
            if board[spot] == color and self.is_captured(board, spot, color, opp):
                score -= 30

        # Encourage clustering: pieces that are connected are stronger.
        # We can compute the number of adjacent friendly pieces.
        my_connections = 0
        opp_connections = 0
        for spot in range(24):
            if board[spot] == color:
                for nb in ADJACENCY[spot]:
                    if board[nb] == color:
                        my_connections += 1
            elif board[spot] == opp:
                for nb in ADJACENCY[spot]:
                    if board[nb] == opp:
                        opp_connections += 1
        score += (my_connections - opp_connections) * 2

        # In placement phase, we also consider the number of pieces left to place.
        if is_placement:
            # Having more pieces in hand is good.
            score += pieces_in_hand[color] * 5
            score -= pieces_in_hand[opp] * 5

        return score

    def count_pieces(self, board, color):
        return sum(1 for spot in board if spot == color)

    def count_mobility(self, board, color):
        count = 0
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        count += 1
        return count

    def is_in_danger(self, board, spot, color, opp):
        """Check if a piece is in danger of being captured next turn."""
        # A piece is in danger if it has zero empty neighbors and the number of opponent neighbors is >= friendly neighbors.
        # Actually, for capture we need strictly greater, but if it's equal, then it's safe for now.
        neighbors = ADJACENCY[spot]
        empty_count = 0
        friendly_count = 0
        opponent_count = 0
        for nb in neighbors:
            if board[nb] == '':
                empty_count += 1
            elif board[nb] == color:
                friendly_count += 1
            else:
                opponent_count += 1
        if empty_count == 0 and opponent_count > friendly_count:
            return True
        return False

    def order_moves(self, board, moves, color, opp):
        """Order moves to improve alpha-beta pruning."""
        # We'll assign a heuristic score to each move and sort descending.
        move_scores = []
        for move in moves:
            from_spot, to_spot = move
            score = 0
            # Prefer moves that capture opponent pieces
            new_board = board.copy()
            new_board[from_spot] = ''
            new_board[to_spot] = color
            after_board, _ = self.simulate_captures_after_move(new_board, to_spot, color, opp)
            # Count captured opponent pieces
            opp_before = self.count_pieces(board, opp)
            opp_after = self.count_pieces(after_board, opp)
            score += (opp_before - opp_after) * 100
            # Prefer moves that don't lose our pieces
            my_before = self.count_pieces(board, color)
            my_after = self.count_pieces(after_board, color)
            score -= (my_before - my_after) * 100
            # Prefer moves to center
            if to_spot in [4, 10, 13, 19]:
                score += 10
            move_scores.append((score, move))
        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in move_scores]
