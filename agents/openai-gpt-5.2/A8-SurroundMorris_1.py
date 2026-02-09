"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-09 19:10:28
"""

import math

import random
import math

class SurroundMorrisAgent:
    """
    A tactical agent for Surround Morris with:
      - correct capture simulation (suicide-first, then self-harm priority sweep)
      - shallow minimax (1-ply response) with heuristics
      - basic repetition-avoidance (in movement phase)
    """

    CROSSROADS = {4, 10, 13, 19}
    CORNERS = {0, 2, 21, 23}

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    # -----------------------------
    # Core helpers
    # -----------------------------
    @staticmethod
    def _opp(color: str) -> str:
        return "W" if color == "B" else "B"

    @staticmethod
    def _count_on_board(board) -> dict:
        return {
            "B": sum(1 for x in board if x == "B"),
            "W": sum(1 for x in board if x == "W"),
        }

    @staticmethod
    def _legal_placements(board):
        return [i for i in range(24) if board[i] == ""]

    @staticmethod
    def _legal_movements(board, color: str):
        moves = []
        for frm in range(24):
            if board[frm] != color:
                continue
            for to in ADJACENCY[frm]:
                if board[to] == "":
                    moves.append((frm, to))
        return moves

    @staticmethod
    def _neighbor_counts(board, spot: int):
        piece = board[spot]
        if piece == "":
            return 0, 0, 0
        empty = friendly = opp = 0
        for n in ADJACENCY[spot]:
            if board[n] == "":
                empty += 1
            elif board[n] == piece:
                friendly += 1
            else:
                opp += 1
        return empty, friendly, opp

    @classmethod
    def _is_captured(cls, board, spot: int) -> bool:
        piece = board[spot]
        if piece == "":
            return False
        empty, friendly, opp = cls._neighbor_counts(board, spot)
        return (empty == 0) and (opp > friendly)

    @classmethod
    def _resolve_captures_after_move(cls, board, active_spot: int):
        """
        Implements:
          1) active-piece suicide check; if dies -> stop, no other captures
          2) sweep: remove overwhelmed friendlies first (simultaneous), then re-check enemies
        """
        active_piece = board[active_spot]
        if active_piece == "":
            return board  # should not happen, but safe

        # Step 1: suicide-first
        if cls._is_captured(board, active_spot):
            board[active_spot] = ""
            return board

        mover = active_piece
        enemy = "W" if mover == "B" else "B"

        # Step 2a: remove overwhelmed friendlies (simultaneous)
        friendly_dead = [i for i in range(24) if board[i] == mover and cls._is_captured(board, i)]
        for i in friendly_dead:
            board[i] = ""

        # Step 2b: re-check enemies after friendlies removed
        enemy_dead = [i for i in range(24) if board[i] == enemy and cls._is_captured(board, i)]
        for i in enemy_dead:
            board[i] = ""

        return board

    @classmethod
    def _apply_placement(cls, board, spot: int, color: str, pieces_in_hand: dict):
        new_board = list(board)
        new_hand = dict(pieces_in_hand)

        new_board[spot] = color
        new_hand[color] = max(0, new_hand.get(color, 0) - 1)

        cls._resolve_captures_after_move(new_board, spot)

        next_phase = "movement" if (new_hand.get("B", 0) == 0 and new_hand.get("W", 0) == 0) else "placement"
        return new_board, new_hand, next_phase

    @classmethod
    def _apply_movement(cls, board, move, color: str, pieces_in_hand: dict):
        frm, to = move
        new_board = list(board)
        new_hand = dict(pieces_in_hand)

        new_board[frm] = ""
        new_board[to] = color
        cls._resolve_captures_after_move(new_board, to)

        return new_board, new_hand, "movement"

    # -----------------------------
    # Terminal checks & scoring hooks
    # -----------------------------
    @classmethod
    def _elimination_status(cls, board, phase: str, pieces_in_hand: dict):
        """
        Returns:
          "B" if Black is eliminated now,
          "W" if White is eliminated now,
          None otherwise.
        Placement elimination needs (on_board == 0 and in_hand == 0).
        Movement elimination needs (on_board == 0).
        """
        counts = cls._count_on_board(board)
        if phase == "placement":
            for c in ("B", "W"):
                if counts[c] == 0 and pieces_in_hand.get(c, 0) == 0:
                    return c
        else:
            for c in ("B", "W"):
                if counts[c] == 0:
                    return c
        return None

    @classmethod
    def _immediate_draw_by_repetition(cls, state_history, next_board, next_player: str) -> bool:
        """
        If the next state's (board_tuple, next_player) has already appeared twice in history,
        then when it's recorded at the start of next turn, it becomes the 3rd -> immediate draw.
        """
        key = (tuple(next_board), next_player)
        seen = 0
        for h in state_history:
            if h == key:
                seen += 1
                if seen >= 2:
                    return True
        return False

    # -----------------------------
    # Heuristic evaluation
    # -----------------------------
    @classmethod
    def _evaluate(cls, board, my_color: str, phase: str) -> float:
        opp = cls._opp(my_color)
        counts = cls._count_on_board(board)
        my_n = counts[my_color]
        op_n = counts[opp]

        # Material advantage (dominant, but not everything)
        score = (my_n - op_n) * 120.0

        # Vulnerability: currently capturable pieces (if a sweep happens)
        my_vul = 0
        op_vul = 0
        my_low_air = 0
        op_low_air = 0

        for i in range(24):
            if board[i] == "":
                continue
            empty, _, _ = cls._neighbor_counts(board, i)
            if board[i] == my_color:
                if empty <= 1:
                    my_low_air += (2 - empty)  # 1 if empty==1, 2 if empty==0
                if cls._is_captured(board, i):
                    my_vul += 1
            else:
                if empty <= 1:
                    op_low_air += (2 - empty)
                if cls._is_captured(board, i):
                    op_vul += 1

        score += op_vul * 55.0
        score -= my_vul * 75.0
        score += op_low_air * 6.0
        score -= my_low_air * 8.0

        # Board influence
        for i in cls.CROSSROADS:
            if board[i] == my_color:
                score += 8.0
            elif board[i] == opp:
                score -= 8.0
        for i in cls.CORNERS:
            if board[i] == my_color:
                score += 3.0
            elif board[i] == opp:
                score -= 3.0

        # Mobility (movement phase)
        if phase == "movement":
            my_moves = len(cls._legal_movements(board, my_color))
            op_moves = len(cls._legal_movements(board, opp))
            score += (my_moves - op_moves) * 3.0

        return score

    # -----------------------------
    # Move choice (minimax depth 1)
    # -----------------------------
    def _score_after_my_move(self, state, my_move):
        board = state["board"]
        phase = state["phase"]
        my = state["your_color"]
        opp = state["opponent_color"]
        hand = state["pieces_in_hand"]
        history = state.get("history", [])

        if phase == "placement":
            new_board, new_hand, next_phase = self._apply_placement(board, my_move, my, hand)
        else:
            new_board, new_hand, next_phase = self._apply_movement(board, my_move, my, hand)

        # Elimination is checked mover-first; if I eliminated myself, it's catastrophic.
        eliminated = self._elimination_status(new_board, next_phase if phase == "placement" else "movement", new_hand)
        if eliminated == my:
            return -1e9

        if eliminated == opp:
            # Winning by elimination: prefer more remaining pieces.
            my_left = self._count_on_board(new_board)[my]
            return 1e8 + my_left * 1000.0

        # Repetition draw only in movement
        if next_phase == "movement":
            if self._immediate_draw_by_repetition(history, new_board, opp):
                counts = self._count_on_board(new_board)
                my_n = counts[my]
                op_n = counts[opp]
                # Avoid draw when ahead; accept when behind.
                base = ((my_n + op_n) / 2.0) * 100.0
                if my_n > op_n:
                    return base - 300.0
                elif my_n < op_n:
                    return base + 300.0
                else:
                    return base

        # Mate check: if opponent to move has no legal moves in movement phase, I win mate (+7/-7).
        if next_phase == "movement":
            opp_moves = self._legal_movements(new_board, opp)
            if len(opp_moves) == 0:
                return 9e7

        # Opponent best response (minimize my evaluation)
        if next_phase == "placement":
            opp_moves = self._legal_placements(new_board)
            if not opp_moves:
                return self._evaluate(new_board, my, next_phase)
            worst_for_me = math.inf
            for om in opp_moves:
                b2, h2, ph2 = self._apply_placement(new_board, om, opp, new_hand)

                eliminated2 = self._elimination_status(b2, ph2, h2)
                if eliminated2 == my:
                    val = -1e9
                elif eliminated2 == opp:
                    my_left = self._count_on_board(b2)[my]
                    val = 1e8 + my_left * 1000.0
                else:
                    val = self._evaluate(b2, my, ph2)

                if val < worst_for_me:
                    worst_for_me = val
            return worst_for_me
        else:
            opp_moves = self._legal_movements(new_board, opp)
            if not opp_moves:
                # mate already handled above, but keep safe
                return 9e7
            worst_for_me = math.inf
            for om in opp_moves:
                b2, h2, ph2 = self._apply_movement(new_board, om, opp, new_hand)

                eliminated2 = self._elimination_status(b2, "movement", h2)
                if eliminated2 == my:
                    val = -1e9
                elif eliminated2 == opp:
                    my_left = self._count_on_board(b2)[my]
                    val = 1e8 + my_left * 1000.0
                else:
                    # If opponent's move creates immediate repetition draw for me, that draw would be checked
                    # at start of my next turn. Opponent might like that if they're ahead.
                    if self._immediate_draw_by_repetition(history, b2, my):
                        counts = self._count_on_board(b2)
                        my_n = counts[my]
                        op_n = counts[opp]
                        base = ((my_n + op_n) / 2.0) * 100.0
                        if my_n < op_n:
                            val = base - 200.0  # opponent is ahead -> they like drawing; bad for me
                        elif my_n > op_n:
                            val = base + 200.0
                        else:
                            val = base
                    else:
                        val = self._evaluate(b2, my, "movement")

                if val < worst_for_me:
                    worst_for_me = val
            return worst_for_me

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        my = state["your_color"]

        # Build candidate legal moves
        if phase == "placement":
            legal = self._legal_placements(board)
            if not legal:
                return 0
        else:
            legal = self._legal_movements(board, my)
            if not legal:
                return (0, 1)

        # If engine says our last attempt was invalid, don't repeat it
        if feedback is not None and "attempted_move" in feedback:
            bad = feedback["attempted_move"]
            legal = [m for m in legal if m != bad]
            if not legal:
                # fall back (shouldn't happen)
                if phase == "placement":
                    legal = self._legal_placements(board) or [0]
                else:
                    legal = self._legal_movements(board, my) or [(0, 1)]

        # Evaluate all moves (shallow minimax) and choose best with small random tie-break
        scored = []
        best_val = -math.inf
        for m in legal:
            val = self._score_after_my_move(state, m)
            if val > best_val:
                best_val = val
            scored.append((val, m))

        # Keep a small set of top moves to avoid deterministic loops
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [m for (v, m) in scored if v >= best_val - 1e-6]
        if len(top) > 3:
            top = top[:3]
        return random.choice(top)
