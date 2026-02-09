"""
Agent Code: A8-SurroundMorris
Model: qwen/qwen3-coder@preset/fp8
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

        if phase == "placement":
            # Find empty spots
            empty = [i for i in range(24) if board[i] == '']
            if not empty:
                return 0  # Fallback, should never happen

            # Prioritize center spots (4, 10, 13, 19) which have more neighbors
            center_spots = [4, 10, 13, 19]
            good_centers = [spot for spot in center_spots if spot in empty]
            if good_centers:
                return random.choice(good_centers)

            # Otherwise, just pick a random empty spot
            return random.choice(empty)
        else:
            # Movement phase
            # Find all legal moves
            moves = []
            for spot in range(24):
                if board[spot] != color:
                    continue
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))

            if not moves:
                # Should not happen in a normal game but return a fallback
                return (0, 1)

            # Simple heuristic: move towards the opponent or to a high-degree node
            best_move = None
            best_score = -1

            for move in moves:
                from_spot, to_spot = move
                score = 0

                # Prefer moves that place us adjacent to opponents
                for n in ADJACENCY[to_spot]:
                    if board[n] == opp:
                        score += 2
                    elif board[n] == color:
                        score += 1

                # Prefer high-degree nodes (crossroads)
                score += len(ADJACENCY[to_spot]) / 10.0  # Small bonus

                if score > best_score:
                    best_score = score
                    best_move = move

            return best_move if best_move else random.choice(moves)
