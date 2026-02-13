"""
Agent Code: A8-SurroundMorris
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:10:12
"""



import random

class SurroundMorrisAgent:
    """
    Simple heuristic agent for Surround Morris.
    It evaluates placement/movement moves by simulating the capture
    rules, checking for immediate wins/mates, avoiding three‑fold
    repetition and favouring material, mobility and central control.
    """

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    # ----------------------------------------------------------------------
    # Public interface
    # ----------------------------------------------------------------------
    def make_move(self, state: dict, feedback=None):
        """
        Choose the best legal move for the current game state.

        Parameters
        ----------
        state : dict
            Full description of the current position (see the problem statement).

        Returns
        -------
        int | tuple[int, int]
            Placement spot (0‑23) or movement pair (from, to).
        """
        board = list(state["board"])
        phase = state["phase"]
        opp_color = state["opponent_color"]
        history = state.get("history", [])

        # Legal moves for the current phase
        if phase == "placement":
            legal = self.legal_placements(board)
        else:
            legal = self.legal_movements(board, self.color)

        # Should never be empty, but guard against bugs in the engine
        if not legal:
            return 0 if phase == "placement" else (0, 1)

        best_score = -10**9
        best_move = legal[0]

        for move in legal:
            # ----- simulate the move and the capture phase -----
            new_board = self.simulate_move(board, move, self.color, phase)

            # ----- immediate win (opponent has no pieces) -----
            if new_board.count(opp_color) == 0:
                return move

            # ----- check for mate (opponent has no legal moves) -----
            if phase == "movement":
                if not self.legal_movements(new_board, opp_color):
                    return move

            # ----- three‑fold repetition detection -----
            next_player = opp_color
            if self.would_be_threefold(history, tuple(new_board), next_player):
                # drawing move – treat as very poor
                score = -1000
            else:
                # ----- evaluate the resulting position -----
                score = self.evaluate(new_board,
                                      self.color,
                                      opp_color,
                                      phase,
                                      original_board=board)

            # keep the best move (random tie‑break)
            if score > best_score:
                best_score = score
                best_move = move
            elif score == best_score:
                if random.random() < 0.5:
                    best_move = move

        return best_move

    # ----------------------------------------------------------------------
    # Helpers – board manipulation
    # ----------------------------------------------------------------------
    def legal_placements(self, board):
        """All empty spots where a piece can be placed."""
        return [i for i in range(24) if board[i] == '']

    def legal_movements(self, board, color):
        """All (from, to) slides for the given colour."""
        moves = []
        for f in range(24):
            if board[f] != color:
                continue
            for t in ADJACENCY[f]:
                if board[t] == '':
                    moves.append((f, t))
        return moves

    def simulate_move(self, board, move, colour, phase):
        """
        Apply the move on a copy of the board and run the capture rules.
        Returns the board after all captures are resolved.
        """
        new_board = list(board)

        if phase == "placement":
            spot = move
            new_board[spot] = colour
            active_spot = spot
        else:                     # movement
            frm, to = move
            new_board[frm] = ''
            new_board[to] = colour
            active_spot = to

        # Apply the “Overwhelm” capture procedure
        return self.apply_captures(new_board, colour, active_spot)

    def apply_captures(self, board, mover, active_spot):
        """
        Implements the exact capture sequence described in the rules:
          1) active‑piece suicide check,
          2a) friendly captures,
          2b) opponent captures (after friendly removal).
        """
        board = list(board)          # mutable copy
        opp = 'W' if mover == 'B' else 'B'

        # ---- 1. Active piece suicide check ----
        if self.is_captured(active_spot, board):
            board[active_spot] = ''   # it dies immediately
            active_survived = False
        else:
            active_survived = True

        # If the active piece died we stop here – no further captures.
        if not active_survived:
            return board

        # ---- 2a. Remove all friendly pieces that are overwhelmed ----
        friendly_dead = [i for i in range(24)
                         if board[i] == mover and self.is_captured(i, board)]
        for i in friendly_dead:
            board[i] = ''

        # ---- 2b. Now remove opponent pieces that are overwhelmed ----
        opp_dead = [i for i in range(24)
                    if board[i] == opp and self.is_captured(i, board)]
        for i in opp_dead:
            board[i] = ''

        return board

    # ----------------------------------------------------------------------
    # Capture predicate
    # ----------------------------------------------------------------------
    def is_captured(self, spot, board):
        """
        True iff the piece on `spot` has
          *no empty neighbours*  AND
          *more opponent neighbours than friendly neighbours*.
        """
        if board[spot] == '':
            return False

        col = board[spot]
        opp = 'W' if col == 'B' else 'B'

        empty = friendly = opponent = 0
        for nb in ADJACENCY[spot]:
            if board[nb] == '':
                empty += 1
            elif board[nb] == col:
                friendly += 1
            else:
                opponent += 1

        if empty != 0:
            return False
        return opponent > friendly

    # ----------------------------------------------------------------------
    # Repetition detection
    # ----------------------------------------------------------------------
    def would_be_threefold(self, history, board_tuple, next_player):
        """Return True if the given (board, player) occurs twice already."""
        cnt = 0
        for b, p in history:
            if b == board_tuple and p == next_player:
                cnt += 1
                if cnt >= 2:
                    return True
        return False

    # ----------------------------------------------------------------------
    # Position evaluation
    # ----------------------------------------------------------------------
    def evaluate(self, board, colour, opp, phase, original_board):
        """
        Simple weighted sum:
          * material (piece count)
          * captures performed in this move
          * mobility (legal moves) – only in movement phase
          * positional strength (sum of vertex degrees)
          * penalty if we end up with no moves.
        """
        # ----- material -----
        my_pieces = board.count(colour)
        opp_pieces = board.count(opp)

        # ----- captures realised in this move -----
        my_before = original_board.count(colour)
        opp_before = original_board.count(opp)
        captured_me = my_before - my_pieces
        captured_opp = opp_before - opp_pieces

        piece_score = 100 * (my_pieces - opp_pieces)
        capture_score = 50 * (captured_opp - captured_me)

        # ----- mobility (movement phase only) -----
        if phase == "movement":
            my_moves = len(self.legal_movements(board, colour))
            opp_moves = len(self.legal_movements(board, opp))
            mobility_score = 5 * (my_moves - opp_moves)
            # penalise ending the turn with zero moves
            if my_moves == 0:
                mobility_score -= 200
        else:
            mobility_score = 0

        # ----- positional control (vertex degree) -----
        pos_score = 0
        for i in range(24):
            if board[i] == colour:
                pos_score += len(ADJACENCY[i])
            elif board[i] == opp:
                pos_score -= len(ADJACENCY[i])

        return piece_score + capture_score + mobility_score + pos_score
