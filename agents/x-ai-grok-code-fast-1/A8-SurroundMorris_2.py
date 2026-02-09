"""
Agent Code: A8-SurroundMorris
Model: x-ai/grok-code-fast-1
Run: 2
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

    def _is_captured(self, board, spot):
        """Helper to check if a piece at spot is captured."""
        piece = board[spot]
        if piece == '':
            return False
        adj = ADJACENCY[spot]
        empty_n = len([n for n in adj if board[n] == ''])
        friendly_n = len([n for n in adj if board[n] == piece])
        opp_n = len([n for n in adj if board[n] != '' and board[n] != piece])
        return empty_n == 0 and opp_n > friendly_n

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
            legal = [i for i in range(24) if board[i] == '']
            candidates = []
            for spot in legal:
                new_board = list(board)
                new_board[spot] = color
                if not self._is_captured(new_board, spot):
                    candidates.append(spot)
            if not candidates:
                # If no safe spots, pick random (forced suicide)
                return random.choice(legal)
            # Evaluate candidates: prefer higher degree among safe spots
            best_deg = -1
            best_spots = []
            for spot in candidates:
                deg = len(ADJACENCY[spot])
                if deg > best_deg:
                    best_deg = deg
                    best_spots = [spot]
                elif deg == best_deg:
                    best_spots.append(spot)
            return random.choice(best_spots)
        else:  # movement phase
            legal_moves = []
            for spot in range(24):
                if board[spot] != color:
                    continue
                for neigh in ADJACENCY[spot]:
                    if board[neigh] == '':
                        legal_moves.append((spot, neigh))
            if not legal_moves:
                return (0, 1)  # No legal moves, return invalid but required
            # Simulate each move and pick the one with best resulting eval (own - opp pieces)
            best_eval = -100
            best_moves = []
            for move in legal_moves:
                fr, to = move
                new_board = list(board)
                new_board[fr] = ''
                new_board[to] = color
                # Apply captures
                if self._is_captured(new_board, to):
                    new_board[to] = ''
                else:
                    # Remove own overwhelmed pieces
                    to_remove = [s for s in range(24) if new_board[s] == color and self._is_captured(new_board, s)]
                    for s in to_remove:
                        new_board[s] = ''
                    # Then remove enemy overwhelmed pieces
                    to_remove = [s for s in range(24) if new_board[s] == opp and self._is_captured(new_board, s)]
                    for s in to_remove:
                        new_board[s] = ''
                # Eval: own pieces - opp pieces
                own = sum(1 for p in new_board if p == color)
                op = sum(1 for p in new_board if p == opp)
                ev = own - op
                if ev > best_eval:
                    best_eval = ev
                    best_moves = [move]
                elif ev == best_eval:
                    best_moves.append(move)
            return random.choice(best_moves)
