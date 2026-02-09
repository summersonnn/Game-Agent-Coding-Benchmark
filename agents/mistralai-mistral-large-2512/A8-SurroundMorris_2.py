"""
Agent Code: A8-SurroundMorris
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-09 19:15:26
"""

from collections import defaultdict

import random
from collections import defaultdict

class SurroundMorrisAgent:
    """
    A strategic agent for Surround Morris that prioritizes board control and safety.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opponent_color = 'W' if color == 'B' else 'B'
        # Precompute neighbor counts for each position
        self.neighbor_counts = {spot: len(neighbors) for spot, neighbors in ADJACENCY.items()}
        # Positions sorted by strategic value (crossroads > T-junctions > corners)
        self.strategic_order = [
            4, 10, 13, 19,  # Crossroads
            1, 7, 16, 22,   # T-junctions
            0, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 23  # Others
        ]

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        pieces_on_board = state["pieces_on_board"]

        if phase == "placement":
            return self._make_placement_move(state)
        else:
            return self._make_movement_move(state)

    def _make_placement_move(self, state):
        board = state["board"]
        color = state["your_color"]
        opp = state["opponent_color"]

        # Get all empty spots
        empty_spots = [i for i in range(24) if board[i] == '']

        # Prioritize spots that:
        # 1. Are not suicide moves
        # 2. Have high strategic value
        # 3. Block opponent clusters
        # 4. Create potential captures

        # First, filter out suicide moves
        safe_spots = []
        for spot in empty_spots:
            # Simulate placing our piece
            temp_board = board.copy()
            temp_board[spot] = color

            # Check if this would be a suicide move
            if not self._is_captured(spot, temp_board):
                safe_spots.append(spot)

        # If we have safe spots, use them
        if safe_spots:
            # Score spots based on strategic value and potential to capture
            scored_spots = []
            for spot in safe_spots:
                score = self._score_placement(spot, state)
                scored_spots.append((score, spot))

            # Sort by score descending
            scored_spots.sort(reverse=True, key=lambda x: x[0])
            best_spots = [spot for score, spot in scored_spots if score == scored_spots[0][0]]
            return random.choice(best_spots)
        else:
            # If all moves are suicide, pick the least bad one
            # (though this should rarely happen)
            return random.choice(empty_spots)

    def _score_placement(self, spot, state):
        board = state["board"]
        color = state["your_color"]
        opp = state["opponent_color"]
        score = 0

        # Strategic value (crossroads > T-junctions > corners)
        strategic_value = self.strategic_order.index(spot) if spot in self.strategic_order else len(self.strategic_order)
        score += (len(self.strategic_order) - strategic_value) * 10

        # Potential to capture opponent pieces
        temp_board = board.copy()
        temp_board[spot] = color

        # Check if this creates any captures
        for neighbor in ADJACENCY[spot]:
            if temp_board[neighbor] == opp and self._is_captured(neighbor, temp_board):
                score += 20

        # Potential to block opponent clusters
        opponent_neighbors = sum(1 for n in ADJACENCY[spot] if board[n] == opp)
        score += opponent_neighbors * 5

        # Potential to create our own clusters (but not too close)
        friendly_neighbors = sum(1 for n in ADJACENCY[spot] if board[n] == color)
        score += friendly_neighbors * 2

        # Avoid creating our own capture opportunities
        if friendly_neighbors >= 2:
            # Check if we're creating a potential capture for ourselves
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == color:
                    # Count opponent neighbors of this friendly piece
                    opp_count = sum(1 for n in ADJACENCY[neighbor] if board[n] == opp)
                    if opp_count >= self.neighbor_counts[neighbor] - 1:
                        score -= 15

        return score

    def _make_movement_move(self, state):
        board = state["board"]
        color = state["your_color"]
        opp = state["opponent_color"]
        history = state["history"]

        # Get all legal moves
        legal_moves = self._get_legal_moves(state)

        if not legal_moves:
            # No legal moves - we're mated
            return (0, 1)  # Shouldn't happen as game would end

        # Score all legal moves
        scored_moves = []
        for move in legal_moves:
            from_spot, to_spot = move
            score = self._score_move(move, state)
            scored_moves.append((score, move))

        # Sort by score descending
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        best_score = scored_moves[0][0]
        best_moves = [move for score, move in scored_moves if score == best_score]

        # Check for repetition - avoid moves that lead to immediate repetition
        if len(history) >= 2:
            last_state = (tuple(board), color)
            if last_state in history[:-1]:
                # We're about to repeat - try to find a different move
                non_repeating_moves = [move for move in best_moves if self._would_repeat(move, state)]
                if non_repeating_moves:
                    best_moves = non_repeating_moves

        return random.choice(best_moves)

    def _get_legal_moves(self, state):
        board = state["board"]
        color = state["your_color"]
        moves = []

        for spot in range(24):
            if board[spot] != color:
                continue
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    moves.append((spot, neighbor))

        return moves

    def _score_move(self, move, state):
        from_spot, to_spot = move
        board = state["board"]
        color = state["your_color"]
        opp = state["opponent_color"]
        score = 0

        # Simulate the move
        temp_board = board.copy()
        temp_board[from_spot] = ''
        temp_board[to_spot] = color

        # Check if this move captures any opponent pieces
        captures = 0
        for spot in range(24):
            if temp_board[spot] == opp and self._is_captured(spot, temp_board):
                captures += 1

        score += captures * 30

        # Check if this move puts us in danger
        if self._is_captured(to_spot, temp_board):
            score -= 50  # Avoid suicide moves

        # Strategic value of destination
        strategic_value = self.strategic_order.index(to_spot) if to_spot in self.strategic_order else len(self.strategic_order)
        score += (len(self.strategic_order) - strategic_value) * 5

        # Potential to create future captures
        for neighbor in ADJACENCY[to_spot]:
            if temp_board[neighbor] == opp:
                # Check if we can capture this piece in the future
                opp_neighbors = sum(1 for n in ADJACENCY[neighbor] if temp_board[n] == opp)
                empty_neighbors = sum(1 for n in ADJACENCY[neighbor] if temp_board[n] == '')
                if empty_neighbors == 1 and opp_neighbors >= self.neighbor_counts[neighbor] - 1:
                    score += 15

        # Mobility - prefer moves that give us more options
        mobility = 0
        for neighbor in ADJACENCY[to_spot]:
            if temp_board[neighbor] == '':
                mobility += 1
        score += mobility * 3

        # Avoid moves that block our own pieces
        for neighbor in ADJACENCY[to_spot]:
            if temp_board[neighbor] == color:
                # Check if this move blocks the last empty neighbor of a friendly piece
                empty_neighbors = sum(1 for n in ADJACENCY[neighbor] if temp_board[n] == '')
                if empty_neighbors == 1:
                    # Check if the only empty neighbor was our from_spot
                    if from_spot in ADJACENCY[neighbor]:
                        score -= 20

        return score

    def _would_repeat(self, move, state):
        from_spot, to_spot = move
        board = state["board"]
        color = state["your_color"]
        history = state["history"]

        # Simulate the move
        temp_board = board.copy()
        temp_board[from_spot] = ''
        temp_board[to_spot] = color

        # Check if this state has occurred before
        new_state = (tuple(temp_board), color)
        return new_state in history

    def _is_captured(self, spot, board):
        """Check if a piece at spot would be captured on the given board."""
        if board[spot] == '':
            return False

        color = board[spot]
        opp = 'W' if color == 'B' else 'B'

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

        # Capture condition: no empty neighbors and more opponents than friends
        return empty_neighbors == 0 and opponent_neighbors > friendly_neighbors
