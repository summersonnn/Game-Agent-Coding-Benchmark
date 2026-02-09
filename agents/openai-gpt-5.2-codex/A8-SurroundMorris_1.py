"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-5.2-codex
Run: 1
Generated: 2026-02-09 19:15:26
"""



class SurroundMorrisAgent:
    """
    A heuristic agent for Surround Morris.
    Chooses moves by simulating captures and evaluating the resulting board.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.rng = random.Random()

        # Positional weights based on node degree
        self.pos_values = {}
        for i in range(24):
            deg = len(ADJACENCY[i])
            if deg >= 4:
                val = 3  # crossroads
            elif deg == 3:
                val = 2  # T-junctions
            else:
                val = 1  # corners
            self.pos_values[i] = val

    # ---------- Core API ----------

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]

        if phase == "placement":
            return self._choose_placement(board, color, opp, state, feedback)
        else:
            return self._choose_movement(board, color, opp, state, feedback)

    # ---------- Helper Functions ----------

    def _opponent(self, color: str) -> str:
        return 'B' if color == 'W' else 'W'

    def _is_captured(self, spot: int, board: list) -> bool:
        piece = board[spot]
        if piece == '':
            return False
        empty = 0
        friendly = 0
        enemy = 0
        for nb in ADJACENCY[spot]:
            if board[nb] == '':
                empty += 1
            elif board[nb] == piece:
                friendly += 1
            else:
                enemy += 1
        if empty > 0:
            return False
        return enemy > friendly

    def _simulate_move(self, board: list, move, color: str, phase: str):
        new_board = board.copy()
        if phase == "placement":
            pos = move
            new_board[pos] = color
            active = pos
        else:
            src, dst = move
            new_board[src] = ''
            new_board[dst] = color
            active = dst

        # Step 1: suicide check
        if self._is_captured(active, new_board):
            new_board[active] = ''
            return new_board, True  # suicide

        # Step 2a: remove friendly pieces first (simultaneous)
        to_remove = [i for i, p in enumerate(new_board)
                     if p == color and self._is_captured(i, new_board)]
        for i in to_remove:
            new_board[i] = ''

        # Step 2b: remove enemy pieces after friendly removals
        opp = self._opponent(color)
        to_remove = [i for i, p in enumerate(new_board)
                     if p == opp and self._is_captured(i, new_board)]
        for i in to_remove:
            new_board[i] = ''

        return new_board, False

    def _count_legal_moves(self, board: list, color: str) -> int:
        count = 0
        for i, p in enumerate(board):
            if p != color:
                continue
            for nb in ADJACENCY[i]:
                if board[nb] == '':
                    count += 1
        return count

    def _evaluate_board(self, board: list, color: str, phase: str) -> float:
        opp = self._opponent(color)
        my_count = board.count(color)
        opp_count = board.count(opp)

        score = (my_count - opp_count) * 100

        # Positional evaluation
        pos_score = 0
        for i, p in enumerate(board):
            if p == color:
                pos_score += self.pos_values[i]
            elif p == opp:
                pos_score -= self.pos_values[i]
        score += pos_score * 5

        # Liberty (escape routes)
        lib_score = 0
        for i, p in enumerate(board):
            if p == '':
                continue
            empties = sum(1 for nb in ADJACENCY[i] if board[nb] == '')
            if p == color:
                lib_score += empties
            else:
                lib_score -= empties
        score += lib_score

        # Mobility in movement phase
        if phase == "movement":
            my_mob = self._count_legal_moves(board, color)
            opp_mob = self._count_legal_moves(board, opp)
            score += (my_mob - opp_mob) * 2
            if opp_mob == 0:
                score += 10000  # winning by mate
            if my_mob == 0:
                score -= 10000

        # Direct win/loss
        if opp_count == 0:
            score += 10000
        if my_count == 0:
            score -= 10000

        return score

    def _repetition_adjustment(self, state: dict, board_after: list, color: str, opp: str) -> float:
        history = state.get("history", [])
        if not history:
            return 0
        key = (tuple(board_after), opp)
        count = sum(1 for h in history if h == key)
        if count >= 2:
            my_count = board_after.count(color)
            opp_count = board_after.count(opp)
            if my_count > opp_count:
                return -5000  # avoid draw when ahead
            elif my_count < opp_count:
                return 5000   # take draw when behind
            else:
                return -1000
        return 0

    # ---------- Move Selection ----------

    def _choose_placement(self, board, color, opp, state, feedback):
        legal = [i for i in range(24) if board[i] == '']
        if feedback:
            attempted = feedback.get("attempted_move")
            if isinstance(attempted, int) and attempted in legal:
                legal.remove(attempted)
        if not legal:
            return 0

        best_score = float('-inf')
        best_moves = []

        for move in legal:
            new_board, suicide = self._simulate_move(board, move, color, "placement")
            score = self._evaluate_board(new_board, color, "placement")
            if suicide:
                score -= 500  # heavy penalty for suicide
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return self.rng.choice(best_moves) if best_moves else self.rng.choice(legal)

    def _choose_movement(self, board, color, opp, state, feedback):
        legal_moves = []
        for i, p in enumerate(board):
            if p != color:
                continue
            for nb in ADJACENCY[i]:
                if board[nb] == '':
                    legal_moves.append((i, nb))

        if feedback:
            attempted = feedback.get("attempted_move")
            if isinstance(attempted, tuple) and attempted in legal_moves:
                legal_moves.remove(attempted)

        if not legal_moves:
            return (0, 1)

        best_score = float('-inf')
        best_moves = []

        for move in legal_moves:
            new_board, suicide = self._simulate_move(board, move, color, "movement")
            score = self._evaluate_board(new_board, color, "movement")
            if suicide:
                score -= 500
            score += self._repetition_adjustment(state, new_board, color, opp)

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return self.rng.choice(best_moves) if best_moves else self.rng.choice(legal_moves)
