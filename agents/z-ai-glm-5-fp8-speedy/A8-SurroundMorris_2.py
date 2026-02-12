"""
Agent Code: A8-SurroundMorris
Model: z-ai/glm-5@preset/fp8
Run: 2
Generated: 2026-02-11 21:33:53
"""



import random


class SurroundMorrisAgent:
    """
    Agent for Surround Morris using position evaluation and capture simulation.
    """
    
    CORNERS = {0, 2, 3, 5, 6, 8, 15, 17, 18, 20, 21, 23}
    T_JUNCTIONS = {1, 7, 9, 11, 12, 14, 16, 22}
    CROSSROADS = {4, 10, 13, 19}

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def make_move(self, state: dict, feedback: dict | None = None):
        board = tuple(state["board"])
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]

        if phase == "placement":
            return self._make_placement(board, color, opp, state)
        else:
            return self._make_movement(board, color, opp, state)

    def _is_captured(self, board, spot, my_color, opp_color):
        neighbors = ADJACENCY[spot]
        empty_count = sum(1 for n in neighbors if board[n] == '')
        friendly_count = sum(1 for n in neighbors if board[n] == my_color)
        opponent_count = sum(1 for n in neighbors if board[n] == opp_color)
        return empty_count == 0 and opponent_count > friendly_count

    def _simulate_placement(self, board, spot, color, opp):
        new_board = list(board)
        new_board[spot] = color

        # Step 1: Suicide check
        if self._is_captured(new_board, spot, color, opp):
            new_board[spot] = ''
            return tuple(new_board), 0, 0, True

        # Step 2a: Remove captured friendly pieces (self-harm priority)
        to_remove = [s for s in range(24) if new_board[s] == color and s != spot 
                     and self._is_captured(new_board, s, color, opp)]
        friendly_deaths = len(to_remove)
        for s in to_remove:
            new_board[s] = ''

        # Step 2b: Remove captured enemy pieces
        to_remove = [s for s in range(24) if new_board[s] == opp 
                     and self._is_captured(new_board, s, opp, color)]
        enemy_deaths = len(to_remove)
        for s in to_remove:
            new_board[s] = ''

        return tuple(new_board), friendly_deaths, enemy_deaths, False

    def _simulate_movement(self, board, from_spot, to_spot, color, opp):
        new_board = list(board)
        new_board[from_spot] = ''
        new_board[to_spot] = color

        # Step 1: Suicide check
        if self._is_captured(new_board, to_spot, color, opp):
            new_board[to_spot] = ''
            return tuple(new_board), 0, 0, True

        # Step 2a: Remove captured friendly pieces
        to_remove = [s for s in range(24) if new_board[s] == color and s != to_spot 
                     and self._is_captured(new_board, s, color, opp)]
        friendly_deaths = len(to_remove)
        for s in to_remove:
            new_board[s] = ''

        # Step 2b: Remove captured enemy pieces
        to_remove = [s for s in range(24) if new_board[s] == opp 
                     and self._is_captured(new_board, s, opp, color)]
        enemy_deaths = len(to_remove)
        for s in to_remove:
            new_board[s] = ''

        return tuple(new_board), friendly_deaths, enemy_deaths, False

    def _count_pieces(self, board, color):
        return sum(1 for s in range(24) if board[s] == color)

    def _get_legal_moves(self, board, color):
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for neighbor in ADJACENCY[spot]:
                if board[neighbor] == '':
                    moves.append((spot, neighbor))
        return moves

    def _evaluate_board(self, board, color, opp):
        my_pieces = self._count_pieces(board, color)
        opp_pieces = self._count_pieces(board, opp)

        if my_pieces == 0:
            return -100000
        if opp_pieces == 0:
            return 100000

        my_mobility = len(self._get_legal_moves(board, color))
        opp_mobility = len(self._get_legal_moves(board, opp))

        if my_mobility == 0:
            return -100000
        if opp_mobility == 0:
            return 100000

        score = (my_pieces - opp_pieces) * 100 + (my_mobility - opp_mobility) * 10

        for s in range(24):
            if board[s] == color:
                score += 5 if s in self.CROSSROADS else (3 if s in self.T_JUNCTIONS else 1)
                neighbors = ADJACENCY[s]
                empty_count = sum(1 for n in neighbors if board[n] == '')
                my_count = sum(1 for n in neighbors if board[n] == color)
                opp_count = sum(1 for n in neighbors if board[n] == opp)
                if empty_count == 0 and opp_count > my_count:
                    score -= 50
                elif empty_count == 1 and opp_count > my_count:
                    score -= 15
                else:
                    score += empty_count
            elif board[s] == opp:
                neighbors = ADJACENCY[s]
                empty_count = sum(1 for n in neighbors if board[n] == '')
                my_count = sum(1 for n in neighbors if board[n] == color)
                opp_count = sum(1 for n in neighbors if board[n] == opp)
                if empty_count == 0 and my_count > opp_count:
                    score += 40
                elif empty_count == 1 and my_count > opp_count:
                    score += 15

        return score

    def _make_placement(self, board, color, opp, state):
        empty = [i for i in range(24) if board[i] == '']
        if not empty:
            return 0

        best_spots, best_score = [], float('-inf')

        for spot in empty:
            new_board, friendly_deaths, enemy_deaths, is_suicide = self._simulate_placement(board, spot, color, opp)
            score = -50000 if is_suicide else self._evaluate_board(new_board, color, opp) + enemy_deaths * 300 - friendly_deaths * 200
            if score > best_score:
                best_score, best_spots = score, [spot]
            elif score == best_score:
                best_spots.append(spot)

        return random.choice(best_spots)

    def _make_movement(self, board, color, opp, state):
        moves = self._get_legal_moves(board, color)
        if not moves:
            return (0, 1)

        best_moves, best_score = [], float('-inf')
        history = state.get("history", [])

        for from_spot, to_spot in moves:
            new_board, friendly_deaths, enemy_deaths, is_suicide = self._simulate_movement(board, from_spot, to_spot, color, opp)
            if is_suicide:
                score = -50000
            else:
                score = self._evaluate_board(new_board, color, opp) + enemy_deaths * 300 - friendly_deaths * 200
                if sum(1 for h in history if h[0] == new_board and h[1] == opp) >= 2:
                    score -= 3000
            if score > best_score:
                best_score, best_moves = score, [(from_spot, to_spot)]
            elif score == best_score:
                best_moves.append((from_spot, to_spot))

        return random.choice(best_moves)
