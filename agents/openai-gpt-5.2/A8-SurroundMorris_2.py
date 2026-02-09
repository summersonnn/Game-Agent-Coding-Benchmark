"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-09 19:10:28
"""



import random

class SurroundMorrisAgent:
    """
    Heuristic + shallow minimax agent for Surround Morris.
    Assumes global ADJACENCY is available at runtime.
    """

    # Utility constants (net utility = my_points - opp_points)
    MATE_NET_UTILITY = 14.0  # +7 vs -7 => net +14
    INF = 10**9

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.rng = random.Random()

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        my = state["your_color"]
        opp = state["opponent_color"]

        # Robust fallback on retries: return a random legal move (excluding last attempted if possible)
        attempted = None if not feedback else feedback.get("attempted_move", None)
        if feedback is not None:
            if phase == "placement":
                actions = self._legal_placements(board)
                if attempted in actions and len(actions) > 1:
                    actions = [a for a in actions if a != attempted]
                return self.rng.choice(actions) if actions else 0
            else:
                actions = self._legal_moves(board, my)
                if attempted in actions and len(actions) > 1:
                    actions = [a for a in actions if a != attempted]
                return self.rng.choice(actions) if actions else (0, 1)

        # Normal play: search
        sim = {
            "board": board[:],
            "phase": phase,
            "current_player": my,
            "in_hand": dict(state["pieces_in_hand"]),
        }

        if phase == "placement":
            actions = self._legal_placements(board)
            if not actions:
                return 0

            # Beam to keep depth-2 placement manageable
            actions = self._beam_actions(sim, actions, beam=10)

            best_val = -self.INF
            best_actions = []
            for a in actions:
                sim2, terminal, val = self._apply_action(sim, a, root_history=state.get("history", []))
                if not terminal:
                    # depth-2 (us then opp)
                    val = self._minimax(sim2, depth=1, alpha=-self.INF, beta=self.INF)
                if val > best_val + 1e-9:
                    best_val = val
                    best_actions = [a]
                elif abs(val - best_val) <= 1e-9:
                    best_actions.append(a)

            return self.rng.choice(best_actions) if best_actions else self.rng.choice(actions)

        else:
            actions = self._legal_moves(board, my)
            if not actions:
                return (0, 1)  # should not be called if mated, but keep type-correct

            # Adaptive depth: deeper when branching is small
            if len(actions) <= 18:
                depth = 3
                beam = 14
            elif len(actions) <= 30:
                depth = 2
                beam = 14
            else:
                depth = 2
                beam = 10

            actions = self._beam_actions(sim, actions, beam=beam)

            best_val = -self.INF
            best_actions = []
            for a in actions:
                sim2, terminal, val = self._apply_action(sim, a, root_history=state.get("history", []))
                if not terminal:
                    val = self._minimax(sim2, depth=depth - 1, alpha=-self.INF, beta=self.INF)
                if val > best_val + 1e-9:
                    best_val = val
                    best_actions = [a]
                elif abs(val - best_val) <= 1e-9:
                    best_actions.append(a)

            return self.rng.choice(best_actions) if best_actions else self.rng.choice(actions)

    # ---------------------------
    # Core rules / simulation
    # ---------------------------

    def _opponent(self, c: str) -> str:
        return "W" if c == "B" else "B"

    def _legal_placements(self, board: list[str]) -> list[int]:
        return [i for i in range(24) if board[i] == ""]

    def _legal_moves(self, board: list[str], color: str) -> list[tuple[int, int]]:
        moves = []
        for s in range(24):
            if board[s] != color:
                continue
            for n in ADJACENCY[s]:
                if board[n] == "":
                    moves.append((s, n))
        return moves

    def _neighbor_counts(self, spot: int, board: list[str]):
        c = board[spot]
        friends = opps = empties = 0
        for n in ADJACENCY[spot]:
            v = board[n]
            if v == "":
                empties += 1
            elif v == c:
                friends += 1
            else:
                opps += 1
        return friends, opps, empties

    def _is_captured(self, spot: int, board: list[str]) -> bool:
        if board[spot] == "":
            return False
        friends, opps, empties = self._neighbor_counts(spot, board)
        return (empties == 0) and (opps > friends)

    def _apply_captures(self, board: list[str], active_spot: int, mover: str) -> tuple[list[str], bool]:
        """
        Returns (board, active_suicided).
        Implements:
          1) active piece suicide check (if captured -> remove, end; no sweep)
          2) sweep friendlies first (simultaneous), then re-check enemies
        """
        if active_spot is None:
            return board, False

        if board[active_spot] == mover and self._is_captured(active_spot, board):
            board[active_spot] = ""
            return board, True

        # Step 2a: remove overwhelmed friendlies (simultaneous)
        friendly_to_remove = [i for i in range(24) if board[i] == mover and self._is_captured(i, board)]
        for i in friendly_to_remove:
            board[i] = ""

        # Step 2b: re-check enemies after friendly removals
        enemy = self._opponent(mover)
        enemy_to_remove = [i for i in range(24) if board[i] == enemy and self._is_captured(i, board)]
        for i in enemy_to_remove:
            board[i] = ""

        return board, False

    def _counts(self, board: list[str]) -> dict:
        return {"B": board.count("B"), "W": board.count("W")}

    def _apply_action(self, sim: dict, action, root_history: list[tuple] | None = None):
        """
        Apply one action for sim['current_player'], including captures.
        Returns: (new_sim, terminal, utility_net)
        If root_history is provided, checks 3-fold repetition draw for the
        immediate next-to-move state and returns terminal draw net=0.
        """
        board = sim["board"][:]
        phase = sim["phase"]
        mover = sim["current_player"]
        enemy = self._opponent(mover)
        in_hand = dict(sim["in_hand"])

        active_spot = None

        if phase == "placement":
            spot = int(action)
            board[spot] = mover
            in_hand[mover] -= 1
            active_spot = spot
        else:
            src, dst = action
            board[src] = ""
            board[dst] = mover
            active_spot = dst

        board, active_suicided = self._apply_captures(board, active_spot, mover)
        counts = self._counts(board)

        # Elimination check with "mover checked first" priority
        mover_elim = False
        enemy_elim = False
        if phase == "movement":
            mover_elim = (counts[mover] == 0)
            enemy_elim = (counts[enemy] == 0)
        else:
            mover_elim = (counts[mover] == 0 and in_hand[mover] == 0)
            enemy_elim = (counts[enemy] == 0 and in_hand[enemy] == 0)

        if mover_elim:
            # mover loses; opponent scores opponent remaining pieces on board
            # net utility from self.color perspective:
            winner = enemy
            winner_pts = counts[winner]
            net = winner_pts if winner == self.color else -winner_pts
            return None, True, net

        if enemy_elim:
            winner = mover
            winner_pts = counts[winner]
            net = winner_pts if winner == self.color else -winner_pts
            return None, True, net

        # Phase transition
        next_phase = phase
        if phase == "placement" and in_hand["B"] == 0 and in_hand["W"] == 0:
            next_phase = "movement"

        next_player = enemy

        # Root-only: repetition draw check (position + player-to-move)
        if root_history is not None:
            key = (tuple(board), next_player)
            seen = 0
            for h_board, h_player in root_history:
                if h_board == key[0] and h_player == key[1]:
                    seen += 1
            if seen >= 2:
                # If this state would occur for the 3rd time, game ends immediately in DRAW (net=0)
                return None, True, 0.0

        new_sim = {
            "board": board,
            "phase": next_phase,
            "current_player": next_player,
            "in_hand": in_hand,
        }

        # Mate check happens at the start of the next player's turn (movement phase only)
        if next_phase == "movement":
            legal = self._legal_moves(board, next_player)
            if not legal:
                # next_player is stuck and loses by mate
                winner = self._opponent(next_player)
                net = self.MATE_NET_UTILITY if winner == self.color else -self.MATE_NET_UTILITY
                return None, True, net

        return new_sim, False, 0.0

    # ---------------------------
    # Search
    # ---------------------------

    def _minimax(self, sim: dict, depth: int, alpha: float, beta: float) -> float:
        # Mate-at-start check (for internal nodes, to be safe)
        if sim["phase"] == "movement":
            cur = sim["current_player"]
            if not self._legal_moves(sim["board"], cur):
                winner = self._opponent(cur)
                return self.MATE_NET_UTILITY if winner == self.color else -self.MATE_NET_UTILITY

        if depth <= 0:
            return self._heuristic(sim)

        cur = sim["current_player"]
        maximizing = (cur == self.color)

        if sim["phase"] == "placement":
            actions = self._legal_placements(sim["board"])
            if not actions:
                return self._heuristic(sim)
            # smaller beam in deeper nodes
            actions = self._beam_actions(sim, actions, beam=8)
        else:
            actions = self._legal_moves(sim["board"], cur)
            if not actions:
                # mate handled above; fallback
                winner = self._opponent(cur)
                return self.MATE_NET_UTILITY if winner == self.color else -self.MATE_NET_UTILITY
            actions = self._beam_actions(sim, actions, beam=10)

        if maximizing:
            value = -self.INF
            for a in actions:
                sim2, terminal, tval = self._apply_action(sim, a, root_history=None)
                v = tval if terminal else self._minimax(sim2, depth - 1, alpha, beta)
                if v > value:
                    value = v
                if value > alpha:
                    alpha = value
                if beta <= alpha:
                    break
            return value
        else:
            value = self.INF
            for a in actions:
                sim2, terminal, tval = self._apply_action(sim, a, root_history=None)
                v = tval if terminal else self._minimax(sim2, depth - 1, alpha, beta)
                if v < value:
                    value = v
                if value < beta:
                    beta = value
                if beta <= alpha:
                    break
            return value

    def _beam_actions(self, sim: dict, actions: list, beam: int) -> list:
        if len(actions) <= beam:
            return actions
        scored = []
        for a in actions:
            sim2, terminal, tval = self._apply_action(sim, a, root_history=None)
            if terminal:
                scored.append((tval, a))
            else:
                scored.append((self._heuristic(sim2), a))
        scored.sort(key=lambda x: x[0], reverse=True if sim["current_player"] == self.color else False)
        return [a for _, a in scored[:beam]]

    # ---------------------------
    # Heuristic evaluation (net: self - opp)
    # ---------------------------

    def _pos_weight(self, spot: int) -> float:
        deg = len(ADJACENCY[spot])
        # favor crossroads > T-junctions > corners
        if deg == 4:
            return 0.20
        if deg == 3:
            return 0.12
        return 0.06  # deg==2

    def _heuristic(self, sim: dict) -> float:
        board = sim["board"]
        my = self.color
        opp = self._opponent(my)

        counts = self._counts(board)
        material = float(counts[my] - counts[opp])  # main signal (net)

        # Positional + liberties + "almost trapped" signals
        pos = 0.0
        liberty = 0.0
        trap = 0.0

        for i, v in enumerate(board):
            if v == "":
                continue
            friends, opps, empties = self._neighbor_counts(i, board)

            w = self._pos_weight(i)
            if v == my:
                pos += w
                liberty += 0.04 * empties
                # penalize being close to blocked
                if empties == 1:
                    liberty -= 0.10
                # extra penalty if many adjacent enemies while low air
                liberty -= 0.03 * max(0, opps - friends)
            else:
                pos -= w
                liberty -= 0.04 * empties
                if empties == 1:
                    liberty += 0.10
                liberty += 0.03 * max(0, opps - friends)

            # encourage creating near-captures (empties==1)
            if v == opp and empties == 1:
                trap += 0.10 + 0.04 * max(0, friends - opps)  # friends/opps are from opp's perspective
            if v == my and empties == 1:
                trap -= 0.10 + 0.04 * max(0, friends - opps)

        mobility = 0.0
        if sim["phase"] == "movement":
            my_moves = len(self._legal_moves(board, my))
            opp_moves = len(self._legal_moves(board, opp))
            mobility = 0.02 * float(my_moves - opp_moves)

        # Keep magnitudes comparable to terminal values (~14)
        return 1.2 * material + pos + liberty + trap + mobility
