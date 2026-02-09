"""
Agent Code: A8-SurroundMorris
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-09 19:17:14
"""



import random

class SurroundMorrisAgent:
    """
    Your agent for Surround Morris.
    """
    def __init__(self, name: str, color: str):
        """
        Initialize your agent.

        Parameters:
        -----------
        name : str
            Your agent name (e.g., "Agent-1").
        color : str
            Your piece color: 'B' (Black) or 'W' (White).
        """
        self.name = name
        self.color = color

    def opposite(self, color):
        return 'B' if color == 'W' else 'W'

    def is_overwhelmed(self, board, spot, color):
        empty = 0
        opp = 0
        friendly = 0
        for neighbor in ADJACENCY[spot]:
            if board[neighbor] == '':
                empty += 1
            elif board[neighbor] == color:
                friendly += 1
            else:
                opp += 1
        return empty == 0 and opp > friendly

    def apply_captures(self, board, active_spot, active_color):
        new_board = board.copy()
        # Step 1: Active piece suicide check
        if self.is_overwhelmed(new_board, active_spot, active_color):
            new_board[active_spot] = ''
            return new_board

        # Step 2a: Remove overwhelmed friendly pieces
        to_remove_friendly = []
        for spot in range(24):
            if new_board[spot] == active_color:
                if self.is_overwhelmed(new_board, spot, active_color):
                    to_remove_friendly.append(spot)
        for spot in to_remove_friendly:
            new_board[spot] = ''

        # Step 2b: Remove overwhelmed enemy pieces (re-checked after friendly removals)
        to_remove_enemy = []
        for spot in range(24):
            if new_board[spot] == self.opposite(active_color):
                if self.is_overwhelmed(new_board, spot, self.opposite(active_color)):
                    to_remove_enemy.append(spot)
        for spot in to_remove_enemy:
            new_board[spot] = ''

        return new_board

    def get_legal_movements(self, board, color):
        moves = []
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        moves.append((spot, neighbor))
        return moves

    def evaluate(self, board, pieces_in_hand, color, opp, phase, history):
        our_on_board = board.count(color)
        opp_on_board = board.count(opp)

        if phase == 'placement':
            our_remaining = our_on_board + pieces_in_hand[color]
            opp_remaining = opp_on_board + pieces_in_hand[opp]
        else:
            our_remaining = our_on_board
            opp_remaining = opp_on_board

        # Immediate win/loss conditions
        if opp_remaining == 0:
            return 1000000
        if our_remaining == 0:
            return -1000000

        our_danger = 0
        opp_danger = 0
        for spot in range(24):
            if board[spot] == color:
                if self.is_overwhelmed(board, spot, color):
                    our_danger += 1
            elif board[spot] == opp:
                if self.is_overwhelmed(board, spot, opp):
                    opp_danger += 1

        score = (our_remaining - opp_remaining) * 1000 - our_danger * 100 + opp_danger * 100

        if phase == 'movement':
            opp_mobility = len(self.get_legal_movements(board, opp))
            our_mobility = len(self.get_legal_movements(board, color))
            score += (opp_mobility == 0) * 10000  # Immediate win if opponent has no moves
            score -= (our_mobility == 0) * 10000   # Severe penalty if we have no moves

        # Avoid 3-fold repetition (penalize positions already seen)
        if (tuple(board), opp) in history:
            score -= 5000

        return score

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Called each turn. Return your move based on the current game state.

        Parameters:
        -----------
        state : dict
            {
                "board": list[str],
                "phase": str,
                "your_color": str,
                "opponent_color": str,
                "pieces_in_hand": dict,
                "pieces_on_board": dict,
                "move_count": int,
                "history": list[tuple],
            }

        feedback : dict or None
            None on first attempt. On retries after an invalid move:
            {
                "error_code": str,
                "error_message": str,
                "attempted_move": ...,
                "attempt_number": int,
            }

        Returns:
        --------
        During placement phase:
            int - the spot number (0-23) to place your piece

        During movement phase:
            tuple[int, int] - (from_spot, to_spot) to slide your piece
        """
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        history = state["history"]

        if phase == "placement":
            # Only consider placements if we have pieces in hand
            if pieces_in_hand[color] == 0:
                # Should not happen, but fallback: return any empty spot
                empty = [i for i in range(24) if board[i] == '']
                return random.choice(empty) if empty else 0

            empty_spots = [i for i in range(24) if board[i] == '']
            best_score = -float('inf')
            best_spot = None
            for spot in empty_spots:
                # Simulate placement
                new_board = board.copy()
                new_board[spot] = color
                new_board = self.apply_captures(new_board, spot, color)
                new_pieces_in_hand = pieces_in_hand.copy()
                new_pieces_in_hand[color] -= 1
                score = self.evaluate(new_board, new_pieces_in_hand, color, opp, phase, history)
                if score > best_score:
                    best_score = score
                    best_spot = spot
            return best_spot
        else:  # movement phase
            moves = self.get_legal_movements(board, color)
            if not moves:
                # Should not happen (engine should detect mate), but fallback
                return (0, 1)

            best_score = -float('inf')
            best_move = None
            for move in moves:
                from_spot, to_spot = move
                new_board = board.copy()
                new_board[from_spot] = ''
                new_board[to_spot] = color
                new_board = self.apply_captures(new_board, to_spot, color)
                new_pieces_in_hand = pieces_in_hand.copy()  # No change in movement phase
                score = self.evaluate(new_board, new_pieces_in_hand, color, opp, phase, history)
                if score > best_score:
                    best_score = score
                    best_move = move
            return best_move
