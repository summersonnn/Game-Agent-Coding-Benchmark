"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-pro-preview
Run: 1
Generated: 2026-02-13 14:53:21
"""

import time

import time

class TicTacToeAgent:
    """
    Agent that uses Iterative Deepening Minimax with Alpha-Beta pruning
    and heuristic evaluation to play 5x5 Tic Tac Toe (3-in-a-row).
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.empty = ' '
        # Precompute winning lines and cell weights for efficiency
        self.lines = self._generate_winning_lines()
        self.cell_lines = self._generate_cell_lines()
        self.cell_weights = self._calculate_cell_weights()

    def make_move(self, board):
        """
        Determines the best move using minimax with alpha-beta pruning.
        Returns an integer 0-24.
        """
        valid_moves = [i for i, x in enumerate(board) if x == self.empty]
        
        if not valid_moves:
            return -1 # Should not happen in normal play

        # 1. Check for Immediate Win
        for move in valid_moves:
            if self._check_win_simulated(board, move, self.symbol):
                return move

        # 2. Check for Forced Block (Opponent winning next)
        # If opponent has a winning move, we MUST block.
        for move in valid_moves:
            if self._check_win_simulated(board, move, self.opponent):
                return move

        # 3. Iterative Deepening Minimax
        # Sort moves initially by centrality/frequency to improve pruning
        valid_moves.sort(key=lambda m: self.cell_weights[m], reverse=True)
        best_move = valid_moves[0]
        
        start_time = time.time()
        time_limit = 0.95  # 1 second limit, keep a buffer
        
        try:
            # Iterative deepening from depth 1 upwards
            for depth in range(1, 20):
                if time.time() - start_time > time_limit:
                    break
                
                score, move = self._minimax(board, depth, -float('inf'), float('inf'), True, start_time, time_limit)
                
                if move is not None:
                    best_move = move
                
                # If we found a guaranteed win, stop searching to save time
                if score > 90000:
                    break
                    
        except TimeoutError:
            # If time runs out, return the best move found in the last fully completed depth
            pass

        return best_move

    def _minimax(self, board, depth, alpha, beta, maximizing, start_time, time_limit):
        # Check timeout
        if time.time() - start_time > time_limit:
            raise TimeoutError

        # Leaf node evaluation
        if depth == 0:
            return self._evaluate(board), None

        valid_moves = [i for i, x in enumerate(board) if x == self.empty]
        if not valid_moves:
            return 0, None # Draw

        # Optimization: Sort moves by heuristic weight for internal nodes too
        valid_moves.sort(key=lambda m: self.cell_weights[m], reverse=True)
        
        best_move = valid_moves[0]

        if maximizing:
            max_eval = -float('inf')
            for move in valid_moves:
                board[move] = self.symbol
                
                # Optimization: Check if this move wins immediately
                if self._check_win_fast(board, move, self.symbol):
                    board[move] = self.empty
                    return 100000 + depth, move # Prefer faster wins

                try:
                    eval_score, _ = self._minimax(board, depth - 1, alpha, beta, False, start_time, time_limit)
                except TimeoutError:
                    board[move] = self.empty
                    raise
                
                board[move] = self.empty
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in valid_moves:
                board[move] = self.opponent
                
                # Optimization: Check if this move wins immediately for opponent
                if self._check_win_fast(board, move, self.opponent):
                    board[move] = self.empty
                    return -100000 - depth, move # Prefer slower losses

                try:
                    eval_score, _ = self._minimax(board, depth - 1, alpha, beta, True, start_time, time_limit)
                except TimeoutError:
                    board[move] = self.empty
                    raise
                
                board[move] = self.empty
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def _evaluate(self, board):
        """
        Heuristic evaluation of the board state.
        """
        score = 0
        
        # Iterate all precomputed winning lines
        for a, b, c in self.lines:
            cells = [board[a], board[b], board[c]]
            my_count = cells.count(self.symbol)
            opp_count = cells.count(self.opponent)
            empty_count = cells.count(self.empty)
            
            if my_count == 3: return 100000
            if opp_count == 3: return -100000
            
            # Threats (2 marks + 1 empty)
            if empty_count == 1:
                if my_count == 2:
                    score += 500
                elif opp_count == 2:
                    score -= 600 # Weight opponent threats slightly higher to prioritize defense
            
            # Potentials (1 mark + 2 empty)
            elif empty_count == 2:
                if my_count == 1:
                    score += 10
                elif opp_count == 1:
                    score -= 10
        
        return score

    def _check_win_simulated(self, board, move, player):
        """Temporarily applies a move to check for a win."""
        board[move] = player
        is_win = self._check_win_fast(board, move, player)
        board[move] = self.empty
        return is_win

    def _check_win_fast(self, board, move, player):
        """Checks if the player won, looking only at lines containing 'move'."""
        for a, b, c in self.cell_lines[move]:
            if board[a] == player and board[b] == player and board[c] == player:
                return True
        return False

    def _generate_winning_lines(self):
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                s = r * 5 + c
                lines.append((s, s + 1, s + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                lines.append((s, s + 5, s + 10))
        # Diagonals (Down-Right)
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                lines.append((s, s + 6, s + 12))
        # Diagonals (Down-Left)
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                lines.append((s, s + 4, s + 8))
        return lines

    def _generate_cell_lines(self):
        # Map each cell to the lines that pass through it
        mapping = [[] for _ in range(25)]
        for line in self.lines:
            for cell in line:
                mapping[cell].append(line)
        return mapping

    def _calculate_cell_weights(self):
        # Calculate how many winning lines pass through each cell
        weights = [0] * 25
        for line in self.lines:
            for cell in line:
                weights[cell] += 1
        return weights
