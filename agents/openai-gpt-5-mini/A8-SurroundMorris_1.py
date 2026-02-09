"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-5-mini
Run: 3
Generated: 2026-02-09 18:54:48
"""



class SurroundMorrisAgent:
    """
    SurroundMorrisAgent: a heuristic agent for Surround Morris.

    Strategy highlights:
    - Simulates the engine's capture sequence (Suicide-first, then friendly sweep, then enemy sweep)
    - Avoids obvious suicides and friendly-fire sacrifices unless they capture enemy pieces or produce mate
    - Prefers captures, mobility, and control of high-degree spots (crossroads)
    - Avoids creating immediate 3-fold repetition (draw) unless no better option
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.rng = random.Random()

    def make_move(self, state: dict, feedback: dict | None = None):
        board = list(state["board"])
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = dict(state.get("pieces_in_hand", {"B": 0, "W": 0}))
        history = list(state.get("history", []))

        before_own_moves = len(self._legal_moves(board, color))
        before_opp_moves = len(self._legal_moves(board, opp))

        # Placement phase
        if phase == "placement":
            empties = [i for i in range(24) if board[i] == '']
            if not empties:
                return 0

            best_score = -10**9
            best_moves = []

            for dest in empties:
                sim_board, removed_friendly, removed_enemy, active_died = self._simulate(board, color, dest)

                new_in_hand = pieces_in_hand.get(color, 0) - 1
                after_own = sim_board.count(color)
                after_opp = sim_board.count(opp)
                after_own_moves = len(self._legal_moves(sim_board, color))
                after_opp_moves = len(self._legal_moves(sim_board, opp))

                rep_tuple = (tuple(sim_board), opp)
                rep_count = history.count(rep_tuple)

                # Scoring heuristics
                score = 0

                # Immediate elimination/win/loss
                if after_opp == 0:
                    score += 100000  # capture-all -> win
                if new_in_hand == 0 and after_own == 0:
                    score -= 100000  # placement that loses you the game -> avoid

                # Capture rewards / penalties
                score += 1200 * removed_enemy
                score -= 2000 * removed_friendly

                # Strong penalty for active suicide (it dies before it can help)
                if active_died:
                    score -= 1500

                # Mobility: prefer moves that increase your mobility and reduce opponent's
                score += 8 * (after_own_moves - before_own_moves)
                score += 4 * (before_opp_moves - after_opp_moves)

                # Positional bonus: prefer crossroads (deg 4), then T-junctions (deg 3)
                deg = len(ADJACENCY[dest])
                if deg == 4:
                    score += 6
                elif deg == 3:
                    score += 2

                # Avoid immediate 3-fold repetition (draw) strongly
                if rep_count >= 2:
                    score -= 800

                # Small randomness to break ties
                score += self.rng.random() * 1e-3

                if score > best_score:
                    best_score = score
                    best_moves = [dest]
                elif abs(score - best_score) < 1e-9:
                    best_moves.append(dest)

            if best_moves:
                return self.rng.choice(best_moves)
            return self.rng.choice(empties)

        # Movement phase
        else:
            moves = []
            for s in range(24):
                if board[s] != color:
                    continue
                for n in ADJACENCY[s]:
                    if board[n] == '':
                        moves.append((s, n))

            if not moves:
                # No legal moves; the engine will detect mate/stalemate. Return a placeholder.
                return (0, 1)

            best_score = -10**9
            best_moves = []

            for mv in moves:
                sim_board, removed_friendly, removed_enemy, active_died = self._simulate(board, color, mv)

                after_own = sim_board.count(color)
                after_opp = sim_board.count(opp)
                after_own_moves = len(self._legal_moves(sim_board, color))
                after_opp_moves = len(self._legal_moves(sim_board, opp))

                rep_tuple = (tuple(sim_board), opp)
                rep_count = history.count(rep_tuple)

                score = 0

                # Immediate elimination/win by capture
                if after_opp == 0:
                    score += 100000

                # Mate: opponent has pieces but no legal moves -> immediate win by mate
                if after_opp > 0 and after_opp_moves == 0:
                    score += 90000

                # Capture rewards / penalties
                score += 1200 * removed_enemy
                score -= 2000 * removed_friendly

                # Active death is usually very bad (suicide)
                if active_died:
                    score -= 4000

                # Mobility and interference effects
                score += 10 * (after_own_moves - before_own_moves)
                score += 5 * (before_opp_moves - after_opp_moves)

                # Positional preference
                deg = len(ADJACENCY[mv[1]])
                if deg == 4:
                    score += 6
                elif deg == 3:
                    score += 2

                # Avoid making a move that immediately creates a 3-fold repetition (draw)
                if rep_count >= 2:
                    score -= 800

                # Small randomness
                score += self.rng.random() * 1e-3

                if score > best_score:
                    best_score = score
                    best_moves = [mv]
                elif abs(score - best_score) < 1e-9:
                    best_moves.append(mv)

            if best_moves:
                return self.rng.choice(best_moves)
            return self.rng.choice(moves)

    @staticmethod
    def _is_overwhelmed(board: list[str], spot: int) -> bool:
        """Return True if the piece at `spot` meets the overwhelm capture condition."""
        if board[spot] == '':
            return False
        color = board[spot]
        opp = 'B' if color == 'W' else 'W'
        empty_neighbors = 0
        friendly_neighbors = 0
        opponent_neighbors = 0
        for n in ADJACENCY[spot]:
            if board[n] == '':
                empty_neighbors += 1
            elif board[n] == color:
                friendly_neighbors += 1
            else:
                opponent_neighbors += 1
        return (empty_neighbors == 0) and (opponent_neighbors > friendly_neighbors)

    @classmethod
    def _simulate(cls, board: list[str], mover_color: str, move):
        """
        Simulate the engine's capture resolution for a given move.

        move: int for placement, or (src, dst) tuple for movement.

        Returns: (new_board_list, removed_friendly_count, removed_enemy_count, active_died_bool)
        """
        b = list(board)
        opp = 'B' if mover_color == 'W' else 'W'
        removed_friendly = 0
        removed_enemy = 0
        active_died = False

        # Apply the move
        if isinstance(move, int):
            dest = move
            b[dest] = mover_color
            active_spot = dest
        else:
            src, dest = move
            b[src] = ''
            b[dest] = mover_color
            active_spot = dest

        # Step 1: Active piece suicide check
        if cls._is_overwhelmed(b, active_spot):
            b[active_spot] = ''
            removed_friendly = 1  # active piece removed
            active_died = True
            return b, removed_friendly, removed_enemy, active_died

        # Step 2a: Remove all friendly pieces that are overwhelmed (simultaneously)
        friendly_positions = [i for i, p in enumerate(b) if p == mover_color]
        to_remove_friendly = [pos for pos in friendly_positions if cls._is_overwhelmed(b, pos)]
        for pos in to_remove_friendly:
            b[pos] = ''
        removed_friendly = len(to_remove_friendly)

        # Step 2b: Re-check and remove enemy pieces that are overwhelmed
        enemy_positions = [i for i, p in enumerate(b) if p == opp]
        to_remove_enemy = [pos for pos in enemy_positions if cls._is_overwhelmed(b, pos)]
        for pos in to_remove_enemy:
            b[pos] = ''
        removed_enemy = len(to_remove_enemy)

        return b, removed_friendly, removed_enemy, active_died

    @staticmethod
    def _legal_moves(board: list[str], color: str):
        moves = []
        for spot, p in enumerate(board):
            if p != color:
                continue
            for n in ADJACENCY[spot]:
                if board[n] == '':
                    moves.append((spot, n))
        return moves
