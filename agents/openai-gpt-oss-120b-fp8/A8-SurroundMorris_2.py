"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-09 12:28:06
"""

import copy

import random
import copy

# ADJACENCY is provided by the game engine as a global variable.
# Example:
# ADJACENCY = {
#     0: [1, 9], 1: [0, 2, 4], ... 
# }

class SurroundMorrisAgent:
    """
    Simple heuristic agent for Surround Morris.
    Tries to avoid suicide, favours high‑degree positions,
    and selects moves that maximise opponent captures while
    minimising self‑captures (self‑harm priority).
    """

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'B' or 'W'

    # ------------------------------------------------------------------ #
    # Helper utilities
    # ------------------------------------------------------------------ #
    def _opponent(self, color: str) -> str:
        return "W" if color == "B" else "B"

    def _neighbors(self, spot: int):
        return ADJACENCY[spot]

    def _capture_info(self, board: list[str], spot: int) -> tuple[int, int, int]:
        """
        Returns (empty_cnt, friendly_cnt, opponent_cnt) for the piece on `spot`.
        """
        color = board[spot]
        opp = self._opponent(color)
        empty = friendly = opponent = 0
        for nb in self._neighbors(spot):
            if board[nb] == "":
                empty += 1
            elif board[nb] == color:
                friendly += 1
            else:
                opponent += 1
        return empty, friendly, opponent

    def _is_overwhelmed(self, board: list[str], spot: int) -> bool:
        """
        True if the piece at `spot` satisfies the capture rule.
        """
        if board[spot] == "":
            return False
        empty, friendly, opponent = self._capture_info(board, spot)
        return empty == 0 and opponent > friendly

    def _simulate_capture_sweep(
        self, board: list[str], mover_color: str, active_spot: int
    ) -> tuple[list[str], int, int]:
        """
        Perform the full capture sweep after a move/placement.
        Returns (new_board, own_captures, opponent_captures).
        The active piece is assumed to have survived the initial suicide check.
        """
        new_board = board[:]
        opp = self._opponent(mover_color)

        # 2a – remove overwhelmed friendly pieces (including possible other pieces of mover)
        friendly_overwhelmed = [
            i for i in range(24) if new_board[i] == mover_color and self._is_overwhelmed(new_board, i)
        ]
        for i in friendly_overwhelmed:
            new_board[i] = ""

        # 2b – now remove overwhelmed opponent pieces (only once)
        opponent_overwhelmed = [
            i for i in range(24) if new_board[i] == opp and self._is_overwhelmed(new_board, i)
        ]
        for i in opponent_overwhelmed:
            new_board[i] = ""

        own_captures = len(friendly_overwhelmed)
        opponent_captures = len(opponent_overwhelmed)
        return new_board, own_captures, opponent_captures

    def _board_key(self, board: list[str]) -> tuple:
        """Immutable representation used for repetition detection."""
        return tuple(board)

    # ------------------------------------------------------------------ #
    # Core decision making
    # ------------------------------------------------------------------ #
    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        my_color = state["your_color"]
        opp_color = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        history = state["history"]  # list of (board_tuple, player)

        # --------------------------------------------------------------
        # Placement phase
        # --------------------------------------------------------------
        if phase == "placement":
            empty_spots = [i for i, v in enumerate(board) if v == ""]
            # Prefer positions with higher degree (more influence)
            spots_by_degree = sorted(
                empty_spots, key=lambda s: len(ADJACENCY[s]), reverse=True
            )
            for spot in spots_by_degree:
                # Simulate placement
                temp_board = board[:]
                temp_board[spot] = my_color

                # Suicide check for the active piece
                if self._is_overwhelmed(temp_board, spot):
                    continue  # would die immediately – avoid

                # Full capture sweep (friendly pieces may die)
                final_board, own_cap, opp_cap = self._simulate_capture_sweep(
                    temp_board, my_color, spot
                )
                # Keep placements where our own piece survived
                if final_board[spot] == my_color:
                    return spot

            # No safe spot found – pick any empty spot (suicide is legal)
            return random.choice(empty_spots) if empty_spots else 0

        # --------------------------------------------------------------
        # Movement phase
        # --------------------------------------------------------------
        # Gather all legal moves
        legal_moves = []
        for src in range(24):
            if board[src] != my_color:
                continue
            for dst in ADJACENCY[src]:
                if board[dst] == "":
                    legal_moves.append((src, dst))

        if not legal_moves:
            # No moves – engine will treat as draw, but we must return something
            return (0, 0)

        best_move = None
        best_score = -10 ** 9  # very low initial value

        # Pre‑compute repetition counts for quick lookup
        rep_counts = {}
        for b, _ in history:
            rep_counts[b] = rep_counts.get(b, 0) + 1

        for src, dst in legal_moves:
            # Simulate the move
            temp_board = board[:]
            temp_board[src] = ""
            temp_board[dst] = my_color

            # ----- 1. Active piece suicide check -----
            if self._is_overwhelmed(temp_board, dst):
                continue  # move would kill our own active piece – discard

            # ----- 2. Full capture sweep -----
            final_board, own_cap, opp_cap = self._simulate_capture_sweep(
                temp_board, my_color, dst
            )
            net_gain = opp_cap - own_cap  # positive is good

            # ----- 3. Repetition avoidance -----
            board_key = self._board_key(final_board)
            future_rep = rep_counts.get(board_key, 0) + 1  # would be seen again
            # If this would be the 3rd occurrence and we are *behind* in material,
            # heavily penalise the move.
            my_pieces = final_board.count(my_color)
            opp_pieces = final_board.count(opp_color)
            if future_rep >= 3 and my_pieces < opp_pieces:
                net_gain -= 5  # arbitrary penalty

            # ----- 4. Choose the best move -----
            # Prefer moves that do not lose our own pieces.
            if own_cap == 0 and net_gain > best_score:
                best_score = net_gain
                best_move = (src, dst)
            # If all moves lose something, still keep the least damaging.
            elif best_move is None and net_gain > best_score:
                best_score = net_gain
                best_move = (src, dst)

        # Fallback – if every move was discarded (e.g., all cause suicide), pick random legal move
        if best_move is None:
            best_move = random.choice(legal_moves)

        return best_move
