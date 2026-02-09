"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-5.2-codex
Run: 2
Generated: 2026-02-09 19:15:26
"""

import math

import random
import math

class SurroundMorrisAgent:
    """
    A simple strategic agent for Surround Morris.
    Uses shallow minimax (1-ply opponent response) with a heuristic evaluation.
    """
    WIN_SCORE = 10000

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.invalid_moves = set()
        # Precompute degree (number of neighbors) for each spot
        self.degrees = {i: len(ADJACENCY[i]) for i in range(24)}

    def make_move(self, state: dict, feedback: dict | None = None):
        if feedback is None:
            self.invalid_moves = set()
        else:
            try:
                self.invalid_moves.add(feedback.get("attempted_move"))
            except Exception:
                pass

        return self.choose_move(state, self.invalid_moves)

    # ----------------- Core Move Choice -----------------

    def choose_move(self, state, exclude_moves):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]

        legal = self.get_legal_moves(board, phase, color)
        if exclude_moves:
            legal = [m for m in legal if m not in exclude_moves]

        if not legal:
            legal = self.get_legal_moves(board, phase, color)
            if not legal:
                return 0 if phase == "placement" else (0, 1)

        if len(legal) == 1:
            return legal[0]

        best_val = -math.inf
        best_moves = []

        for move in legal:
            val = self.evaluate_move(board, move, state, color, opp, phase)
            if val > best_val + 1e-6:
                best_val = val
                best_moves = [move]
            elif abs(val - best_val) <= 1e-6:
                best_moves.append(move)

        return random.choice(best_moves) if best_moves else legal[0]

    # ----------------- Minimax Evaluation -----------------

    def evaluate_move(self, board, move, state, color, opp, phase):
        board_after = self.apply_move(board, move, color, phase)
        hand_after = state["pieces_in_hand"].copy()
        if phase == "placement":
            hand_after[color] -= 1

        next_phase = phase
        if phase == "placement" and hand_after["B"] == 0 and hand_after["W"] == 0:
            next_phase = "movement"

        counts = self.count_pieces(board_after)

        # Elimination check
        if counts[color] == 0 and hand_after[color] == 0:
            return -self.WIN_SCORE
        if counts[opp] == 0 and hand_after[opp] == 0:
            return self.WIN_SCORE

        # Repetition check (movement only, and only if already in movement)
        if phase == "movement":
            history = state.get("history", [])
            if self.would_repeat(board_after, opp, history):
                return 0  # Draw

        # Mate check for opponent
        if next_phase == "movement":
            opp_moves = self.get_legal_moves(board_after, next_phase, opp)
            if not opp_moves:
                return self.WIN_SCORE

        return self.min_value(board_after, hand_after, next_phase, opp, color)

    def min_value(self, board, hand, phase, opp, color):
        opp_moves = self.get_legal_moves(board, phase, opp)
        if not opp_moves:
            return self.WIN_SCORE  # opponent mated

        min_val = math.inf

        for move in opp_moves:
            board2 = self.apply_move(board, move, opp, phase)
            hand2 = hand.copy()
            if phase == "placement":
                hand2[opp] -= 1

            next_phase = phase
            if phase == "placement" and hand2["B"] == 0 and hand2["W"] == 0:
                next_phase = "movement"

            counts = self.count_pieces(board2)

            if counts[color] == 0 and hand2[color] == 0:
                val = -self.WIN_SCORE
            elif counts[opp] == 0 and hand2[opp] == 0:
                val = self.WIN_SCORE
            else:
                if next_phase == "movement":
                    our_moves = self.get_legal_moves(board2, next_phase, color)
                    if not our_moves:
                        val = -self.WIN_SCORE
                    else:
                        val = self.evaluate_board(board2, color, hand2)
                else:
                    val = self.evaluate_board(board2, color, hand2)

            if val < min_val:
                min_val = val
                if min_val <= -self.WIN_SCORE:
                    break

        return min_val

    # ----------------- Heuristic Evaluation -----------------

    def evaluate_board(self, board, color, hand):
        opp = self.other(color)

        count_color = 0
        count_opp = 0
        captured_self = 0
        captured_opp = 0
        center = 0

        for i, p in enumerate(board):
            if p == color:
                count_color += 1
                center += self.degrees[i]
                if self.is_captured(i, board):
                    captured_self += 1
            elif p == opp:
                count_opp += 1
                center -= self.degrees[i]
                if self.is_captured(i, board):
                    captured_opp += 1

        total_color = count_color + hand[color]
        total_opp = count_opp + hand[opp]

        material_total = total_color - total_opp
        board_diff = count_color - count_opp
        mobility = len(self.get_legal_moves(board, "movement", color)) - \
                   len(self.get_legal_moves(board, "movement", opp))

        score = (
            material_total * 100 +
            board_diff * 20 +
            (captured_opp - captured_self) * 40 +
            mobility * 5 +
            center * 2
        )

        return score

    # ----------------- Utility Functions -----------------

    def get_legal_moves(self, board, phase, color):
        if phase == "placement":
            return [i for i, p in enumerate(board) if p == ""]
        else:
            moves = []
            for i, p in enumerate(board):
                if p == color:
                    for n in ADJACENCY[i]:
                        if board[n] == "":
                            moves.append((i, n))
            return moves

    def apply_move(self, board, move, color, phase):
        new_board = board.copy()

        if phase == "placement":
            new_board[move] = color
            active = move
        else:
            src, dst = move
            new_board[src] = ""
            new_board[dst] = color
            active = dst

        # Step 1: Active piece suicide check
        if self.is_captured(active, new_board):
            new_board[active] = ""
            return new_board

        # Step 2a: Remove captured friendly pieces
        to_remove = [i for i, p in enumerate(new_board)
                     if p == color and self.is_captured(i, new_board)]
        for i in to_remove:
            new_board[i] = ""

        # Step 2b: Remove captured enemy pieces
        opp = self.other(color)
        to_remove = [i for i, p in enumerate(new_board)
                     if p == opp and self.is_captured(i, new_board)]
        for i in to_remove:
            new_board[i] = ""

        return new_board

    def is_captured(self, spot, board):
        color = board[spot]
        if color == "":
            return False

        empty = 0
        friendly = 0
        opp = 0

        for n in ADJACENCY[spot]:
            if board[n] == "":
                empty += 1
            elif board[n] == color:
                friendly += 1
            else:
                opp += 1

        if empty > 0:
            return False
        return opp > friendly

    def count_pieces(self, board):
        return {"B": board.count("B"), "W": board.count("W")}

    def other(self, color):
        return "B" if color == "W" else "W"

    def would_repeat(self, board, next_player, history):
        if not history:
            return False
        target = (tuple(board), next_player)
        count = 0
        for h in history:
            if h == target:
                count += 1
                if count >= 2:
                    return True
        return False
