"""
Agent Code: A8-SurroundMorris
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-09 19:15:26
"""



import random

# Global Adjacency Graph
ADJACENCY = {
    0: [1, 9],       1: [0, 2, 4],     2: [1, 14],
    3: [4, 10],      4: [1, 3, 5, 7],  5: [4, 13],
    6: [7, 11],      7: [4, 6, 8],     8: [7, 12],
    9: [0, 10, 21],  10: [3, 9, 11, 18], 11: [6, 10, 15],
    12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
    15: [11, 16],    16: [15, 17, 19],  17: [12, 16],
    18: [10, 19],    19: [16, 18, 20, 22], 20: [13, 19],
    21: [9, 22],     22: [19, 21, 23], 23: [14, 22],
}

# Positional weights: 2-neighbor spots (corners/inner) are weak (1), 
# 3-neighbor spots (sides) are medium (3), 4-neighbor spots (crossroads) are strong (5).
POSITION_WEIGHTS = [
    1, 3, 1,
    1, 5, 1,
    1, 3, 1,
    3, 5, 3,
    3, 5, 3,
    1, 3, 1,
    1, 5, 1,
    1, 3, 1
]

class SurroundMorrisAgent:
    """
    A strategic agent for Surround Morris using Minimax with Alpha-Beta pruning.
    """
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.max_depth = 3  # Search depth

    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        player = state["your_color"]
        opponent = state["opponent_color"]
        history = state["history"]

        if phase == "placement":
            return self._decide_placement(board, player, opponent, history)
        else:
            return self._decide_movement(board, player, opponent, history)

    def _decide_placement(self, board, player, opponent, history):
        """Select a placement spot using minimax."""
        legal_moves = [i for i in range(24) if board[i] == '']
        if not legal_moves:
            return 0 # Should not happen

        best_score = -float('inf')
        best_move = legal_moves[0]
        random.shuffle(legal_moves)

        for move in legal_moves:
            new_board, _ = self._simulate(board, move, "placement", player, opponent)
            
            # Check for 3-fold repetition (Draw)
            if self._is_repetition(new_board, opponent, history):
                current_score = 0
            else:
                current_score = self._minimax(new_board, self.max_depth - 1, False, player, opponent, -float('inf'), float('inf'))

            if current_score > best_score:
                best_score = current_score
                best_move = move
        
        return best_move

    def _decide_movement(self, board, player, opponent, history):
        """Select a movement using minimax."""
        legal_moves = []
        for spot in range(24):
            if board[spot] == player:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        legal_moves.append((spot, neighbor))
        
        if not legal_moves:
            return (0, 1) # No moves, loss is imminent

        best_score = -float('inf')
        best_move = legal_moves[0]
        random.shuffle(legal_moves)

        for move in legal_moves:
            new_board, _ = self._simulate(board, move, "movement", player, opponent)
            
            # Check for Mate (Opponent has no moves)
            if not self._has_moves(new_board, opponent):
                return move # Immediate win
            
            # Check for 3-fold repetition
            if self._is_repetition(new_board, opponent, history):
                current_score = 0
            else:
                current_score = self._minimax(new_board, self.max_depth - 1, False, player, opponent, -float('inf'), float('inf'))

            if current_score > best_score:
                best_score = current_score
                best_move = move
                
        return best_move

    def _simulate(self, board, move, phase, player, opponent):
        """
        Simulates a move and applies capture logic (Suicide First, Self-Harm Priority).
        Returns (new_board_list, active_piece_died_bool).
        """
        new_board = list(board)
        active_spot = -1

        if phase == "placement":
            spot = move
            new_board[spot] = player
            active_spot = spot
        else:
            from_s, to_s = move
            new_board[from_s] = ''
            new_board[to_s] = player
            active_spot = to_s

        # 1. Active Piece Suicide Check
        if self._is_overwhelmed(active_spot, new_board, player):
            new_board[active_spot] = ''
            return new_board, True

        # 2. Friendly Sweep (Self-Harm Priority)
        dead_friendlies = []
        for i in range(24):
            if new_board[i] == player and self._is_overwhelmed(i, new_board, player):
                dead_friendlies.append(i)
        for i in dead_friendlies:
            new_board[i] = ''

        # 3. Enemy Sweep
        dead_enemies = []
        for i in range(24):
            if new_board[i] == opponent and self._is_overwhelmed(i, new_board, opponent):
                dead_enemies.append(i)
        for i in dead_enemies:
            new_board[i] = ''

        return new_board, False

    def _is_overwhelmed(self, spot, board, color):
        """Checks if a piece is surrounded (0 empty neighbors) and outnumbered."""
        neighbors = ADJACENCY[spot]
        empty = 0
        opp = 0
        friend = 0
        
        for n in neighbors:
            val = board[n]
            if val == '':
                empty += 1
            elif val == color:
                friend += 1
            else:
                opp += 1
        
        return (empty == 0) and (opp > friend)

    def _has_moves(self, board, color):
        """Checks if a player has any legal moves."""
        for spot in range(24):
            if board[spot] == color:
                for neighbor in ADJACENCY[spot]:
                    if board[neighbor] == '':
                        return True
        return False

    def _is_repetition(self, board, next_player, history):
        """Checks if the resulting board state has occurred twice before (3rd rep)."""
        state_key = (tuple(board), next_player)
        return history.count(state_key) >= 2

    def _minimax(self, board, depth, is_maximizing, player, opponent, alpha, beta):
        """Minimax algorithm with Alpha-Beta pruning."""
        # Determine phase based on piece count
        total_pieces = 24 - board.count('')
        phase = "placement" if total_pieces < 14 else "movement"

        # Terminal Conditions
        p_count = board.count(player)
        o_count = board.count(opponent)

        if p_count == 0: return -10000 # Loss
        if o_count == 0: return 10000  # Win
        
        if depth == 0:
            return self._evaluate(board, player, opponent)

        if is_maximizing:
            # Generate Moves
            legal_moves = []
            if phase == "placement":
                legal_moves = [i for i in range(24) if board[i] == '']
            else:
                if not self._has_moves(board, player): return -10000 # Mate
                for s in range(24):
                    if board[s] == player:
                        for n in ADJACENCY[s]:
                            if board[n] == '':
                                legal_moves.append((s, n))
            
            max_eval = -float('inf')
            for move in legal_moves:
                new_board, _ = self._simulate(board, move, phase, player, opponent)
                eval_val = self._minimax(new_board, depth - 1, False, player, opponent, alpha, beta)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # Generate Moves for Opponent
            legal_moves = []
            if phase == "placement":
                legal_moves = [i for i in range(24) if board[i] == '']
            else:
                if not self._has_moves(board, opponent): return 10000 # Opponent Mated
                for s in range(24):
                    if board[s] == opponent:
                        for n in ADJACENCY[s]:
                            if board[n] == '':
                                legal_moves.append((s, n))
            
            min_eval = float('inf')
            for move in legal_moves:
                new_board, _ = self._simulate(board, move, phase, opponent, player)
                eval_val = self._minimax(new_board, depth - 1, True, player, opponent, alpha, beta)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, board, player, opponent):
        """Heuristic evaluation of the board state."""
        score = 0
        
        # 1. Material Difference
        score += (board.count(player) - board.count(opponent)) * 100
        
        # 2. Positional Value
        p_pos = sum(POSITION_WEIGHTS[i] for i in range(24) if board[i] == player)
        o_pos = sum(POSITION_WEIGHTS[i] for i in range(24) if board[i] == opponent)
        score += (p_pos - o_pos) * 5
        
        # 3. Mobility
        p_mob = 0
        o_mob = 0
        for i in range(24):
            if board[i] == player:
                for n in ADJACENCY[i]:
                    if board[n] == '': p_mob += 1
            elif board[i] == opponent:
                for n in ADJACENCY[i]:
                    if board[n] == '': o_mob += 1
        score += (p_mob - o_mob) * 2
        
        return score
