"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-09 12:28:06
"""

import copy

import random
import copy

# ADJACENCY is provided by the game engine as a global variable.
# It maps each spot (0‑23) to a list of adjacent spot indices.

class SurroundMorrisAgent:
    """
    Simple heuristic agent for Surround Morris.
    - Avoids suicide moves.
    - Prefers moves that capture opponent pieces while preserving own pieces.
    - Tries to keep central (high‑degree) positions.
    - Avoids entering a board state that would be a 3‑fold repetition
      when it would give the win to the opponent.
    """

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'B' or 'W'

    # --------------------------------------------------------------------- #
    #  Helper utilities
    # --------------------------------------------------------------------- #
    def _is_captured(self, spot: int, board: list[str]) -> bool:
        """Return True if the piece on `spot` satisfies the capture rule."""
        piece = board[spot]
        if piece == "":
            return False

        empty = friendly = opponent = 0
        for nb in ADJACENCY[spot]:
            if board[nb] == "":
                empty += 1
            elif board[nb] == piece:
                friendly += 1
            else:
                opponent += 1
        return empty == 0 and opponent > friendly

    def _apply_captures(self, board: list[str], mover: str, active_spot: int):
        """
        Perform the capture sequence after a placement or a move.
        Returns (own_captured, opp_captured) and the final board.
        """
        own_captured = opp_captured = 0
        opp = "W" if mover == "B" else "B"

        # 1️⃣ Active piece suicide check
        if self._is_captured(active_spot, board):
            board[active_spot] = ""
            own_captured += 1
            # active piece died → no further captures
            return own_captured, opp_captured, board

        # 2️⃣ Universal sweep (self‑harm priority)
        # 2a – remove overwhelmed friendly pieces
        to_remove_friendly = [
            i for i, p in enumerate(board)
            if p == mover and self._is_captured(i, board)
        ]
        for i in to_remove_friendly:
            board[i] = ""
            own_captured += 1

        # 2b – remove overwhelmed enemy pieces (after friendly removal)
        to_remove_enemy = [
            i for i, p in enumerate(board)
            if p == opp and self._is_captured(i, board)
        ]
        for i in to_remove_enemy:
            board[i] = ""
            opp_captured += 1

        return own_captured, opp_captured, board

    def _simulate_placement(self, board: list[str], spot: int, color: str):
        """Simulate placing at `spot`; return (net_gain, new_board)."""
        new_board = board.copy()
        new_board[spot] = color
        own_c, opp_c, final = self._apply_captures(new_board, color, spot)
        net = opp_c - own_c          # positive → good for us
        return net, final, own_c, opp_c

    def _simulate_movement(
        self, board: list[str], src: int, dst: int, color: str
    ):
        """Simulate sliding piece src→dst; return (net_gain, new_board)."""
        new_board = board.copy()
        new_board[src] = ""
        new_board[dst] = color
        own_c, opp_c, final = self._apply_captures(new_board, color, dst)
        net = opp_c - own_c
        return net, final, own_c, opp_c

    def _piece_counts(self, board: list[str]) -> tuple[int, int]:
        """Return (black_count, white_count)."""
        b = sum(1 for p in board if p == "B")
        w = sum(1 for p in board if p == "W")
        return b, w

    def _repetition_risk(self, board_tuple, history, my_pieces, opp_pieces):
        """
        Return True if this board state would become a 3‑fold repetition
        and we would lose (i.e., we have ≤ opponent pieces).
        """
        occ = sum(1 for h_board, _ in history if h_board == board_tuple)
        # occ is how many times this position has already appeared.
        # If we would create the third occurrence (occ == 2) and we are not ahead,
        # avoid it.
        return occ == 2 and my_pieces <= opp_pieces

    # --------------------------------------------------------------------- #
    #  Main decision routine
    # --------------------------------------------------------------------- #
    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        my_color = state["your_color"]
        opp_color = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        history = state["history"]

        # Helper to get degree (number of neighbours) – used for tie‑breaking.
        degree = {i: len(ADJACENCY[i]) for i in range(24)}

        # -----------------------------------------------------------------
        # Placement phase
        # -----------------------------------------------------------------
        if phase == "placement":
            empty_spots = [i for i, p in enumerate(board) if p == ""]
            best_spot = None
            best_score = -10**9

            for spot in empty_spots:
                net, new_board, own_c, opp_c = self._simulate_placement(
                    board, spot, my_color
                )
                # Prefer non‑suicidal placements (own_c == 0)
                score = net
                if own_c > 0:
                    score -= 5  # heavy penalty for killing our own piece

                # Prefer central positions when scores tie
                score += 0.1 * degree[spot]

                # Repetition safety
                b_cnt, w_cnt = self._piece_counts(new_board)
                my_cnt = b_cnt if my_color == "B" else w_cnt
                opp_cnt = b_cnt if opp_color == "B" else w_cnt
                board_tuple = tuple(new_board)
                if self._repetition_risk(board_tuple, history, my_cnt, opp_cnt):
                    continue  # skip risky move

                if score > best_score:
                    best_score = score
                    best_spot = spot

            # Fallback – if every spot is risky (unlikely), just pick random.
            if best_spot is None:
                best_spot = random.choice(empty_spots) if empty_spots else 0
            return best_spot

        # -----------------------------------------------------------------
        # Movement phase
        # -----------------------------------------------------------------
        # Gather all legal slides
        legal_moves = []
        for src, piece in enumerate(board):
            if piece != my_color:
                continue
            for dst in ADJACENCY[src]:
                if board[dst] == "":
                    legal_moves.append((src, dst))

        best_move = None
        best_score = -10**9

        for src, dst in legal_moves:
            net, new_board, own_c, opp_c = self._simulate_movement(
                board, src, dst, my_color
            )
            score = net
            if own_c > 0:
                score -= 5  # penalise suicide of our own piece

            # Prefer moves that keep our piece on a high‑degree spot
            score += 0.05 * degree[dst]

            # Repetition safety
            b_cnt, w_cnt = self._piece_counts(new_board)
            my_cnt = b_cnt if my_color == "B" else w_cnt
            opp_cnt = b_cnt if opp_color == "B" else w_cnt
            board_tuple = tuple(new_board)
            if self._repetition_risk(board_tuple, history, my_cnt, opp_cnt):
                continue  # skip this move

            if score > best_score:
                best_score = score
                best_move = (src, dst)

        # If every move was rejected because of repetition risk, fall back.
        if best_move is None:
            best_move = random.choice(legal_moves) if legal_moves else (0, 1)

        return best_move
