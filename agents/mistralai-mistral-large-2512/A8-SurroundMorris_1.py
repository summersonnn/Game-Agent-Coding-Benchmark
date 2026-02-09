"""
Agent Code: A8-SurroundMorris
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-09 19:15:26
"""

from collections import defaultdict

import random
from collections import defaultdict

class SurroundMorrisAgent:
    """
    A strategic agent for Surround Morris that considers capture threats,
    mobility, and positional control.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opponent_color = 'W' if color == 'B' else 'B'

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        pieces_on_board = state["pieces_on_board"]

        if phase == "placement":
            return self._placement_strategy(board, color, opp, pieces_in_hand)
        else:
            return self._movement_strategy(state)

    def _placement_strategy(self, board, color, opp, pieces_in_hand):
        empty_spots = [i for i in range(24) if board[i] == '']
        if not empty_spots:
            return 0  # fallback

        # Evaluate each empty spot
        spot_scores = []
        for spot in empty_spots:
            score = 0

            # Prefer spots with more neighbors (central control)
            neighbors = ADJACENCY[spot]
            score += len(neighbors) * 0.5

            # Avoid spots that would be immediately captured
            temp_board = board.copy()
            temp_board[spot] = color
            if self._is_captured(spot, temp_board):
                score -= 10  # strong penalty for suicide moves

            # Prefer spots that threaten opponent pieces
            threat_score = 0
            for neighbor in neighbors:
                if board[neighbor] == opp:
                    # Check if placing here would threaten this opponent piece
                    temp_board = board.copy()
                    temp_board[spot] = color
                    if self._is_captured(neighbor, temp_board):
                        threat_score += 1
            score += threat_score * 2

            # Prefer spots that connect to our existing pieces
            friendly_neighbors = sum(1 for n in neighbors if board[n] == color)
            score += friendly_neighbors * 0.3

            spot_scores.append((score, spot))

        # Sort by score descending and pick the best spot
        spot_scores.sort(reverse=True, key=lambda x: x[0])
        best_spots = [spot for score, spot in spot_scores if score == spot_scores[0][0]]
        return random.choice(best_spots)

    def _movement_strategy(self, state):
        board = state["board"]
        color = state["your_color"]
        opp = state["opponent_color"]
        move_count = state["move_count"]
        history = state["history"]

        # Get all legal moves
        legal_moves = self._get_legal_moves(board, color)
        if not legal_moves:
            return (0, 1)  # fallback

        # Evaluate each move
        move_scores = []
        for from_spot, to_spot in legal_moves:
            score = 0

            # Simulate the move
            temp_board = board.copy()
            temp_board[from_spot] = ''
            temp_board[to_spot] = color

            # Check if this move captures any opponent pieces
            captured_opponents = self._get_captured_pieces(to_spot, temp_board, opp)
            score += len(captured_opponents) * 5

            # Check if this move puts any of our pieces in danger
            our_pieces_in_danger = self._get_our_pieces_in_danger(temp_board, color)
            score -= len(our_pieces_in_danger) * 3

            # Mobility: prefer moves that give us more future options
            mobility = self._calculate_mobility(temp_board, color)
            score += mobility * 0.2

            # Positional control: prefer central positions
            position_value = len(ADJACENCY[to_spot])
            score += position_value * 0.3

            # Avoid repetition
            if self._would_cause_repetition(temp_board, color, history):
                score -= 5

            move_scores.append((score, from_spot, to_spot))

        # Sort moves by score descending
        move_scores.sort(reverse=True, key=lambda x: x[0])
        best_moves = [(f, t) for s, f, t in move_scores if s == move_scores[0][0]]

        # If we have multiple best moves, prefer those that capture
        capturing_moves = [(f, t) for f, t in best_moves
                          if self._move_captures(f, t, board, color)]
        if capturing_moves:
            return random.choice(capturing_moves)

        return random.choice(best_moves)

    def _get_legal_moves(self, board, color):
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    moves.append((spot, neighbor))
        return moves

    def _is_captured(self, spot, board):
        if board[spot] == '':
            return False

        color = board[spot]
        opp = 'W' if color == 'B' else 'B'
        neighbors = ADJACENCY[spot]

        empty_neighbors = sum(1 for n in neighbors if board[n] == '')
        if empty_neighbors > 0:
            return False

        friendly_neighbors = sum(1 for n in neighbors if board[n] == color)
        opponent_neighbors = sum(1 for n in neighbors if board[n] == opp)

        return opponent_neighbors > friendly_neighbors

    def _get_captured_pieces(self, active_spot, board, color_to_check):
        captured = []

        # First check if the active piece is captured (suicide)
        if self._is_captured(active_spot, board):
            return captured  # active piece dies first, no captures

        # Then check all other pieces of the specified color
        for spot in range(24):
            if board[spot] == color_to_check and self._is_captured(spot, board):
                captured.append(spot)

        return captured

    def _get_our_pieces_in_danger(self, board, color):
        in_danger = []
        for spot in range(24):
            if board[spot] == color and self._is_in_danger(spot, board):
                in_danger.append(spot)
        return in_danger

    def _is_in_danger(self, spot, board):
        if board[spot] == '':
            return False

        color = board[spot]
        neighbors = ADJACENCY[spot]

        empty_neighbors = sum(1 for n in neighbors if board[n] == '')
        if empty_neighbors == 0:
            return False  # already captured or safe

        opp = 'W' if color == 'B' else 'B'
        opponent_neighbors = sum(1 for n in neighbors if board[n] == opp)
        friendly_neighbors = sum(1 for n in neighbors if board[n] == color)

        # If opponents could outnumber us by filling empty spots
        return opponent_neighbors >= friendly_neighbors + empty_neighbors

    def _calculate_mobility(self, board, color):
        mobility = 0
        for spot in range(24):
            if board[spot] == color:
                mobility += sum(1 for n in ADJACENCY[spot] if board[n] == '')
        return mobility

    def _move_captures(self, from_spot, to_spot, board, color):
        temp_board = board.copy()
        temp_board[from_spot] = ''
        temp_board[to_spot] = color
        opp = 'W' if color == 'B' else 'B'
        captured = self._get_captured_pieces(to_spot, temp_board, opp)
        return len(captured) > 0

    def _would_cause_repetition(self, new_board, color, history):
        new_state = (tuple(new_board), color)
        return history.count(new_state) >= 2
