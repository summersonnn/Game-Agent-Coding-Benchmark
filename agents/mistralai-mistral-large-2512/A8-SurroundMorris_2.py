"""
Agent Code: A8-SurroundMorris
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-10 22:38:58
"""



import random

class SurroundMorrisAgent:
    """
    A strategic agent for Surround Morris that prioritizes control and safety.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opponent_color = 'W' if color == 'B' else 'B'
        # Precompute neighbor counts for each position
        self.neighbor_counts = {spot: len(neighbors) for spot, neighbors in ADJACENCY.items()}
        # Prioritize central positions during placement
        self.position_values = {
            0: 1, 1: 2, 2: 1,
            3: 1, 4: 4, 5: 1,
            6: 1, 7: 3, 8: 1,
            9: 1, 10: 4, 11: 1,
            12: 1, 13: 4, 14: 1,
            15: 1, 16: 3, 17: 1,
            18: 1, 19: 4, 20: 1,
            21: 1, 22: 2, 23: 1
        }

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]

        if phase == "placement":
            return self._placement_move(board, color, opp)
        else:
            return self._movement_move(board, color, opp, state["history"])

    def _placement_move(self, board, color, opp):
        empty_spots = [i for i in range(24) if board[i] == '']
        if not empty_spots:
            return 0

        # Evaluate each empty spot
        spot_scores = []
        for spot in empty_spots:
            # Check if this placement would be suicidal
            if self._would_be_suicidal(board, spot, color):
                score = -100  # Avoid suicide
            else:
                # Score based on position value and potential to capture
                score = self.position_values[spot]
                # Bonus for adjacent friendly pieces
                friendly_neighbors = sum(1 for n in ADJACENCY[spot] if board[n] == color)
                score += friendly_neighbors * 2
                # Penalty for adjacent opponent pieces
                opp_neighbors = sum(1 for n in ADJACENCY[spot] if board[n] == opp)
                score -= opp_neighbors * 1
            spot_scores.append(score)

        # Choose the best spot, with some randomness to avoid predictability
        max_score = max(spot_scores)
        best_spots = [spot for spot, score in zip(empty_spots, spot_scores) if score == max_score]
        return random.choice(best_spots)

    def _movement_move(self, board, color, opp, history):
        # Get all legal moves
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    moves.append((spot, neighbor))

        if not moves:
            return (0, 1)  # Shouldn't happen as game would have ended

        # Evaluate each move
        move_scores = []
        for from_spot, to_spot in moves:
            # Check if this move would be suicidal
            if self._would_be_suicidal_after_move(board, from_spot, to_spot, color):
                score = -100  # Avoid suicide
            else:
                # Score based on position value and safety
                new_board = board.copy()
                new_board[from_spot] = ''
                new_board[to_spot] = color

                # Position value
                score = self.position_values[to_spot]

                # Safety - count empty neighbors
                empty_neighbors = sum(1 for n in ADJACENCY[to_spot] if new_board[n] == '')
                score += empty_neighbors * 2

                # Potential to capture opponents
                opp_captures = 0
                for n in ADJACENCY[to_spot]:
                    if new_board[n] == opp and self._is_captured(n, new_board):
                        opp_captures += 1
                score += opp_captures * 5

                # Avoid repetition
                new_board_tuple = tuple(new_board)
                if (new_board_tuple, color) in history:
                    score -= 10

            move_scores.append(score)

        # Choose the best move, with some randomness
        max_score = max(move_scores)
        best_moves = [move for move, score in zip(moves, move_scores) if score == max_score]
        return random.choice(best_moves)

    def _would_be_suicidal(self, board, spot, color):
        """Check if placing a piece at spot would be suicidal"""
        # Count neighbors
        empty = 0
        friendly = 0
        opponent = 0
        for n in ADJACENCY[spot]:
            if board[n] == '':
                empty += 1
            elif board[n] == color:
                friendly += 1
            else:
                opponent += 1

        # Suicidal if completely blocked and opponents > friendlies
        return empty == 0 and opponent > friendly

    def _would_be_suicidal_after_move(self, board, from_spot, to_spot, color):
        """Check if moving to to_spot would be suicidal"""
        new_board = board.copy()
        new_board[from_spot] = ''
        new_board[to_spot] = color

        # Check if the moved piece would be suicidal
        empty = 0
        friendly = 0
        opponent = 0
        for n in ADJACENCY[to_spot]:
            if new_board[n] == '':
                empty += 1
            elif new_board[n] == color:
                friendly += 1
            else:
                opponent += 1

        return empty == 0 and opponent > friendly

    def _is_captured(self, spot, board):
        """Check if a piece at spot is captured"""
        if board[spot] == '':
            return False

        color = board[spot]
        empty = 0
        friendly = 0
        opponent = 0
        for n in ADJACENCY[spot]:
            if board[n] == '':
                empty += 1
            elif board[n] == color:
                friendly += 1
            else:
                opponent += 1

        return empty == 0 and opponent > friendly
