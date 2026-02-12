"""
Agent Code: A8-SurroundMorris
Model: xiaomi/mimo-v2-flash
Run: 1
Generated: 2026-02-10 22:38:58
"""



import random

class SurroundMorrisAgent:
    """
    Agent for Surround Morris that uses a heuristic evaluation of moves.
    - Placement phase: Prefers central spots and avoids immediate suicide.
    - Movement phase: Evaluates moves based on net piece capture and positional safety.
    - Considers repetition draws when ahead.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = state["pieces_in_hand"]
        pieces_on_board = state["pieces_on_board"]
        history = state["history"]
        
        # Adjacency graph (global variable provided by the game engine)
        ADJACENCY = {
            0: [1, 9], 1: [0, 2, 4], 2: [1, 14],
            3: [4, 10], 4: [1, 3, 5, 7], 5: [4, 13],
            6: [7, 11], 7: [4, 6, 8], 8: [7, 12],
            9: [0, 10, 21], 10: [3, 9, 11, 18], 11: [6, 10, 15],
            12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
            15: [11, 16], 16: [15, 17, 19], 17: [12, 16],
            18: [10, 19], 19: [16, 18, 20, 22], 20: [13, 19],
            21: [9, 22], 22: [19, 21, 23], 23: [14, 22]
        }

        def is_captured(board, spot, piece_color):
            """Check if a piece at `spot` of `piece_color` is captured."""
            if board[spot] != piece_color:
                return False
            opp_color = 'B' if piece_color == 'W' else 'W'
            neighbors = ADJACENCY[spot]
            empty = 0
            friendly = 0
            opponent = 0
            for n in neighbors:
                if board[n] == '':
                    empty += 1
                elif board[n] == piece_color:
                    friendly += 1
                elif board[n] == opp_color:
                    opponent += 1
            return (empty == 0) and (opponent > friendly)

        def simulate_capture(board, mover_color):
            """Simulate the capture process after a move, returning the final board."""
            opp_color = 'B' if mover_color == 'W' else 'W'
            new_board = board[:]
            # Step 1: Check active piece (if any) - handled outside this function
            # Step 2a: Remove overwhelmed friendlies iteratively
            changed = True
            while changed:
                changed = False
                to_remove = []
                for i in range(24):
                    if new_board[i] == mover_color and is_captured(new_board, i, mover_color):
                        to_remove.append(i)
                        changed = True
                for i in to_remove:
                    new_board[i] = ''
            # Step 2b: Remove overwhelmed enemies iteratively
            changed = True
            while changed:
                changed = False
                to_remove = []
                for i in range(24):
                    if new_board[i] == opp_color and is_captured(new_board, i, opp_color):
                        to_remove.append(i)
                        changed = True
                for i in to_remove:
                    new_board[i] = ''
            return new_board

        def evaluate_move(new_board, mover_color, opp_color, pieces_on_board_before, pieces_in_hand_before, is_placement):
            """Evaluate the move based on piece capture and win/loss conditions."""
            # Count pieces after move and captures
            our_pieces_after = sum(1 for x in new_board if x == mover_color)
            opp_pieces_after = sum(1 for x in new_board if x == opp_color)
            
            # Check win/loss conditions
            if is_placement:
                our_hand_after = pieces_in_hand_before[mover_color] - 1
                if our_pieces_after == 0 and our_hand_after == 0:
                    return -1000  # We lose
                opp_hand_after = pieces_in_hand_before[opp_color]
                if opp_pieces_after == 0 and opp_hand_after == 0:
                    return 1000   # We win
            else:  # movement phase
                if opp_pieces_after == 0:
                    return 1000   # We win
                if our_pieces_after == 0:
                    return -1000  # We lose
            
            # Calculate net capture
            enemy_captured = pieces_on_board_before[opp_color] - opp_pieces_after
            if is_placement:
                our_captured = (pieces_on_board_before[mover_color] + 1) - our_pieces_after
            else:
                our_captured = pieces_on_board_before[mover_color] - our_pieces_after
            net_capture = enemy_captured - our_captured
            
            # Positional bonus for central spots (only in placement)
            positional_bonus = 0
            if is_placement and isinstance(move, int):
                central_spots = [4, 10, 13, 19]
                if move in central_spots:
                    positional_bonus = 0.1
            
            # Check for repetition draw risk
            repetition_penalty = 0
            next_player = opp_color
            new_state = (tuple(new_board), next_player)
            if new_state in history:
                count = history.count(new_state)
                if count >= 2:  # This move would cause 3-fold repetition
                    if net_capture + positional_bonus > 0:  # We are winning
                        repetition_penalty = -10  # Avoid draw
                    else:
                        repetition_penalty = 5   # Prefer draw if losing
            
            return net_capture + positional_bonus + repetition_penalty

        # Placement Phase
        if phase == "placement":
            empty_spots = [i for i in range(24) if board[i] == '']
            if not empty_spots:
                return 0  # Fallback
            
            best_score = float('-inf')
            best_move = empty_spots[0]
            
            for spot in empty_spots:
                # Simulate placement
                new_board = board[:]
                new_board[spot] = color
                # Check active piece capture
                if is_captured(new_board, spot, color):
                    # Active piece dies immediately -> no capture
                    our_pieces_after = pieces_on_board[color]  # Piece is placed then removed
                    opp_pieces_after = pieces_on_board[opp]
                    # Check loss condition
                    our_hand_after = pieces_in_hand[color] - 1
                    if our_pieces_after == 0 and our_hand_after == 0:
                        score = -1000
                    else:
                        score = -1  # Bad move: loses a piece without capturing
                else:
                    # Active piece survives, do sweep
                    new_board = simulate_capture(new_board, color)
                    score = evaluate_move(new_board, color, opp, pieces_on_board, pieces_in_hand, True)
                
                if score > best_score:
                    best_score = score
                    best_move = spot
            
            return best_move

        # Movement Phase
        else:
            # Generate all legal moves
            moves = []
            for from_spot in range(24):
                if board[from_spot] != color:
                    continue
                for to_spot in ADJACENCY[from_spot]:
                    if board[to_spot] == '':
                        moves.append((from_spot, to_spot))
            
            if not moves:
                # Should not happen as the engine handles mate, but return a dummy move
                return (0, 1)
            
            best_score = float('-inf')
            best_move = moves[0]
            
            for move in moves:
                from_spot, to_spot = move
                # Simulate movement
                new_board = board[:]
                new_board[from_spot] = ''
                new_board[to_spot] = color
                # Check active piece capture
                if is_captured(new_board, to_spot, color):
                    # Active piece dies immediately
                    new_board[to_spot] = ''  # Remove it
                    # Then no sweep (since active piece died)
                    our_pieces_after = sum(1 for x in new_board if x == color)
                    opp_pieces_after = sum(1 for x in new_board if x == opp)
                    if opp_pieces_after == 0:
                        score = 1000
                    elif our_pieces_after == 0:
                        score = -1000
                    else:
                        enemy_captured = pieces_on_board[opp] - opp_pieces_after
                        our_captured = pieces_on_board[color] - our_pieces_after
                        score = enemy_captured - our_captured
                else:
                    # Active piece survives, do sweep
                    new_board = simulate_capture(new_board, color)
                    score = evaluate_move(new_board, color, opp, pieces_on_board, pieces_in_hand, False)
                
                if score > best_score:
                    best_score = score
                    best_move = move
            
            return best_move
