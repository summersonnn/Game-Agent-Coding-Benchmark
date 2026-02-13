"""
Agent Code: A2-TicTacToe
Model: google/gemini-3-pro-preview
Run: 2
Generated: 2026-02-13 14:53:21
"""

import time

import random
import time

class TicTacToeAgent:
    """
    A Tic Tac Toe agent that uses Iterative Deepening Minimax with Alpha-Beta pruning.
    It includes optimizations for the specific 5x5 grid with 3-in-a-row rules,
    such as precomputed winning lines, fast win checking, and heuristic move ordering.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
        # --- Precompute Winning Lines ---
        # The game engine defines win conditions as 3-in-a-row on a 5x5 grid.
        self.win_lines = []
        
        # Rows: 5 rows * 3 segments
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 1, start + 2))
        
        # Cols: 5 cols * 3 segments
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 5, start + 10))
                
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 6, start + 12))
                
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_lines.append((start, start + 4, start + 8))
                
        # --- Lookup Tables for Optimization ---
        # Map each cell to the lines that pass through it.
        # This allows O(1) retrieval of relevant lines for win checking.
        self.cell_lines = {i: [] for i in range(25)}
        for line in self.win_lines:
            for cell in line:
                self.cell_lines[cell].append(line)

        # Positional weights: Prefer cells involved in more winning lines (e.g., center)
        self.pos_weights = [0] * 25
        for line in self.win_lines:
            for cell in line:
                self.pos_weights[cell] += 1

    def make_move(self, board):
        """
        Calculates the best move within the 1-second time limit.
        """
        start_time = time.time()
        time_limit = 0.92  # Leave a safety buffer
        
        # Identify available moves
        empties = [i for i, x in enumerate(board) if x == ' ']
        if not empties:
            return None 
            
        # Create a working copy of the board
        search_board = board[:]

        # 1. Immediate Win Check (Priority 1)
        # If we can win now, do it.
        for m in empties:
            search_board[m] = self.symbol
            if self.check_win_fast(search_board, m, self.symbol):
                return m
            search_board[m] = ' '
            
        # 2. Immediate Block Check (Priority 2)
        # If opponent can win next, we must block.
        blocks = []
        for m in empties:
            search_board[m] = self.opponent
            if self.check_win_fast(search_board, m, self.opponent):
                blocks.append(m)
            search_board[m] = ' '
            
        if blocks:
            # If multiple blocks exist, we are in a bad spot (forked).
            # Pick the block that offers the best positional value to maximize survival chance.
            blocks.sort(key=lambda x: self.pos_weights[x], reverse=True)
            return blocks[0]

        # 3. Iterative Deepening Minimax Search
        # If no immediate win/loss, search deeper.
        best_move = empties[0]
        
        # Sort empties by positional heuristic to improve Alpha-Beta pruning efficiency
        empties.sort(key=lambda x: self.pos_weights[x], reverse=True)
        
        try:
            # Start at depth 2 (Depth 1 is essentially covered by logic above)
            # Max depth 25, but time will likely cut off around depth 4-6.
            for depth in range(2, 25): 
                if time.time() - start_time > time_limit:
                    break
                
                # Run Minimax
                score, move = self.minimax(search_board, depth, -9999999, 9999999, True, start_time, time_limit)
                
                if move is not None:
                    best_move = move
                
                # If we found a forced win path, stop searching to save time/resources
                # Score > 80000 indicates a winning path found
                if score > 80000:
                    break
                    
        except TimeoutError:
            # If search times out, return the best move found in the last completed depth
            pass
            
        return best_move

    def check_win_fast(self, board, last_move, player):
        """
        Checks if the move just made at `last_move` created a win for `player`.
        Only checks lines involving `last_move` for efficiency.
        """
        for a, b, c in self.cell_lines[last_move]:
            if board[a] == player and board[b] == player and board[c] == player:
                return True
        return False

    def evaluate(self, board):
        """
        Heuristic evaluation of a non-terminal board state.
        Higher score = better for self.
        """
        score = 0
        
        # Iterate through all possible winning lines to assess threats and potentials
        for a, b, c in self.win_lines:
            va, vb, vc = board[a], board[b], board[c]
            
            us = 0
            them = 0
            
            if va == self.symbol: us += 1
            elif va == self.opponent: them += 1
            
            if vb == self.symbol: us += 1
            elif vb == self.opponent: them += 1
            
            if vc == self.symbol: us += 1
            elif vc == self.opponent: them += 1
            
            # Score the line
            if them == 0:
                if us == 2: score += 100  # Strong threat (2 in a row)
                elif us == 1: score += 10 # Potential
            elif us == 0:
                if them == 2: score -= 100 # Opponent threat
                elif them == 1: score -= 10 # Opponent potential
                
        return score

    def minimax(self, board, depth, alpha, beta, is_max, start_time, time_limit):
        """
        Minimax algorithm with Alpha-Beta pruning and timeout detection.
        """
        # Check timeout
        if time.time() - start_time > time_limit:
            raise TimeoutError

        empties = [i for i, x in enumerate(board) if x == ' ']
        
        # Terminal state: Draw
        if not empties:
            return 0, None 

        # Leaf node: Heuristic evaluation
        if depth == 0:
            return self.evaluate(board), None

        best_move = None

        # Move Ordering: Try high-value position moves first to prune tree
        # Using sorted list is fast enough for N<=25
        empties.sort(key=lambda x: self.pos_weights[x], reverse=True)

        if is_max:
            max_eval = -float('inf')
            
            for move in empties:
                board[move] = self.symbol
                
                # Optimization: Check for win immediately after move
                if self.check_win_fast(board, move, self.symbol):
                    board[move] = ' '
                    # Prefer winning sooner (higher depth remaining)
                    return 100000 + depth, move 
                
                eval_val, _ = self.minimax(board, depth - 1, alpha, beta, False, start_time, time_limit)
                board[move] = ' '
                
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            
            if best_move is None: best_move = empties[0]
            return max_eval, best_move
            
        else:
            min_eval = float('inf')
            
            for move in empties:
                board[move] = self.opponent
                
                if self.check_win_fast(board, move, self.opponent):
                    board[move] = ' '
                    # Prefer losing later (lower depth remaining)
                    # Note: score is negative for loss
                    return -100000 - depth, move 
                
                eval_val, _ = self.minimax(board, depth - 1, alpha, beta, True, start_time, time_limit)
                board[move] = ' '
                
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
                    
            if best_move is None: best_move = empties[0]
            return min_eval, best_move
