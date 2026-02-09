"""
Agent Code: A8-SurroundMorris
Model: google/gemini-3-pro-preview
Run: 2
Generated: 2026-02-09 18:54:48
"""



import random

class SurroundMorrisAgent:
    """
    Agent for Surround Morris strategy game.
    Uses Minimax with Alpha-Beta pruning to determine optimal moves.
    Handles 'Overwhelm' capture logic including suicide and self-harm priority.
    """
    def __init__(self, name: str, color: str):
        """
        Initialize the agent.
        """
        self.name = name
        self.color = color
        self.opp_color = 'W' if color == 'B' else 'B'
        # Depth 3 is chosen to balance lookahead with performance (timeout prevention)
        # given the branching factor of the game.
        self.depth = 3

    def make_move(self, state: dict, feedback: dict | None = None):
        """
        Determines the best move based on the current game state using Minimax.
        """
        board = state["board"]
        phase = state["phase"]
        history = state.get("history", [])

        # If previous move was invalid (feedback provided), fallback to random to ensure legality
        if feedback:
            return self._get_random_move(board, phase)

        # Get all legal moves
        legal_moves = self._get_legal_moves(board, phase, self.color)
        
        # If no legal moves, we are in a loss state (Mate). 
        # Return a dummy move; the engine will handle the game end.
        if not legal_moves:
            return self._get_random_move(board, phase)

        # Optimization: If only one move is available, take it immediately
        if len(legal_moves) == 1:
            return legal_moves[0]

        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        # Shuffle moves to ensure variety in equivalent positions
        random.shuffle(legal_moves)

        for move in legal_moves:
            # Simulate the move to get the resulting board
            sim_board = self._simulate(board, move, phase, self.color)
            
            # Check for 3-fold repetition (Draw)
            # The state history stores (board_tuple, current_player).
            # After my move, the next state is (sim_board, opponent).
            next_state_key = (tuple(sim_board), self.opp_color)
            repetition_count = history.count(next_state_key)
            
            if repetition_count >= 2:
                # This move leads to a draw. Score it as 0 (neutral).
                # If we are winning (score > 0), Minimax will avoid this.
                # If we are losing (score < 0), Minimax will prefer this.
                score = 0
            else:
                # Run Minimax search
                score = self._minimax(sim_board, self.depth - 1, False, alpha, beta, phase)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        
        return best_move if best_move is not None else random.choice(legal_moves)

    def _minimax(self, board, depth, is_maximizing, alpha, beta, phase):
        # Evaluate if leaf node or depth limit reached
        current_score = self._evaluate(board, phase)
        
        # If terminal state (huge score indicating win/loss), return immediately
        if abs(current_score) > 5000:
            return current_score
            
        if depth == 0:
            return current_score

        current_mover = self.color if is_maximizing else self.opp_color
        legal_moves = self._get_legal_moves(board, phase, current_mover)

        # Check for Mate (no legal moves)
        if not legal_moves:
            # If current mover has no moves, they lose.
            # If maximizing (me) has no moves -> -10000
            # If minimizing (opp) has no moves -> +10000
            return -10000 if is_maximizing else 10000

        if is_maximizing:
            max_eval = -float('inf')
            for move in legal_moves:
                sim_board = self._simulate(board, move, phase, current_mover)
                eval_score = self._minimax(sim_board, depth - 1, False, alpha, beta, phase)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                sim_board = self._simulate(board, move, phase, current_mover)
                eval_score = self._minimax(sim_board, depth - 1, True, alpha, beta, phase)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, board, phase):
        """
        Heuristic evaluation of the board.
        Positive score favors self.color.
        """
        my_pieces = board.count(self.color)
        opp_pieces = board.count(self.opp_color)

        # 1. Elimination Check
        if my_pieces == 0: return -10000
        if opp_pieces == 0: return 10000

        # 2. Material Score (Heavily weighted)
        score = 100 * (my_pieces - opp_pieces)

        # 3. Mobility and Danger Analysis
        my_mobility = 0
        opp_mobility = 0
        my_danger = 0
        opp_danger = 0
        
        # Positional weights
        corners = [0, 2, 9, 14, 21, 23]
        crossroads = [4, 10, 13, 19]

        for i in range(24):
            p = board[i]
            if p == '': continue
            
            # Count empty neighbors
            empty_neighbors = 0
            for n in ADJACENCY[i]:
                if board[n] == '':
                    empty_neighbors += 1
            
            if p == self.color:
                my_mobility += empty_neighbors
                # Penalty for being trapped or near trapped
                if empty_neighbors == 0: my_danger += 3
                elif empty_neighbors == 1: my_danger += 1
                
                # Bonus/Penalty for position type
                if i in crossroads: score += 5
                if i in corners: score -= 3
            else:
                opp_mobility += empty_neighbors
                if empty_neighbors == 0: opp_danger += 3
                elif empty_neighbors == 1: opp_danger += 1
                
                if i in crossroads: score -= 5
                if i in corners: score += 3

        score += 5 * (my_mobility - opp_mobility)
        score -= 10 * (my_danger - opp_danger)

        return score

    def _simulate(self, board, move, phase, active_color):
        """
        Simulates a move and processes the 'Overwhelm' capture logic.
        Returns the new board state.
        """
        new_board = list(board)
        opp_c = 'W' if active_color == 'B' else 'B'
        active_spot = -1

        # Apply the move
        if phase == 'placement':
            active_spot = move
            new_board[active_spot] = active_color
        else:
            src, dst = move
            new_board[src] = ''
            new_board[dst] = active_color
            active_spot = dst

        # 1. Active Piece Suicide Check
        if self._is_captured(active_spot, new_board, active_color, opp_c):
            new_board[active_spot] = ''
            # If suicide, turn ends immediately. No other captures occur.
            return new_board

        # 2. Universal Capture Sweep
        # 2a. Identify Friendly pieces to be removed (Self-Harm Priority)
        friends_to_die = []
        for i, p in enumerate(new_board):
            if p == active_color:
                if self._is_captured(i, new_board, active_color, opp_c):
                    friends_to_die.append(i)
        
        # 2b. Identify Enemy pieces that MIGHT be removed
        enemies_to_check = []
        for i, p in enumerate(new_board):
            if p == opp_c:
                if self._is_captured(i, new_board, opp_c, active_color):
                    enemies_to_check.append(i)

        # Execute Friendly deaths first
        for i in friends_to_die:
            new_board[i] = ''

        # Re-check Enemy candidates
        # Some enemies might survive if a friendly neighbor died (opening a spot)
        for i in enemies_to_check:
            if self._is_captured(i, new_board, opp_c, active_color):
                new_board[i] = ''

        return new_board

    def _is_captured(self, spot, board, my_c, opp_c):
        """
        Check if a piece at 'spot' is overwhelmed.
        Condition: 0 empty neighbors AND opponent neighbors > friendly neighbors.
        """
        empty = 0
        friendly = 0
        enemy = 0
        for n in ADJACENCY[spot]:
            val = board[n]
            if val == '':
                empty += 1
            elif val == my_c:
                friendly += 1
            elif val == opp_c:
                enemy += 1
        
        # If there is any breathing room, it's safe
        if empty > 0:
            return False
        
        # Must be strictly overwhelmed
        return enemy > friendly

    def _get_legal_moves(self, board, phase, color):
        if phase == 'placement':
            return [i for i, x in enumerate(board) if x == '']
        else:
            moves = []
            for i, p in enumerate(board):
                if p == color:
                    for n in ADJACENCY[i]:
                        if board[n] == '':
                            moves.append((i, n))
            return moves

    def _get_random_move(self, board, phase):
        if phase == 'placement':
            empty = [i for i, x in enumerate(board) if x == '']
            return random.choice(empty) if empty else 0
        else:
            moves = self._get_legal_moves(board, phase, self.color)
            return random.choice(moves) if moves else (0, 1)
