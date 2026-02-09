"""
Agent Code: A8-SurroundMorris
Model: anthropic/claude-opus-4.6
Run: 1
Generated: 2026-02-09 21:28:26
"""

import random

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opp = 'W' if color == 'B' else 'B'

    def make_move(self, state: dict, feedback: dict | None = None):
        board = list(state["board"])
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        pieces_in_hand = dict(state["pieces_in_hand"])
        pieces_on_board = dict(state["pieces_on_board"])
        history = state.get("history", [])

        if phase == "placement":
            return self._placement_move(board, color, opp, pieces_in_hand, pieces_on_board)
        else:
            return self._movement_move(board, color, opp, pieces_on_board, history)

    def _get_legal_moves(self, board, color):
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for nb in ADJACENCY[spot]:
                if board[nb] == '':
                    moves.append((spot, nb))
        return moves

    def _is_captured(self, spot, board):
        piece = board[spot]
        if piece == '':
            return False
        opp = 'W' if piece == 'B' else 'B'
        empty = 0
        friendly = 0
        opponent = 0
        for nb in ADJACENCY[spot]:
            v = board[nb]
            if v == '':
                empty += 1
            elif v == piece:
                friendly += 1
            else:
                opponent += 1
        return empty == 0 and opponent > friendly

    def _apply_captures(self, board, active_spot, active_color):
        opp = 'W' if active_color == 'B' else 'B'
        removed = {'B': 0, 'W': 0}

        if board[active_spot] != '' and self._is_captured(active_spot, board):
            removed[active_color] += 1
            board[active_spot] = ''
            return removed

        friendly_removed = []
        for s in range(24):
            if s == active_spot:
                continue
            if board[s] == active_color and self._is_captured(s, board):
                friendly_removed.append(s)
        for s in friendly_removed:
            board[s] = ''
            removed[active_color] += 1

        enemy_removed = []
        for s in range(24):
            if board[s] == opp and self._is_captured(s, board):
                enemy_removed.append(s)
        for s in enemy_removed:
            board[s] = ''
            removed[opp] += 1

        return removed

    def _simulate_placement(self, board, spot, color):
        b = list(board)
        b[spot] = color
        removed = self._apply_captures(b, spot, color)
        return b, removed

    def _simulate_movement(self, board, frm, to, color):
        b = list(board)
        b[frm] = ''
        b[to] = color
        removed = self._apply_captures(b, to, color)
        return b, removed

    def _evaluate(self, board, my_color, opp_color, my_board, opp_board):
        if my_board <= 0:
            return -10000
        if opp_board <= 0:
            return 10000

        score = (my_board - opp_board) * 100

        my_moves = len(self._get_legal_moves(board, my_color))
        opp_moves = len(self._get_legal_moves(board, opp_color))

        if opp_moves == 0 and opp_board > 0:
            return 10000
        if my_moves == 0 and my_board > 0:
            return -10000

        score += (my_moves - opp_moves) * 10

        crossroads = [4, 10, 13, 19]
        tjunctions = [1, 3, 5, 7, 9, 11, 12, 14, 16, 18, 20, 22]
        for s in crossroads:
            if board[s] == my_color:
                score += 15
            elif board[s] == opp_color:
                score -= 15
        for s in tjunctions:
            if board[s] == my_color:
                score += 5
            elif board[s] == opp_color:
                score -= 5

        for s in range(24):
            if board[s] == opp_color:
                empty_nb = sum(1 for nb in ADJACENCY[s] if board[nb] == '')
                if empty_nb == 1:
                    score += 20
                elif empty_nb == 0:
                    pass

        for s in range(24):
            if board[s] == my_color:
                empty_nb = sum(1 for nb in ADJACENCY[s] if board[nb] == '')
                if empty_nb == 0:
                    score -= 15
                elif empty_nb == 1:
                    score -= 5

        return score

    def _placement_move(self, board, color, opp, pieces_in_hand, pieces_on_board):
        empty = [i for i in range(24) if board[i] == '']
        if not empty:
            return 0

        best_score = -float('inf')
        best_spots = []

        for spot in empty:
            b, removed = self._simulate_placement(board, spot, color)

            if removed.get(color, 0) > 0 and b[spot] == '':
                score = -5000
            else:
                my_on = pieces_on_board[color] + 1 - removed.get(color, 0)
                opp_on = pieces_on_board[opp] - removed.get(opp, 0)
                score = self._evaluate(b, color, opp, my_on, opp_on)

            if score > best_score:
                best_score = score
                best_spots = [spot]
            elif score == best_score:
                best_spots.append(spot)

        return random.choice(best_spots)

    def _movement_move(self, board, color, opp, pieces_on_board, history):
        moves = self._get_legal_moves(board, color)
        if not moves:
            return (0, 1)

        history_set = {}
        for h in history:
            key = h
            history_set[key] = history_set.get(key, 0) + 1

        depth = 3
        if len(moves) <= 6:
            depth = 4
        if len(moves) <= 3:
            depth = 5

        best_score = -float('inf')
        best_moves = []

        for frm, to in moves:
            b, removed = self._simulate_movement(board, frm, to, color)
            my_on = pieces_on_board[color] - removed.get(color, 0)
            opp_on = pieces_on_board[opp] - removed.get(opp, 0)

            if my_on <= 0:
                score = -10000
            elif opp_on <= 0:
                score = 10000
            else:
                board_key = (tuple(b), opp)
                new_hist = dict(history_set)
                new_hist[board_key] = new_hist.get(board_key, 0) + 1
                if new_hist[board_key] >= 3:
                    score = 0
                else:
                    score = self._minimax(b, opp, color, opp_on, my_on, depth - 1, -float('inf'), float('inf'), False, new_hist)

            if score > best_score:
                best_score = score
                best_moves = [(frm, to)]
            elif score == best_score:
                best_moves.append((frm, to))

        return random.choice(best_moves)

    def _minimax(self, board, current, other, cur_on, oth_on, depth, alpha, beta, maximizing, hist):
        if cur_on <= 0:
            return 10000 if not maximizing else -10000
        if oth_on <= 0:
            return -10000 if not maximizing else 10000

        moves = self._get_legal_moves(board, current)
        if not moves:
            return -10000 if maximizing else 10000

        if depth <= 0:
            if maximizing:
                return self._evaluate(board, current, other, cur_on, oth_on)
            else:
                return self._evaluate(board, other, current, oth_on, cur_on)

        if maximizing:
            max_eval = -float('inf')
            for frm, to in moves:
                b, removed = self._simulate_movement(board, frm, to, current)
                new_cur = cur_on - removed.get(current, 0)
                new_oth = oth_on - removed.get(other, 0)

                if new_cur <= 0:
                    val = -10000
                elif new_oth <= 0:
                    val = 10000
                else:
                    board_key = (tuple(b), other)
                    new_hist = dict(hist)
                    new_hist[board_key] = new_hist.get(board_key, 0) + 1
                    if new_hist[board_key] >= 3:
                        val = 0
                    else:
                        val = self._minimax(b, other, current, new_oth, new_cur, depth - 1, alpha, beta, False, new_hist)

                max_eval = max(max_eval, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for frm, to in moves:
                b, removed = self._simulate_movement(board, frm, to, current)
                new_cur = cur_on - removed.get(current, 0)
                new_oth = oth_on - removed.get(other, 0)

                if new_cur <= 0:
                    val = 10000
                elif new_oth <= 0:
                    val = -10000
                else:
                    board_key = (tuple(b), other)
                    new_hist = dict(hist)
                    new_hist[board_key] = new_hist.get(board_key, 0) + 1
                    if new_hist[board_key] >= 3:
                        val = 0
                    else:
                        val = self._minimax(b, other, current, new_oth, new_cur, depth - 1, alpha, beta, True, new_hist)

                min_eval = min(min_eval, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval