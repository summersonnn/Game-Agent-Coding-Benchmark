"""
Agent Code: A8-SurroundMorris
Model: google/gemini-3-pro-preview
Run: 1
Generated: 2026-02-09 18:54:48
"""

import copy

import random
import copy

class SurroundMorrisAgent:
    """
    Agent for Surround Morris that uses Minimax with Alpha-Beta pruning to determine optimal moves.
    It rigorously simulates the specific capture rules (Suicide First, Self-Harm Priority) to avoid
    blunders and capitalize on opponent mistakes.
    """
    def __init__(self, name: str, color: str):
        """
        Initialize the agent.
        """
        self.name = name
        self.color = color
        self.opp_color = 'W' if color == 'B' else 'B'
        # Depth 2 allows the agent to see: My Move -> Opponent Response.
        # This is sufficient to detect immediate threats and tactical captures.
        self.depth = 2

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Determine the best move based on the current game state.
        If feedback is provided (meaning the previous move was invalid), falls back to a safe random move.
        """
        # Fallback logic for invalid moves to ensure game continuity
        if feedback:
            return self.get_random_move(state)

        board = state["board"]
        phase = state["phase"]
        history = state.get("history", [])

        # Get all legal moves
        legal_moves = self.get_legal_moves(board, phase, self.color)

        # Handle case with no legal moves (Mate condition, though engine usually catches this first)
        if not legal_moves:
            return 0 if phase == "placement" else (0, 1)

        # Initialize Minimax variables
        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        # Shuffle moves to provide variety in statically equal positions
        random.shuffle(legal_moves)

        for move in legal_moves:
            # Simulate the move to get the resulting board
            sim_board = self.simulate(board, move, phase, self.color)

            # Check for 3-fold repetition
            # The next state's active player is the opponent
            next_state_tuple = (tuple(sim_board), self.opp_color)
            rep_count = history.count(next_state_tuple)

            score = 0
            if rep_count >= 2:
                # If this move causes a 3rd repetition, evaluate as a Draw
                score = self.evaluate_draw(sim_board)
            else:
                # Recursively evaluate via Minimax
                # Pass updated history to detect repetitions deeper in the tree
                score = self.minimax(sim_board, self.depth - 1, alpha, beta, False, phase, history + [next_state_tuple])

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)
            if beta <= alpha:
                break

        # Return best found move, or a random legal move if something went wrong
        return best_move if best_move is not None else random.choice(legal_moves)

    def minimax(self, board, depth, alpha, beta, is_maximizing, phase, history):
        """
        Minimax algorithm with Alpha-Beta pruning.
        """
        # 1. Terminal State Checks
        my_count = board.count(self.color)
        opp_count = board.count(self.opp_color)

        if my_count == 0: return -10000  # I lost (Elimination)
        if opp_count == 0: return 10000  # I won (Elimination)

        # Determine active player for this node
        active_color = self.color if is_maximizing else self.opp_color
        legal_moves = self.get_legal_moves(board, phase, active_color)

        if not legal_moves:
            # Current player has no moves -> They lose (Mate)
            return -10000 if is_maximizing else 10000

        # 2. Leaf Node Evaluation
        if depth == 0:
            return self.evaluate(board, phase, len(legal_moves), is_maximizing)

        # 3. Recursive Search
        if is_maximizing:
            max_eval = -float('inf')
            for move in legal_moves:
                sim_board = self.simulate(board, move, phase, self.color)
                
                next_state_tuple = (tuple(sim_board), self.opp_color)
                rep_count = history.count(next_state_tuple)
                
                eval_val = 0
                if rep_count >= 2:
                    eval_val = self.evaluate_draw(sim_board)
                else:
                    eval_val = self.minimax(sim_board, depth - 1, alpha, beta, False, phase, history + [next_state_tuple])
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                sim_board = self.simulate(board, move, phase, self.opp_color)
                
                next_state_tuple = (tuple(sim_board), self.color)
                rep_count = history.count(next_state_tuple)
                
                eval_val = 0
                if rep_count >= 2:
                    eval_val = self.evaluate_draw(sim_board)
                else:
                    eval_val = self.minimax(sim_board, depth - 1, alpha, beta, True, phase, history + [next_state_tuple])
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate(self, board, phase, mobility_count, is_maximizing):
        """
        Heuristic evaluation of a board state from the perspective of self.color.
        """
        my_count = board.count(self.color)
        opp_count = board.count(self.opp_color)
        
        # Primary Heuristic: Material Difference
        # 100 points per piece advantage
        score = 100 * (my_count - opp_count)
        
        # Secondary Heuristic: Mobility (Movement Phase only)
        # Having more moves is generally better to avoid Mate and control board.
        if phase == 'movement':
            if is_maximizing:
                score += mobility_count
            else:
                score -= mobility_count
        
        return score

    def evaluate_draw(self, board):
        """
        Calculates the score for a Draw based on the competition rules:
        Score = Half the total pieces on board.
        """
        total = board.count(self.color) + board.count(self.opp_color)
        # Scale by 100 to match the material heuristic scale
        return (total / 2.0) * 100

    def get_legal_moves(self, board, phase, color):
        """
        Generates list of legal moves (int for placement, tuple for movement).
        """
        moves = []
        if phase == 'placement':
            for i in range(24):
                if board[i] == '':
                    moves.append(i)
        else:
            for i in range(24):
                if board[i] == color:
                    for n in ADJACENCY[i]:
                        if board[n] == '':
                            moves.append((i, n))
        return moves

    def get_random_move(self, state):
        """
        Helper for fallback logic.
        """
        board = state["board"]
        phase = state["phase"]
        moves = self.get_legal_moves(board, phase, self.color)
        return random.choice(moves) if moves else (0 if phase == 'placement' else (0, 1))

    def simulate(self, board, move, phase, active_color):
        """
        Simulates the full capture logic:
        1. Apply Move
        2. Suicide Check (Active piece dies first)
        3. Friendly Sweep (Self-Harm Priority)
        4. Enemy Sweep
        """
        new_board = list(board)
        
        # 1. Apply Move
        active_spot = -1
        if phase == 'placement':
            active_spot = move
            new_board[active_spot] = active_color
        else:
            frm, to = move
            new_board[frm] = ''
            new_board[to] = active_color
            active_spot = to
            
        # 2. Suicide Check
        # If the active piece is overwhelmed immediately, it dies.
        # It creates no pressure, so no other captures occur.
        if self.is_overwhelmed(active_spot, new_board, active_color):
            new_board[active_spot] = ''
            return new_board
            
        # 3. Friendly Sweep (Self-Harm Priority)
        # Check all friendly pieces. If overwhelmed, they are removed.
        # This might open up spots for enemies, saving them.
        friendlies_to_remove = []
        for i in range(24):
            if new_board[i] == active_color:
                if self.is_overwhelmed(i, new_board, active_color):
                    friendlies_to_remove.append(i)
        
        for i in friendlies_to_remove:
            new_board[i] = ''
            
        # 4. Enemy Sweep
        # Check all enemy pieces.
        opp_c = 'W' if active_color == 'B' else 'B'
        enemies_to_remove = []
        for i in range(24):
            if new_board[i] == opp_c:
                if self.is_overwhelmed(i, new_board, opp_c):
                    enemies_to_remove.append(i)
                    
        for i in enemies_to_remove:
            new_board[i] = ''
            
        return new_board

    def is_overwhelmed(self, spot, board, color):
        """
        Check if a piece satisfies the capture condition:
        (empty_neighbors == 0) AND (opponent_neighbors > friendly_neighbors)
        """
        # ADJACENCY is available globally per prompt
        neighbors = ADJACENCY[spot]
        empty = 0
        friendly = 0
        enemy = 0
        
        for n in neighbors:
            p = board[n]
            if p == '':
                empty += 1
            elif p == color:
                friendly += 1
            else:
                enemy += 1
        
        # Critical: If there is even one empty neighbor, the piece is safe.
        if empty > 0:
            return False
        
        return enemy > friendly
