"""
Agent Code: A8-SurroundMorris
Model: anthropic/claude-opus-4.6
Run: 2
Generated: 2026-02-09 21:28:26
"""

import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        history = state.get("history", [])

        if phase == "placement":
            return self._placement_move(board, color, opp, state)
        else:
            return self._movement_move(board, color, opp, state, history)

    def _get_neighbors(self, spot):
        return ADJACENCY[spot]

    def _is_captured(self, spot, board):
        piece = board[spot]
        if piece == '':
            return False
        opp = 'W' if piece == 'B' else 'B'
        empty = 0
        friendly = 0
        opponent = 0
        for n in ADJACENCY[spot]:
            if board[n] == '':
                empty += 1
            elif board[n] == piece:
                friendly += 1
            else:
                opponent += 1
        return empty == 0 and opponent > friendly

    def _simulate_move_placement(self, board, spot, color):
        opp = 'W' if color == 'B' else 'B'
        b = list(board)
        b[spot] = color

        # Step 1: suicide check
        if self._is_captured(spot, b):
            b[spot] = ''
            return b, -1, 0  # lost own piece, captured 0

        # Step 2a: remove friendly pieces that are captured
        friendly_lost = 0
        for i in range(24):
            if i != spot and b[i] == color and self._is_captured(i, b):
                b[i] = ''
                friendly_lost += 1

        # Step 2b: remove enemy pieces that are captured (re-check after friendly removal)
        enemy_lost = 0
        for i in range(24):
            if b[i] == opp and self._is_captured(i, b):
                b[i] = ''
                enemy_lost += 1

        return b, friendly_lost, enemy_lost

    def _simulate_move_movement(self, board, frm, to, color):
        opp = 'W' if color == 'B' else 'B'
        b = list(board)
        b[frm] = ''
        b[to] = color

        if self._is_captured(to, b):
            b[to] = ''
            return b, -1, 0

        friendly_lost = 0
        for i in range(24):
            if i != to and b[i] == color and self._is_captured(i, b):
                b[i] = ''
                friendly_lost += 1

        enemy_lost = 0
        for i in range(24):
            if b[i] == opp and self._is_captured(i, b):
                b[i] = ''
                enemy_lost += 1

        return b, friendly_lost, enemy_lost

    def _get_legal_moves(self, board, color):
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for n in ADJACENCY[spot]:
                if board[n] == '':
                    moves.append((spot, n))
        return moves

    def _count_pieces(self, board, color):
        return sum(1 for s in board if s == color)

    def _evaluate(self, board, color, opp):
        my_pieces = self._count_pieces(board, color)
        opp_pieces = self._count_pieces(board, opp)

        if my_pieces == 0:
            return -10000
        if opp_pieces == 0:
            return 10000

        my_moves = len(self._get_legal_moves(board, color))
        opp_moves = len(self._get_legal_moves(board, opp))

        if my_moves == 0 and my_pieces > 0:
            return -10000
        if opp_moves == 0 and opp_pieces > 0:
            return 10000

        score = (my_pieces - opp_pieces) * 100
        score += (my_moves - opp_moves) * 5

        # Positional value
        pos_values = {}
        for i in range(24):
            pos_values[i] = len(ADJACENCY[i])  # crossroads=4, T=3, corner=2

        for i in range(24):
            if board[i] == color:
                score += pos_values[i] * 3
                # Empty neighbor bonus (safety)
                empty_n = sum(1 for n in ADJACENCY[i] if board[n] == '')
                score += empty_n * 4
                # Vulnerability penalty
                if empty_n == 0:
                    opp_n = sum(1 for n in ADJACENCY[i] if board[n] == opp)
                    fri_n = sum(1 for n in ADJACENCY[i] if board[n] == color)
                    if opp_n > fri_n:
                        score -= 80
            elif board[i] == opp:
                score -= pos_values[i] * 3
                empty_n = sum(1 for n in ADJACENCY[i] if board[n] == '')
                score -= empty_n * 4
                if empty_n == 0:
                    opp_n = sum(1 for n in ADJACENCY[i] if board[n] == color)
                    fri_n = sum(1 for n in ADJACENCY[i] if board[n] == opp)
                    if opp_n > fri_n:
                        score += 80

        return score

    def _minimax(self, board, color, opp, depth, alpha, beta, maximizing, root_color):
        if depth == 0:
            return self._evaluate(board, root_color, 'W' if root_color == 'B' else 'B'), None

        current = color if maximizing else opp
        other = opp if maximizing else color
        moves = self._get_legal_moves(board, current)

        my_count = self._count_pieces(board, current)
        other_count = self._count_pieces(board, other)

        if my_count == 0:
            val = -10000 if maximizing else 10000
            return val, None
        if other_count == 0:
            val = 10000 if maximizing else -10000
            return val, None
        if not moves:
            val = -10000 if maximizing else 10000
            return val, None

        best_move = None
        if maximizing:
            max_eval = -float('inf')
            for frm, to in moves:
                new_board, fl, el = self._simulate_move_movement(board, frm, to, current)
                eval_score, _ = self._minimax(new_board, color, opp, depth - 1, alpha, beta, False, root_color)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (frm, to)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for frm, to in moves:
                new_board, fl, el = self._simulate_move_movement(board, frm, to, current)
                eval_score, _ = self._minimax(new_board, color, opp, depth - 1, alpha, beta, True, root_color)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (frm, to)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def _placement_move(self, board, color, opp, state):
        empty = [i for i in range(24) if board[i] == '']
        if not empty:
            return 0

        best_score = -float('inf')
        best_spots = []

        for spot in empty:
            new_board, fl, el = self._simulate_move_placement(board, spot, color)

            if fl == -1:  # suicide
                score = -500
            else:
                score = el * 150 - fl * 200
                score += self._evaluate(new_board, color, opp) * 0.5

            if score > best_score:
                best_score = score
                best_spots = [spot]
            elif score == best_score:
                best_spots.append(spot)

        return random.choice(best_spots)

    def _would_repeat(self, board, color, history):
        board_tuple = tuple(board)
        count = sum(1 for h in history if h[0] == board_tuple and h[1] == color)
        return count >= 2

    def _movement_move(self, board, color, opp, state, history):
        moves = self._get_legal_moves(board, color)
        if not moves:
            return (0, 1)

        # Adaptive depth based on number of moves
        total_moves = len(moves) + len(self._get_legal_moves(board, opp))
        if total_moves <= 10:
            depth = 5
        elif total_moves <= 20:
            depth = 4
        elif total_moves <= 40:
            depth = 3
        else:
            depth = 2

        # Pre-filter: check for immediate captures and avoid suicide
        scored_moves = []
        for frm, to in moves:
            new_board, fl, el = self._simulate_move_movement(board, frm, to, color)

            if fl == -1:  # suicide move
                scored_moves.append(((frm, to), -10000))
                continue

            # Check repetition
            if self._would_repeat(new_board, opp, history):
                my_p = self._count_pieces(new_board, color)
                opp_p = self._count_pieces(new_board, opp)
                if my_p > opp_p:
                    scored_moves.append(((frm, to), -5000))
                    continue

            quick_score = el * 200 - fl * 300
            scored_moves.append(((frm, to), quick_score))

        # Sort by quick score descending for better alpha-beta pruning
        scored_moves.sort(key=lambda x: x[1], reverse=True)

        # Filter out clearly terrible moves for search
        search_moves = [m for m, s in scored_moves if s > -5000]
        if not search_moves:
            search_moves = [m for m, s in scored_moves]

        best_score = -float('inf')
        best_move = search_moves[0]
        alpha = -float('inf')
        beta = float('inf')

        for frm, to in search_moves:
            new_board, fl, el = self._simulate_move_movement(board, frm, to, color)
            eval_score, _ = self._minimax(new_board, color, opp, depth - 1, alpha, beta, False, color)

            # Bonus for captures at root
            eval_score += el * 50

            if eval_score > best_score:
                best_score = eval_score
                best_move = (frm, to)
            alpha = max(alpha, eval_score)

        return best_move