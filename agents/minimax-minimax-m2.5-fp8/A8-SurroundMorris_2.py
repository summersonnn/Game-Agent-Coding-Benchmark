"""
Agent Code: A8-SurroundMorris
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-13 14:10:12
"""



import random

class SurroundMorrisAgent:
    """
    A greedy agent for Surround Morris.
    It evaluates every legal placement / movement by simulating the
    board after the move and applying the exact capture rules
    (Suicide‑First, Self‑Harm‑Priority).  The resulting board is scored
    by a weighted sum of remaining pieces (piece count dominates) and
    the degree of the occupied spots.
    """

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        # degree (number of neighbours) for each spot – used as positional weight
        self.degree = {spot: len(ADJACENCY[spot]) for spot in range(24)}

    # -----------------------------------------------------------------
    # helpers for capture logic
    # -----------------------------------------------------------------
    def _is_captured(self, board, spot, colour):
        """Return True if the piece at *spot* of *colour* is captured."""
        neighbours = ADJACENCY[spot]
        empty_nb = friendly_nb = opponent_nb = 0
        opponent = 'W' if colour == 'B' else 'B'

        for nb in neighbours:
            if board[nb] == '':
                empty_nb += 1
            elif board[nb] == colour:
                friendly_nb += 1
            else:  # opponent piece
                opponent_nb += 1

        # a piece is safe if it has any empty neighbour
        if empty_nb > 0:
            return False
        # otherwise it is captured when opponents outnumber friends
        return opponent_nb > friendly_nb

    def _simulate_move(self, board, colour, move, phase):
        """
        Apply a placement or movement *move* made by *colour* and process
        captures exactly as the game engine does.

        Returns
        -------
        new_board : list
            The board after captures have been resolved.
        active_captured : bool
            True if the piece just placed/moved was removed in the
            “Suicide‑First” step (in which case no further captures occur).
        """
        new_board = board[:]               # shallow copy
        opponent = 'W' if colour == 'B' else 'B'

        # -----------------------------------------------------------------
        # 1. perform the raw placement / movement
        # -----------------------------------------------------------------
        if phase == 'placement':           # move is an integer spot
            spot = move
            new_board[spot] = colour
            active_spot = spot
        else:                               # movement phase – move is (from, to)
            frm, to = move
            new_board[frm] = ''
            new_board[to] = colour
            active_spot = to

        # -----------------------------------------------------------------
        # 2. “Suicide‑First” – check the active piece
        # -----------------------------------------------------------------
        if self._is_captured(new_board, active_spot, colour):
            # the active piece is removed immediately, turn ends
            new_board[active_spot] = ''
            return new_board, True

        # -----------------------------------------------------------------
        # 3. Universal sweep: friendly pieces first, then opponents
        # -----------------------------------------------------------------
        # 3a. remove all friendly pieces that are already overwhelmed
        to_remove_friendly = [
            s for s in range(24)
            if new_board[s] == colour and self._is_captured(new_board, s, colour)
        ]
        for s in to_remove_friendly:
            new_board[s] = ''

        # 3b. re‑evaluate opponent pieces after friendly removals
        to_remove_opponent = [
            s for s in range(24)
            if new_board[s] == opponent and self._is_captured(new_board, s, opponent)
        ]
        for s in to_remove_opponent:
            new_board[s] = ''

        return new_board, False

    # -----------------------------------------------------------------
    # evaluation
    # -----------------------------------------------------------------
    def _evaluate(self, board, my_colour):
        """Simple static evaluation: piece count dominates, positional weight adds small tie‑breaker."""
        opponent = 'W' if my_colour == 'B' else 'B'

        my_piece_cnt = sum(1 for c in board if c == my_colour)
        opp_piece_cnt = sum(1 for c in board if c == opponent)

        my_positional = sum(self.degree[i] for i, c in enumerate(board) if c == my_colour)
        opp_positional = sum(self.degree[i] for i, c in enumerate(board) if c == opponent)

        # piece count is worth 100 points, position adds at most a few points
        return (my_piece_cnt - opp_piece_cnt) * 100 + (my_positional - opp_positional)

    # -----------------------------------------------------------------
    # legal move generators
    # -----------------------------------------------------------------
    def _legal_placements(self, board, colour):
        return [i for i, c in enumerate(board) if c == '']

    def _legal_movements(self, board, colour):
        moves = []
        for frm in range(24):
            if board[frm] != colour:
                continue
            for nb in ADJACENCY[frm]:
                if board[nb] == '':
                    moves.append((frm, nb))
        return moves

    # -----------------------------------------------------------------
    # main decision routine
    # -----------------------------------------------------------------
    def make_move(self, state, feedback=None):
        board = state["board"]
        phase = state["phase"]
        my_colour = state["your_color"]

        # -----------------------------------------------------------------
        # generate all legal moves for the current phase
        # -----------------------------------------------------------------
        if phase == "placement":
            candidates = self._legal_placements(board, my_colour)
            move_type = "placement"
        else:
            candidates = self._legal_movements(board, my_colour)
            move_type = "movement"

        # no legal move – should not happen in normal play, but guard anyway
        if not candidates:
            # return a dummy move; the engine will handle the loss
            return candidates[0] if candidates else (0, 1)

        # -----------------------------------------------------------------
        # evaluate each candidate by simulating the board after the move
        # -----------------------------------------------------------------
        best_score = -10**9
        best_moves = []

        for mv in candidates:
            new_board, _ = self._simulate_move(board, my_colour, mv, phase)
            score = self._evaluate(new_board, my_colour)

            if score > best_score:
                best_score = score
                best_moves = [mv]
            elif score == best_score:
                best_moves.append(mv)

        # random tie‑breaking
        return random.choice(best_moves)
