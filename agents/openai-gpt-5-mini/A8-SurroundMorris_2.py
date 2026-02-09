"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-09 18:54:48
"""



class SurroundMorrisAgent:
    """
    A heuristic Surround Morris agent.

    Strategy highlights:
    - Avoids immediate suicide (placing/moving into a position where the active piece dies).
    - Simulates the engine's capture resolution (Suicide First, then friendly removals, then enemy removals)
      to pick moves that maximize material gain and avoid "friendly fire".
    - Prioritizes immediate wins (elimination or mate).
    - Tries to avoid causing 3-fold repetition (draw) unless that is preferable.
    - Prefers central/crossroad control when ties occur.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'B' or 'W'

    # --- Helper methods ---
    def _other(self, c: str) -> str:
        return 'B' if c == 'W' else 'W'

    def _is_overwhelmed(self, spot: int, board: list, color: str) -> bool:
        """
        Returns True if the piece of 'color' at 'spot' would be captured
        according to the capture rule given the current board state.
        Assumes board[spot] == color.
        """
        neighbors = ADJACENCY.get(spot, [])
        empty_neighbors = sum(1 for nb in neighbors if board[nb] == '')
        if empty_neighbors > 0:
            return False
        friendlies = sum(1 for nb in neighbors if board[nb] == color)
        opponents = sum(1 for nb in neighbors if board[nb] == self._other(color))
        return opponents > friendlies

    def _simulate_after_action(self, board: list, color: str, placement_spot: int = None,
                               move_from: int = None, move_to: int = None):
        """
        Simulate the board after either placing at placement_spot (if given)
        or moving move_from -> move_to (if given). Returns (board_after, metrics_dict)
        where metrics_dict contains:
            - active_died: bool
            - friendlies_removed: int
            - enemies_removed: int
        Implements Suicide First and Self-Harm Priority rules exactly.
        """
        b = board.copy()
        assert (placement_spot is None) ^ (move_from is None and move_to is not None)
        active_spot = None
        if placement_spot is not None:
            if b[placement_spot] != '':
                # invalid placement; but caller should avoid. Return unchanged with heavy penalty semantics.
                return b, {"active_died": False, "friendlies_removed": 0, "enemies_removed": 0}
            b[placement_spot] = color
            active_spot = placement_spot
        else:
            # movement
            if b[move_from] != color or b[move_to] != '':
                # invalid move - return board unchanged
                return b, {"active_died": False, "friendlies_removed": 0, "enemies_removed": 0}
            b[move_from] = ''
            b[move_to] = color
            active_spot = move_to

        # Step 1: active piece suicide check
        if self._is_overwhelmed(active_spot, b, color):
            b[active_spot] = ''
            return b, {"active_died": True, "friendlies_removed": 0, "enemies_removed": 0}

        # Step 2a: remove all friendly overwhelmed pieces (simultaneously)
        friendly_positions = [i for i in range(24) if b[i] == color]
        friendly_overwhelmed = [i for i in friendly_positions if self._is_overwhelmed(i, b, color)]
        for i in friendly_overwhelmed:
            b[i] = ''
        friendlies_removed = len(friendly_overwhelmed)

        # Step 2b: re-check enemies on the new board and remove overwhelmed enemies
        opp = self._other(color)
        enemy_positions = [i for i in range(24) if b[i] == opp]
        enemy_overwhelmed = [i for i in enemy_positions if self._is_overwhelmed(i, b, opp)]
        for i in enemy_overwhelmed:
            b[i] = ''
        enemies_removed = len(enemy_overwhelmed)

        return b, {"active_died": False, "friendlies_removed": friendlies_removed, "enemies_removed": enemies_removed}

    def _opponent_has_moves(self, board: list, opp_color: str) -> bool:
        for i in range(24):
            if board[i] != opp_color:
                continue
            for nb in ADJACENCY[i]:
                if board[nb] == '':
                    return True
        return False

    def _count_pieces(self, board: list):
        return {'B': board.count('B'), 'W': board.count('W')}

    # --- Main interface ---
    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        history = state.get("history", [])

        # Sanity: prefer the state color (engine authoritative)
        self.color = color

        # Avoid returning the same invalid attempted move on retries
        attempted_previous = None
        if feedback:
            attempted_previous = feedback.get("attempted_move", None)

        # current on-board counts
        cur_counts = self._count_pieces(board)
        cur_own = cur_counts[color]
        cur_opp = cur_counts[opp]

        # Useful constants
        CROSSROADS = {4, 10, 13, 19}

        if phase == "placement":
            empties = [i for i in range(24) if board[i] == '']
            if not empties:
                # No legal placements (shouldn't normally happen)
                return 0

            best_score = -10**9
            best_moves = []

            for spot in empties:
                move_repr = spot
                if attempted_previous is not None and attempted_previous == move_repr:
                    # avoid repeating same invalid attempt
                    continue

                b_after, metrics = self._simulate_after_action(board, color, placement_spot=spot)

                # Immediate win by elimination?
                counts_after = self._count_pieces(b_after)
                if counts_after[opp] == 0:
                    return spot

                # Check repetition: will the next position (board_after, opponent) reach 3 occurrences?
                hist_key = (tuple(b_after), opp)
                rep_count = sum(1 for h in history if h == hist_key)
                causes_third_repetition = (rep_count >= 2)

                # Heuristic scoring
                own_final = counts_after[color]
                opp_final = counts_after[opp]
                opp_removed = cur_opp - opp_final
                own_removed = cur_own - own_final

                score = 0
                # prioritize removing opponent pieces
                score += 9000 * opp_removed
                # material difference
                score += 1000 * (own_final - opp_final)
                # prefer to keep our pieces
                score -= 800 * own_removed
                # heavy penalty for active piece suicide (even if it leads to some enemy removals - seldom good)
                if metrics["active_died"]:
                    score -= 5000
                # penalty for friendly removals
                score -= 700 * metrics["friendlies_removed"]
                # bonus for placing on crossroads
                if spot in CROSSROADS:
                    score += 50
                # prefer spots that leave more empty neighbors for the placed piece
                empty_nbs = sum(1 for nb in ADJACENCY[spot] if b_after[nb] == '')
                score += 5 * empty_nbs
                # prefer to increase overall liberties for our pieces
                sum_lib_after = sum(sum(1 for nb in ADJACENCY[i] if b_after[nb] == '') for i in range(24) if b_after[i] == color)
                sum_lib_before = sum(sum(1 for nb in ADJACENCY[i] if board[nb] == '') for i in range(24) if board[i] == color)
                score += 2 * (sum_lib_after - sum_lib_before)

                # repetition penalty (avoid drawing unless necessary)
                if causes_third_repetition:
                    # if draw is strictly worse than current best, avoid it; penalize heavily
                    score -= 4000

                if score > best_score:
                    best_score = score
                    best_moves = [spot]
                elif score == best_score:
                    best_moves.append(spot)

            if not best_moves:
                # fallback: random empty
                return random.choice(empties)
            return random.choice(best_moves)

        else:
            # movement phase
            moves = []
            for i in range(24):
                if board[i] != color:
                    continue
                for nb in ADJACENCY[i]:
                    if board[nb] == '':
                        moves.append((i, nb))
            if not moves:
                # No legal moves: agent is stalemated (should lead to loss). Return a dummy move similar to reference.
                return (0, 1)

            best_score = -10**9
            best_moves = []

            for mv in moves:
                if attempted_previous is not None and attempted_previous == mv:
                    continue

                f, t = mv
                b_after, metrics = self._simulate_after_action(board, color, move_from=f, move_to=t)

                counts_after = self._count_pieces(b_after)
                own_final = counts_after[color]
                opp_final = counts_after[opp]
                opp_removed = cur_opp - opp_final
                own_removed = cur_own - own_final

                # Immediate win checks
                if opp_final == 0:
                    return mv  # elimination win
                # Check if opponent has any moves on their turn (mate)
                opp_has_moves = self._opponent_has_moves(b_after, opp)
                if not opp_has_moves:
                    return mv  # mate (immediate win)

                # repetition check: would the resulting (board_after, opponent) be the 3rd occurrence?
                hist_key = (tuple(b_after), opp)
                rep_count = sum(1 for h in history if h == hist_key)
                causes_third_repetition = (rep_count >= 2)

                # Scoring heuristics
                score = 0
                score += 9000 * opp_removed
                score += 1000 * (own_final - opp_final)
                score -= 800 * own_removed
                if metrics["active_died"]:
                    score -= 5000
                score -= 700 * metrics["friendlies_removed"]
                # small bonus for moving into crossroads
                if t in CROSSROADS:
                    score += 60
                # prefer moves that increase our liberties
                sum_lib_after = sum(sum(1 for nb in ADJACENCY[i] if b_after[nb] == '') for i in range(24) if b_after[i] == color)
                sum_lib_before = sum(sum(1 for nb in ADJACENCY[i] if board[nb] == '') for i in range(24) if board[i] == color)
                score += 3 * (sum_lib_after - sum_lib_before)
                # prefer that moved piece has empty neighbors
                dest_empty_nbs = sum(1 for nb in ADJACENCY[t] if b_after[nb] == '')
                score += 6 * dest_empty_nbs

                if causes_third_repetition:
                    score -= 4000

                if score > best_score:
                    best_score = score
                    best_moves = [mv]
                elif score == best_score:
                    best_moves.append(mv)

            if not best_moves:
                return random.choice(moves)
            return random.choice(best_moves)
