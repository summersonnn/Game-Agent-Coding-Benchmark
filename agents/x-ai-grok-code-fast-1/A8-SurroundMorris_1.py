"""
Agent Code: A8-SurroundMorris
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-09 21:38:14
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
        # Priority for spots during placement (higher is better)
        self.spot_priority = {
            4: 10, 10: 10, 13: 10, 19: 10,  # Crossroads
            7: 7, 16: 7,  # Central T-junctions
            1: 5, 3: 5, 5: 5, 9: 5, 12: 5, 14: 5, 18: 5, 20: 5, 21: 5, 22: 5, 23: 5,  # Other T-junctions and edges
            0: 3, 2: 3, 6: 3, 8: 3, 11: 3, 15: 3, 17: 3  # Corners and lesser spots
        }

    def is_captured(self, spot, board, piece_color):
        if board[spot] == '':
            return False
        opp_color = 'W' if piece_color == 'B' else 'B'
        empty_count = 0
        friendly_count = 0
        opp_count = 0
        for adj in ADJACENCY[spot]:
            if board[adj] == '':
                empty_count += 1
            elif board[adj] == piece_color:
                friendly_count += 1
            else:
                opp_count += 1
        if empty_count == 0 and opp_count > friendly_count:
            return True
        return False

    def simulate_after_move(self, board, from_spot, to_spot, color):
        temp_board = board.copy()
        temp_board[from_spot] = ''
        temp_board[to_spot] = color
        opp = 'W' if color == 'B' else 'B'
        # Check suicide
        if self.is_captured(to_spot, temp_board, color):
            temp_board[to_spot] = ''
            return temp_board
        # Universal sweep: self-harm priority
        friendly_captured = []
        for spot in range(24):
            if temp_board[spot] == color and self.is_captured(spot, temp_board, color):
                friendly_captured.append(spot)
        for spot in friendly_captured:
            temp_board[spot] = ''
        enemy_captured = []
        for spot in range(24):
            if temp_board[spot] == opp and self.is_captured(spot, temp_board, opp):
                enemy_captured.append(spot)
        for spot in enemy_captured:
            temp_board[spot] = ''
        return temp_board

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Called each turn. Return your move based on the current game state.

        Parameters:
        -----------
        state : dict
            {
                "board": list[str],
                    # 24-element list. Each element is '', 'B', or 'W'.
                    # Index corresponds to spot number on the board.
                "phase": str,
                    # 'placement' or 'movement'
                "your_color": str,
                    # Your color: 'B' or 'W'
                "opponent_color": str,
                    # Opponent's color
                "pieces_in_hand": dict,
                    # {'B': int, 'W': int} - pieces not yet placed
                "pieces_on_board": dict,
                    # {'B': int, 'W': int} - pieces currently on the board
                "move_count": int,
                    # Number of movement turns elapsed (0 during placement)
                "history": list[tuple],
                    # List of (board_tuple, current_player) states seen so far.
                    # Use this to detect and avoid 3-fold repetition.
                    # Reset when transitioning from placement to movement phase.
            }

        feedback : dict or None
            None on first attempt. On retries after an invalid move:
            {
                "error_code": str,
                "error_message": str,
                "attempted_move": ...,
                "attempt_number": int,
            }

        Returns:
        --------
        During placement phase:
            int - the spot number (0-23) to place your piece

        During movement phase:
            tuple[int, int] - (from_spot, to_spot) to slide your piece
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        history = state["history"]

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            candidates = []
            for s in empty_spots:
                temp_board = board.copy()
                temp_board[s] = color
                if not self.is_captured(s, temp_board, color):
                    candidates.append(s)
            if not candidates:
                # Have to suicide, pick random
                return random.choice(empty_spots)
            else:
                # Pick with highest priority
                best = max(candidates, key=lambda s: self.spot_priority.get(s, 0))
                return best
        else:
            # Movement phase
            legal_moves = []
            for spot in range(24):
                if board[spot] == color:
                    for adj in ADJACENCY[spot]:
                        if board[adj] == '':
                            legal_moves.append((spot, adj))
            if not legal_moves:
                # Mated, shouldn't happen but return something
                return (0, 1)
            # Evaluate each move
            scores = []
            for from_s, to_s in legal_moves:
                new_board = self.simulate_after_move(board, from_s, to_s, color)
                position = (tuple(new_board), opp)
                if history.count(position) >= 2:
                    score = -100  # Avoid 3-fold repetition
                else:
                    my_count = sum(1 for p in new_board if p == color)
                    opp_count = sum(1 for p in new_board if p == opp)
                    score = my_count - opp_count
                scores.append((score, (from_s, to_s)))
            # Choose the move with the highest score
            best_score, best_move = max(scores)
            return best_move
