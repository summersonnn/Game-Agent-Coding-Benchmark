"""
Agent Code: A8-SurroundMorris
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-10 22:38:58
"""



class SurroundMorrisAgent:
    """
    A heuristic Surround Morris agent.
    - Avoids immediate suicide when possible.
    - Simulates captures exactly according to the "Suicide First, Self-Harm Priority" rules.
    - During placement it prefers central/high-degree spots and moves that net more opponent captures than friendly losses.
    - During movement it simulates each legal slide, avoids repetition (3-fold) if possible, prefers moves that capture or mate the opponent,
      and penalizes moves that cause friendly losses or immediate suicide.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    # --- Helper / simulation routines ---
    def _opponent(self, color: str) -> str:
        return 'W' if color == 'B' else 'B'

    def _is_captured(self, board: list, spot: int) -> bool:
        piece = board[spot]
        if not piece:
            return False
        neighbors = ADJACENCY[spot]
        empty_neighbors = 0
        friendly_neighbors = 0
        opponent_neighbors = 0
        for n in neighbors:
            if board[n] == '':
                empty_neighbors += 1
            elif board[n] == piece:
                friendly_neighbors += 1
            else:
                opponent_neighbors += 1
        return (empty_neighbors == 0) and (opponent_neighbors > friendly_neighbors)

    def _apply_captures(self, board: list, active_spot: int, color: str, pieces_on_board: dict):
        """
        Mutates board and pieces_on_board in-place according to capture rules.
        Returns True if the active piece died in the suicide-first check, False otherwise.
        """
        opp = self._opponent(color)

        # Step 1: Active piece suicide check
        if board[active_spot] and self._is_captured(board, active_spot):
            # Active piece removed immediately; turn ends.
            board[active_spot] = ''
            pieces_on_board[color] = max(0, pieces_on_board.get(color, 0) - 1)
            return True

        # Step 2a: Remove all friendly overwhelmed pieces simultaneously
        friendly_to_remove = [i for i in range(24) if board[i] == color and self._is_captured(board, i)]
        for i in friendly_to_remove:
            board[i] = ''
        pieces_on_board[color] = max(0, pieces_on_board.get(color, 0) - len(friendly_to_remove))

        # Step 2b: Re-check all enemy pieces and remove those overwhelmed now
        enemy_to_remove = [j for j in range(24) if board[j] == opp and self._is_captured(board, j)]
        for j in enemy_to_remove:
            board[j] = ''
        pieces_on_board[opp] = max(0, pieces_on_board.get(opp, 0) - len(enemy_to_remove))

        return False

    def _simulate_place(self, board: list, color: str, spot: int,
                        pieces_in_hand: dict, pieces_on_board: dict):
        """
        Returns (new_board, new_pieces_on_board, new_pieces_in_hand, active_died)
        Does not mutate the original board or dicts.
        """
        b = list(board)
        p_hand = dict(pieces_in_hand)
        p_board = dict(pieces_on_board)

        # Place piece
        b[spot] = color
        p_hand[color] = max(0, p_hand.get(color, 0) - 1)
        p_board[color] = p_board.get(color, 0) + 1

        active_died = self._apply_captures(b, spot, color, p_board)
        return b, p_board, p_hand, active_died

    def _simulate_move(self, board: list, color: str, from_spot: int, to_spot: int,
                       pieces_on_board: dict):
        """
        Returns (new_board, new_pieces_on_board, active_died)
        Does not mutate original board or dict.
        """
        b = list(board)
        p_board = dict(pieces_on_board)

        # Slide
        b[to_spot] = color
        b[from_spot] = ''

        active_died = self._apply_captures(b, to_spot, color, p_board)
        return b, p_board, active_died

    def _opponent_has_moves(self, board: list, opp_color: str) -> bool:
        for s in range(24):
            if board[s] != opp_color:
                continue
            for n in ADJACENCY[s]:
                if board[n] == '':
                    return True
        return False

    # --- Main interface ---
    def make_move(self, state: dict, feedback: dict | None = None):
        board = list(state["board"])
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = dict(state["pieces_in_hand"])
        pieces_on_board = dict(state["pieces_on_board"])
        history = list(state.get("history", []))

        # PLACEMENT PHASE
        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0  # fallback

            best_score = -10**9
            best_spots = []

            for spot in empty_spots:
                new_board, new_p_on_board, new_p_hand, active_died = self._simulate_place(
                    board, color, spot, pieces_in_hand, pieces_on_board
                )

                # Immediate elimination check (placement): opponent has no pieces on board AND no pieces in hand
                if new_p_on_board.get(opp, 0) == 0 and new_p_hand.get(opp, 0) == 0:
                    return spot

                captured_opp = pieces_on_board.get(opp, 0) - new_p_on_board.get(opp, 0)
                lost_self = pieces_on_board.get(color, 0) - new_p_on_board.get(color, 0)
                deg = len(ADJACENCY[spot])
                friendly_after = sum(1 for n in ADJACENCY[spot] if new_board[n] == color)
                opp_after = sum(1 for n in ADJACENCY[spot] if new_board[n] == opp)

                # Heuristic scoring
                score = 0
                score += captured_opp * 800
                score -= lost_self * 1000
                score += deg * 6
                score += friendly_after * 4
                score -= opp_after * 2
                if active_died:
                    score -= 700  # strongly avoid immediate suicide
                # slight randomness to diversify equivalent choices
                score += random.random() * 1e-3

                if score > best_score:
                    best_score = score
                    best_spots = [spot]
                elif abs(score - best_score) < 1e-9:
                    best_spots.append(spot)

            return random.choice(best_spots)

        # MOVEMENT PHASE
        else:
            # legal moves: slide one of your pieces to adjacent empty spot
            moves = []
            for s in range(24):
                if board[s] != color:
                    continue
                for n in ADJACENCY[s]:
                    if board[n] == '':
                        moves.append((s, n))

            if not moves:
                # no legal moves — return something (engine will handle mate)
                return (0, 1)

            best_score = -10**9
            best_moves = []

            for (frm, to) in moves:
                new_board, new_p_on_board, active_died = self._simulate_move(
                    board, color, frm, to, pieces_on_board
                )

                # Immediate elimination win (movement): opponent has 0 pieces on board
                if new_p_on_board.get(opp, 0) == 0:
                    return (frm, to)

                # Immediate mate check: does opponent have any legal moves after this move?
                opp_has_moves = self._opponent_has_moves(new_board, opp)
                if not opp_has_moves:
                    # mate -> immediate best
                    return (frm, to)

                captured_opp = pieces_on_board.get(opp, 0) - new_p_on_board.get(opp, 0)
                lost_self = pieces_on_board.get(color, 0) - new_p_on_board.get(color, 0)

                # mobility for our side after move (count of pieces that can move)
                our_movable_count = 0
                for s in range(24):
                    if new_board[s] != color:
                        continue
                    for n in ADJACENCY[s]:
                        if new_board[n] == '':
                            our_movable_count += 1
                            break

                # repetition avoidance: avoid moves that would create a 3rd occurrence of (board, next_player)
                future_state = (tuple(new_board), opp)
                repeat_count = sum(1 for h in history if h == future_state)
                repeat_penalty = 0
                if repeat_count >= 2:
                    # making this move would cause immediate draw by 3-fold repetition -> avoid if possible
                    repeat_penalty = 100000

                # Heuristic score
                score = 0
                score += captured_opp * 1500
                score -= lost_self * 1200
                score += our_movable_count * 8
                score += len(ADJACENCY[to]) * 6  # prefer moving to higher-degree spots
                if active_died:
                    score -= 2000  # penalize moves where your active piece dies immediately
                score -= repeat_penalty
                # small random tie-break
                score += random.random() * 1e-3

                if score > best_score:
                    best_score = score
                    best_moves = [(frm, to)]
                elif abs(score - best_score) < 1e-9:
                    best_moves.append((frm, to))

            return random.choice(best_moves)
