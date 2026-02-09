"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-oss-120b@preset/fp8
Run: 4
Generated: 2026-02-09 12:28:06
"""

from copy import deepcopy

import random
from copy import deepcopy

# ADJACENCY is provided by the game engine at runtime
# Example:
# ADJACENCY = {
#     0: [1, 9], 1: [0, 2, 4], ... 
# }

class SurroundMorrisAgent:
    """
    A heuristic agent for Surround Morris.
    It tries to:
      • avoid suicide moves,
      • maximise material gain after the capture sweep,
      • favour high‑influence positions (crossroads, then T‑junctions),
      • avoid creating a third repetition when it would lose the game.
    """

    # Preference order for empty spots during placement
    _PLACEMENT_PRIORITY = [
        4, 10, 13, 19,            # crossroads (4 neighbours)
        1, 3, 5, 7, 9, 11, 12, 14, 15, 16, 18, 20, 21, 22, 23,  # T‑junctions
        0, 2, 6, 8, 17, 24,  # corners (2 neighbours) – note 24 is out of range, kept for completeness
    ]

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'B' or 'W'

    # --------------------------------------------------------------------- #
    # Helper methods
    # --------------------------------------------------------------------- #
    def _opponent(self, color: str) -> str:
        return 'W' if color == 'B' else 'B'

    def _neighbour_counts(self, board, spot, color):
        """Return (empty, friendly, opponent) neighbour counts for spot."""
        empty = friendly = opponent = 0
        for nb in ADJACENCY[spot]:
            if board[nb] == '':
                empty += 1
            elif board[nb] == color:
                friendly += 1
            else:
                opponent += 1
        return empty, friendly, opponent

    def _is_captured(self, board, spot, color):
        """True if piece at spot would be captured under the rules."""
        empty, friendly, opponent = self._neighbour_counts(board, spot, color)
        return empty == 0 and opponent > friendly

    def _apply_capture_sweep(self, board, active_spot, mover_color):
        """
        Simulate the whole capture process after a placement or movement.
        Returns a new board list after all removals.
        """
        board = board[:]                     # shallow copy is enough (list of strings)

        # ---- Step 1: active piece suicide check ----
        if self._is_captured(board, active_spot, mover_color):
            board[active_spot] = ''
            # active piece died → no universal sweep
            return board

        # ---- Step 2a: remove all friendly pieces that are overwhelmed ----
        # (including possibly the active piece if it later becomes overwhelmed)
        to_remove = []
        for i, cell in enumerate(board):
            if cell == mover_color and self._is_captured(board, i, mover_color):
                to_remove.append(i)
        for i in to_remove:
            board[i] = ''

        # ---- Step 2b: now remove overwhelmed enemy pieces ----
        opp = self._opponent(mover_color)
        to_remove = []
        for i, cell in enumerate(board):
            if cell == opp and self._is_captured(board, i, opp):
                to_remove.append(i)
        for i in to_remove:
            board[i] = ''

        return board

    def _evaluate_board(self, board):
        """Return (my_pieces, opp_pieces) counts for the current board."""
        my = board.count(self.color)
        opp = board.count(self._opponent(self.color))
        return my, opp

    def _avoid_third_repetition(self, new_board, next_player, history):
        """
        Return True if playing this board would create a third occurrence.
        History stores tuples (board_tuple, current_player) *before* each turn.
        """
        tup = tuple(new_board)
        occ = sum(1 for b, p in history if b == tup and p == next_player)
        return occ >= 2   # 2 already stored → this would be the 3rd

    # --------------------------------------------------------------------- #
    # Main decision routine
    # --------------------------------------------------------------------- #
    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        my_color = state["your_color"]
        opp_color = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        history = state["history"]

        # -----------------------------------------------------------------
        # Placement phase
        # -----------------------------------------------------------------
        if phase == "placement":
            empty_spots = [i for i, v in enumerate(board) if v == '']
            best_spot = None
            best_score = -10**9  # very low

            for spot in empty_spots:
                # simulate placement
                sim = board[:]
                sim[spot] = my_color
                after = self._apply_capture_sweep(sim, spot, my_color)
                my_cnt, opp_cnt = self._evaluate_board(after)
                score = my_cnt - opp_cnt   # net material advantage

                # tie‑break with static priority list
                if score > best_score:
                    best_score = score
                    best_spot = spot
                elif score == best_score:
                    # prefer higher priority (lower index in list)
                    cur_pri = self._PLACEMENT_PRIORITY.index(spot) if spot in self._PLACEMENT_PRIORITY else 999
                    best_pri = self._PLACEMENT_PRIORITY.index(best_spot) if best_spot in self._PLACEMENT_PRIORITY else 999
                    if cur_pri < best_pri:
                        best_spot = spot

            # fallback (should never happen)
            if best_spot is None:
                best_spot = random.choice(empty_spots)

            return best_spot

        # -----------------------------------------------------------------
        # Movement phase
        # -----------------------------------------------------------------
        # Gather all legal moves
        legal_moves = []
        for src, cell in enumerate(board):
            if cell != my_color:
                continue
            for dst in ADJACENCY[src]:
                if board[dst] == '':
                    legal_moves.append((src, dst))

        # If for some reason there are no moves (should be a draw), return a dummy move
        if not legal_moves:
            return (0, 1)

        best_move = None
        best_score = -10**9

        for src, dst in legal_moves:
            sim = board[:]
            sim[src] = ''
            sim[dst] = my_color

            # capture sweep with active spot = dst
            after = self._apply_capture_sweep(sim, dst, my_color)
            my_cnt, opp_cnt = self._evaluate_board(after)
            score = my_cnt - opp_cnt   # net gain

            # check repetition penalty
            next_player = opp_color
            if self._avoid_third_repetition(after, next_player, history):
                # If we would lose by repetition, heavily penalise this move
                score -= 1000

            # choose best
            if score > best_score:
                best_score = score
                best_move = (src, dst)

        # If for any reason no move survived (all penalised), pick a random legal move
        if best_move is None:
            best_move = random.choice(legal_moves)

        return best_move
