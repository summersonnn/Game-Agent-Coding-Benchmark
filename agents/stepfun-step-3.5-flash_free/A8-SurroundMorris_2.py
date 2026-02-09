"""
Agent Code: A8-SurroundMorris
Model: stepfun/step-3.5-flash:free
Run: 2
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

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Called each turn. Return your move based on the current game state.

        Parameters:
        -----------
        state : dict
            {
                "board": list[str],
                    # 24-element list. Each element is '', 'B', or 'W'.
                    # Index corresponds to spot number on the board.
                "phase": str,
                    # 'placement' or 'movement'
                "your_color": str,
                    # Your color: 'B' or 'W'
                "opponent_color": str,
                    # Opponent's color
                "pieces_in_hand": dict,
                    # {'B': int, 'W': int} - pieces not yet placed
                "pieces_on_board": dict,
                    # {'B': int, 'W': int} - pieces currently on the board
                "move_count": int,
                    # Number of movement turns elapsed (0 during placement)
                "history": list[tuple],
                    # List of (board_tuple, current_player) states seen so far.
                    # Use this to detect and avoid 3-fold repetition.
                    # Reset when transitioning from placement to movement phase.
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

        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            candidate_moves = []
            for spot in empty_spots:
                board_after = board.copy()
                board_after[spot] = color
                new_board, our_losses, enemy_losses = self.simulate_captures(board_after, spot, color)
                our_pieces_after = state["pieces_on_board"][color] + 1 - our_losses
                opp_pieces_after = state["pieces_on_board"][opp] - enemy_losses
                our_hand_after = state["pieces_in_hand"][color] - 1
                opp_hand_after = state["pieces_in_hand"][opp]

                if opp_pieces_after == 0 and opp_hand_after == 0:
                    score = 1000 + our_pieces_after  # win
                elif our_pieces_after == 0 and our_hand_after == 0:
                    score = -1000  # loss
                else:
                    score = enemy_losses - our_losses

                candidate_moves.append((score, spot))

            candidate_moves.sort(key=lambda x: x[0], reverse=True)
            max_score = candidate_moves[0][0]
            best_moves = [spot for score, spot in candidate_moves if score == max_score]
            return random.choice(best_moves)

        else:  # movement
            moves = []
            for from_spot in range(24):
                if board[from_spot] != color:
                    continue
                for to_spot in ADJACENCY[from_spot]:
                    if board[to_spot] == '':
                        moves.append((from_spot, to_spot))

            if not moves:
                return (0, 1)  # should not happen, but return something

            winning_moves = []
            losing_moves = []
            draw_moves = []
            non_draw_moves = []

            our_pieces = state["pieces_on_board"][color]
            opp_pieces = state["pieces_on_board"][opp]
            history = state["history"]

            for (from_spot, to_spot) in moves:
                board_after_move = board.copy()
                board_after_move[from_spot] = ''
                board_after_move[to_spot] = color
                new_board, our_losses, enemy_losses = self.simulate_captures(board_after_move, to_spot, color)

                our_pieces_after = our_pieces - our_losses
                opp_pieces_after = opp_pieces - enemy_losses

                if opp_pieces_after == 0:
                    winning_moves.append(((from_spot, to_spot), 1000 + our_pieces_after))
                elif our_pieces_after == 0:
                    losing_moves.append(((from_spot, to_spot), -1000))
                else:
                    board_tuple = tuple(new_board)
                    count = 0
                    for (hist_board, hist_player) in history:
                        if hist_board == board_tuple and hist_player == opp:
                            count += 1
                    if count >= 2:
                        score = - (our_losses + enemy_losses)
                        draw_moves.append(((from_spot, to_spot), score))
                    else:
                        score = enemy_losses - our_losses
                        non_draw_moves.append(((from_spot, to_spot), score))

            if winning_moves:
                winning_moves.sort(key=lambda x: x[1], reverse=True)
                max_score = winning_moves[0][1]
                best_moves = [move for move, score in winning_moves if score == max_score]
                return random.choice(best_moves)
            elif losing_moves:
                return random.choice([move for move, score in losing_moves])
            else:
                if our_pieces > opp_pieces:
                    if non_draw_moves:
                        candidate_moves = non_draw_moves
                    else:
                        candidate_moves = draw_moves
                elif our_pieces < opp_pieces:
                    if draw_moves:
                        candidate_moves = draw_moves
                    else:
                        candidate_moves = non_draw_moves
                else:
                    if non_draw_moves:
                        candidate_moves = non_draw_moves
                    else:
                        candidate_moves = draw_moves

                if not candidate_moves:
                    candidate_moves = draw_moves + non_draw_moves

                if not candidate_moves:
                    return random.choice(moves)

                candidate_moves.sort(key=lambda x: x[1], reverse=True)
                max_score = candidate_moves[0][1]
                best_moves = [move for move, score in candidate_moves if score == max_score]
                return random.choice(best_moves)

    @staticmethod
    def check_capture(spot, board):
        piece_color = board[spot]
        if piece_color == '':
            return False
        opponent_color = 'B' if piece_color == 'W' else 'W'
        empty = 0
        opponent = 0
        friendly = 0
        for neighbor in ADJACENCY[spot]:
            neighbor_color = board[neighbor]
            if neighbor_color == '':
                empty += 1
            elif neighbor_color == piece_color:
                friendly += 1
            else:
                opponent += 1
        return (empty == 0) and (opponent > friendly)

    @staticmethod
    def simulate_captures(board, active_spot, mover_color):
        opp_color = 'B' if mover_color == 'W' else 'W'

        if SurroundMorrisAgent.check_capture(active_spot, board):
            new_board = board.copy()
            new_board[active_spot] = ''
            return new_board, 1, 0

        new_board = board.copy()
        our_overwhelmed = []
        for spot in range(24):
            if new_board[spot] == mover_color:
                if SurroundMorrisAgent.check_capture(spot, new_board):
                    our_overwhelmed.append(spot)
        for spot in our_overwhelmed:
            new_board[spot] = ''
        our_losses = len(our_overwhelmed)

        enemy_overwhelmed = []
        for spot in range(24):
            if new_board[spot] == opp_color:
                if SurroundMorrisAgent.check_capture(spot, new_board):
                    enemy_overwhelmed.append(spot)
        for spot in enemy_overwhelmed:
            new_board[spot] = ''
        enemy_losses = len(enemy_overwhelmed)

        return new_board, our_losses, enemy_losses
