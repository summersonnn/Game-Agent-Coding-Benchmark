"""
Agent Code: A8-SurroundMorris
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-17 14:26:05
"""

from typing import List, Tuple, Dict

import random
from typing import List, Tuple, Dict


class SurroundMorrisAgent:
    """
    Agent for Surround Morris.
    Uses heuristic evaluation and shallow minimax search.
    """
    # Board adjacency graph (self‑contained)
    ADJACENCY = {
        0: [1, 9],       1: [0, 2, 4],     2: [1, 14],
        3: [4, 10],      4: [1, 3, 5, 7],  5: [4, 13],
        6: [7, 11],      7: [4, 6, 8],     8: [7, 12],
        9: [0, 10, 21],  10: [3, 9, 11, 18], 11: [6, 10, 15],
        12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
        15: [11, 16],    16: [15, 17, 19],  17: [12, 16],
        18: [10, 19],    19: [16, 18, 20, 22], 20: [13, 19],
        21: [9, 22],     22: [19, 21, 23],  23: [14, 22],
    }

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.opp_color = 'W' if color == 'B' else 'B'
        # Pre‑compute spot degrees and centrality bonus (0,1,2)
        self.deg = {s: len(nbrs) for s, nbrs in self.ADJACENCY.items()}
        self.centrality = {s: max(0, len(nbrs) - 2) for s, nbrs in self.ADJACENCY.items()}

    # ------------------------------------------------------------------
    #  Core game‑logic helpers
    # ------------------------------------------------------------------
    def _is_captured(self, spot: int, board: List[str]) -> bool:
        piece = board[spot]
        if piece == '':
            return False
        empty = opp = friend = 0
        for nb in self.ADJACENCY[spot]:
            v = board[nb]
            if v == '':
                empty += 1
            elif v == piece:
                friend += 1
            else:
                opp += 1
        return empty == 0 and opp > friend

    def _simulate_placement(self, board: List[str], spot: int, color: str) -> List[str]:
        """Place a piece and resolve captures."""
        b = board.copy()
        b[spot] = color
        # Active‑piece suicide check
        if self._is_captured(spot, b):
            b[spot] = ''
            return b
        opp = 'W' if color == 'B' else 'B'
        # Friendly captures first
        to_rem = [s for s in range(24) if b[s] == color and self._is_captured(s, b)]
        for s in to_rem:
            b[s] = ''
        # Enemy captures (re‑checked after friendly removal)
        to_rem_e = [s for s in range(24) if b[s] == opp and self._is_captured(s, b)]
        for s in to_rem_e:
            b[s] = ''
        return b

    def _simulate_move(self, board: List[str], src: int, dst: int, color: str) -> List[str]:
        """Slide a piece and resolve captures."""
        b = board.copy()
        b[src] = ''
        b[dst] = color
        # Active‑piece suicide check
        if self._is_captured(dst, b):
            b[dst] = ''
            return b
        opp = 'W' if color == 'B' else 'B'
        # Friendly captures
        to_rem = [s for s in range(24) if b[s] == color and self._is_captured(s, b)]
        for s in to_rem:
            b[s] = ''
        # Enemy captures
        to_rem_e = [s for s in range(24) if b[s] == opp and self._is_captured(s, b)]
        for s in to_rem_e:
            b[s] = ''
        return b

    # ------------------------------------------------------------------
    #  Evaluation
    # ------------------------------------------------------------------
    def _evaluate(self, board: List[str]) -> int:
        my, opp = self.color, self.opp_color
        my_cnt = board.count(my)
        opp_cnt = board.count(opp)
        if my_cnt == 0:
            return -10000
        if opp_cnt == 0:
            return 10000

        my_mob = opp_mob = 0
        my_cent = opp_cent = 0
        my_trap = opp_trap = 0

        for s in range(24):
            p = board[s]
            if p == '':
                continue
            empty_n = sum(1 for nb in self.ADJACENCY[s] if board[nb] == '')
            if p == my:
                my_mob += empty_n
                my_cent += self.centrality[s]
                if empty_n == 0:
                    my_trap += 1
            else:
                opp_mob += empty_n
                opp_cent += self.centrality[s]
                if empty_n == 0:
                    opp_trap += 1

        score = 100 * (my_cnt - opp_cnt)
        score += 5 * (my_mob - opp_mob)
        score += 3 * (my_cent - opp_cent)
        score -= 10 * (my_trap - opp_trap)
        return score

    # ------------------------------------------------------------------
    #  Move generation
    # ------------------------------------------------------------------
    def _legal_placements(self, board: List[str]) -> List[int]:
        return [i for i in range(24) if board[i] == '']

    def _legal_moves(self, board: List[str], color: str) -> List[Tuple[int, int]]:
        moves = []
        for s in range(24):
            if board[s] != color:
                continue
            for nb in self.ADJACENCY[s]:
                if board[nb] == '':
                    moves.append((s, nb))
        return moves

    def _is_draw_by_repetition(self, board: List[str], player: str, history: List[Tuple]) -> bool:
        state = (tuple(board), player)
        return history.count(state) >= 2

    # ------------------------------------------------------------------
    #  Public interface
    # ------------------------------------------------------------------
    def make_move(self, state: Dict, feedback=None):
        board = state["board"]
        phase = state["phase"]
        my = state["your_color"]
        opp = state["opponent_color"]
        history = state.get("history", [])

        if phase == "placement":
            return self._placement(board, my, opp, state, history)
        else:
            return self._movement(board, my, opp, history)

    # ------------------------------------------------------------------
    #  Placement phase (depth‑2 minimax)
    # ------------------------------------------------------------------
    def _placement(self, board, my, opp, state, history):
        empties = self._legal_placements(board)
        if not empties:
            return 0

        best_score = -999999
        best_spot = empties[0]
        opp_hand = state["pieces_in_hand"].get(opp, 0)

        for spot in empties:
            b1 = self._simulate_placement(board, spot, my)
            # Immediate terminal
            if b1.count(my) == 0:
                sc = -9000
            elif b1.count(opp) == 0:
                sc = 9000
            else:
                # Opponent replies (if they have pieces)
                if opp_hand > 0:
                    worst = 999999
                    for ospot in self._legal_placements(b1):
                        b2 = self._simulate_placement(b1, ospot, opp)
                        val = self._evaluate(b2)
                        if val < worst:
                            worst = val
                            if worst <= -8000:
                                break
                    sc = worst
                else:
                    sc = self._evaluate(b1)

            if self._is_draw_by_repetition(b1, opp, history):
                sc -= 5000

            if sc > best_score:
                best_score = sc
                best_spot = spot

        return best_spot

    # ------------------------------------------------------------------
    #  Movement phase (alpha‑beta, depth 2 or 3)
    # ------------------------------------------------------------------
    def _movement(self, board, my, opp, history):
        moves = self._legal_moves(board, my)
        if not moves:
            return (0, 0)

        # Immediate wins / suicides
        winners = []
        losers = []
        safe = []
        for m in moves:
            src, dst = m
            b = self._simulate_move(board, src, dst, my)
            if b.count(opp) == 0:
                winners.append(m)
            elif b.count(my) == 0:
                losers.append(m)
            else:
                safe.append(m)

        if winners:
            return winners[0]
        if not safe:
            # forced suicide
            return random.choice(moves)

        moves = safe
        total_pieces = board.count(my) + board.count(opp)
        depth = 3 if total_pieces <= 6 else 2

        # Alpha‑beta
        def minimax(b, player, d, alpha, beta):
            if d == 0:
                return self._evaluate(b)
            legal = self._legal_moves(b, player)
            if not legal:
                return -10000 if player == my else 10000
            if player == my:
                best = -1000000
                for mv in legal:
                    nb = self._simulate_move(b, mv[0], mv[1], player)
                    val = minimax(nb, opp, d - 1, alpha, beta)
                    best = max(best, val)
                    alpha = max(alpha, val)
                    if beta <= alpha:
                        break
                return best
            else:
                best = 1000000
                for mv in legal:
                    nb = self._simulate_move(b, mv[0], mv[1], player)
                    val = minimax(nb, my, d - 1, alpha, beta)
                    best = min(best, val)
                    beta = min(beta, val)
                    if beta <= alpha:
                        break
                return best

        best_score = -999999
        best_move = moves[0]
        random.shuffle(moves)
        for m in moves:
            src, dst = m
            b = self._simulate_move(board, src, dst, my)
            if self._is_draw_by_repetition(b, opp, history):
                sc = -2000
            else:
                sc = minimax(b, opp, depth - 1, -1000000, 1000000) if depth > 0 else self._evaluate(b)
            if sc > best_score:
                best_score = sc
                best_move = m
        return best_move
