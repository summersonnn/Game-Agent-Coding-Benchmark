"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-09 12:28:06
"""

import copy

import random
import copy

# ADJACENCY is provided by the game engine at runtime
# Example:
# ADJACENCY = {0: [1, 9], 1: [0, 2, 4], ... }

class SurroundMorrisAgent:
    """
    Simple but rule‑aware agent for Surround Morris.
    It tries to avoid suicide/self‑harm, prefers moves that capture
    opponent pieces, and steers clear of 3‑fold repetition when it is
    behind in material.
    """

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'B' or 'W'

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _neighbors(pos: int):
        """Return adjacency list for a spot."""
        return ADJACENCY[pos]

    @staticmethod
    def _capture_status(board, pos, color):
        """
        Returns True if the piece at `pos` (of `color`) would be captured
        according to the Overwhelm rule.
        """
        if board[pos] != color:
            return False

        empty = opp = friendly = 0
        for nb in ADJACENCY[pos]:
            if board[nb] == '':
                empty += 1
            elif board[nb] == color:
                friendly += 1
            else:
                opp += 1

        # capture only when no empty neighbours and opp > friendly
        return empty == 0 and opp > friendly

    @staticmethod
    def _apply_capture(board, active_pos, active_color):
        """
        Perform the capture sweep after a move/placement.
        Returns a new board list after all removals.
        """
        new_board = board[:]

        # 1️⃣ Active piece suicide check
        if SurroundMorrisAgent._capture_status(new_board, active_pos, active_color):
            new_board[active_pos] = ''          # it dies immediately
            return new_board                    # turn ends, no further captures

        # 2️⃣ Universal capture sweep (self‑harm priority)
        opp_color = 'W' if active_color == 'B' else 'B'

        # step 2a – remove own overwhelmed pieces
        to_remove_friendly = [
            i for i, v in enumerate(new_board)
            if v == active_color and SurroundMorrisAgent._capture_status(new_board, i, active_color)
        ]
        for i in to_remove_friendly:
            new_board[i] = ''

        # step 2b – remove opponent overwhelmed pieces (after friendly removal)
        to_remove_enemy = [
            i for i, v in enumerate(new_board)
            if v == opp_color and SurroundMorrisAgent._capture_status(new_board, i, opp_color)
        ]
        for i in to_remove_enemy:
            new_board[i] = ''

        return new_board

    @staticmethod
    def _board_key(board, player):
        """Immutable representation used for repetition detection."""
        return (tuple(board), player)

    # ------------------------------------------------------------------
    # Core decision logic
    # ------------------------------------------------------------------
    def _choose_placement(self, state):
        board = state['board']
        color = state['your_color']
        opp = state['opponent_color']
        history = state['history']

        empty_spots = [i for i, v in enumerate(board) if v == '']
        best_spot = None
        best_score = -10**9

        for spot in empty_spots:
            # simulate placing at `spot`
            trial = board[:]
            trial[spot] = color
            trial = self._apply_capture(trial, spot, color)

            # count pieces after the placement
            my_cnt = trial.count(color)
            opp_cnt = trial.count(opp)

            # avoid suicide (my_cnt may drop to 0)
            score = (my_cnt - opp_cnt) * 10   # material advantage priority

            # small bonus for threatening opponent (adjacent opp count)
            threat = sum(1 for nb in ADJACENCY[spot] if board[nb] == opp)
            score += threat

            # repetition avoidance – if this board would be the 3rd occurrence,
            # treat it as very bad when we are losing material
            key = self._board_key(trial, opp)  # next turn will be opponent
            rep = sum(1 for h in state['history'] if h == key)
            if rep >= 2 and my_cnt < opp_cnt:
                score -= 1000

            if score > best_score:
                best_score = score
                best_spot = spot

        # fallback (should never happen)
        return best_spot if best_spot is not None else random.choice(empty_spots)

    def _choose_movement(self, state):
        board = state['board']
        color = state['your_color']
        opp = state['opponent_color']
        history = state['history']

        legal_moves = []
        for src, piece in enumerate(board):
            if piece != color:
                continue
            for dst in ADJACENCY[src]:
                if board[dst] == '':
                    legal_moves.append((src, dst))

        best_move = None
        best_score = -10**9

        for src, dst in legal_moves:
            trial = board[:]
            trial[src] = ''
            trial[dst] = color
            trial = self._apply_capture(trial, dst, color)

            my_cnt = trial.count(color)
            opp_cnt = trial.count(opp)

            # net material change (enemy captured - own captured)
            material_gain = (my_cnt - state['pieces_on_board'][color]) - (opp_cnt - state['pieces_on_board'][opp])
            # Positive if we captured more enemies than we lost
            score = material_gain * 100

            # safety: penalise moves that cause us to lose any piece
            if my_cnt < state['pieces_on_board'][color]:
                score -= 200

            # positional bonus: occupy high‑degree nodes (4‑neighbour spots)
            degree = len(ADJACENCY[dst])
            if degree == 4:
                score += 5
            elif degree == 3:
                score += 2

            # threat bonus – how many opponent neighbours we now block
            blocked = sum(1 for nb in ADJACENCY[dst] if board[nb] == opp)
            score += blocked

            # repetition avoidance
            key = self._board_key(trial, opp)   # opponent to move next
            rep = sum(1 for h in history if h == key)
            if rep >= 2 and my_cnt < opp_cnt:
                score -= 1000

            if score > best_score:
                best_score = score
                best_move = (src, dst)

        # If for some reason no move survives (should be draw), return a dummy
        if best_move is None:
            # choose any legal move to satisfy engine; if none, return dummy
            return legal_moves[0] if legal_moves else (0, 0)

        return best_move

    # ------------------------------------------------------------------
    # Public interface required by the competition
    # ------------------------------------------------------------------
    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Return a placement (int) during the placement phase or a movement
        (tuple[int, int]) during the movement phase.
        """
        phase = state['phase']

        # Simple retry handling – if we got feedback we just recompute;
        # the logic above already avoids illegal moves.
        if phase == 'placement':
            return self._choose_placement(state)
        else:  # movement phase
            return self._choose_movement(state)
