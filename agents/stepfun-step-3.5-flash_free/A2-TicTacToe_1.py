"""
Agent Code: A2-TicTacToe
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-13 15:25:40
"""



import random

class TicTacToeAgent:
    """
    A strategic Tic Tac Toe agent for 5x5 board with 3-in-a-row win condition.
    Uses a prioritized approach: win > block > center control > fork creation > heuristic evaluation.
    """
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
        # Precompute all winning triplets (3-in-a-row) for 5x5 board
        self.win_combinations = []
        # Rows (5 rows × 3 positions each)
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_combinations.append((start, start + 1, start + 2))
        # Columns (5 columns × 3 positions each)
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_combinations.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_combinations.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_combinations.append((start, start + 4, start + 8))
    
    def make_move(self, board):
        """Return optimal move index (0-24) for current board state."""
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return 0  # Should not happen, but fallback
        
        # 1. Check for immediate winning move
        for move in available_moves:
            if self._would_win(board, move, self.symbol):
                return move
        
        # 2. Block opponent's immediate win
        for move in available_moves:
            if self._would_win(board, move, self.opponent):
                return move
        
        # 3. Take center if available (index 12)
        if 12 in available_moves:
            return 12
        
        # 4. Create a fork (two simultaneous threats) if possible
        fork_move = self._find_fork_move(board, self.symbol)
        if fork_move is not None:
            return fork_move
        
        # 5. Block opponent's fork potential
        block_fork = self._find_fork_move(board, self.opponent)
        if block_fork is not None:
            return block_fork
        
        # 6. Strategic position evaluation
        return self._evaluate_positions(board, available_moves)
    
    def _would_win(self, board, move, symbol):
        """Check if placing 'symbol' at 'move' would complete a 3-in-a-row."""
        # Temporarily place symbol
        original = board[move]
        board[move] = symbol
        won = False
        for combo in self.win_combinations:
            a, b, c = combo
            if board[a] == board[b] == board[c] == symbol:
                won = True
                break
        board[move] = original
        return won
    
    def _count_threats(self, board, move, symbol):
        """
        Count threat potential for a move.
        Returns (immediate_threat, potential_threat) where:
        - immediate_threat: number of winning combos that would have 2 of 'symbol' + empty after move
        - potential_threat: number of combos that would have 1 of 'symbol' + 2 empties after move
        """
        immediate = 0
        potential = 0
        
        for combo in self.win_combinations:
            if move not in combo:
                continue
                
            counts = {self.symbol: 0, self.opponent: 0, ' ': 0}
            for idx in combo:
                if idx == move:
                    counts[symbol] += 1  # simulate placing symbol here
                else:
                    counts[board[idx]] += 1
            
            # Only consider combos not blocked by opponent
            if counts[self.opponent] > 0:
                continue
                
            if counts[symbol] == 2 and counts[' '] == 1:
                immediate += 1
            elif counts[symbol] == 1 and counts[' '] == 2:
                potential += 1
                
        return immediate, potential
    
    def _find_fork_move(self, board, symbol):
        """
        Find a move that creates two or more immediate threats (fork).
        Returns move index or None if no fork available.
        """
        best_move = None
        best_threat_count = 0
        
        for move in [i for i, spot in enumerate(board) if spot == ' ']:
            immediate, _ = self._count_threats(board, move, symbol)
            if immediate > best_threat_count:
                best_threat_count = immediate
                best_move = move
                
        return best_move if best_threat_count >= 2 else None
    
    def _evaluate_positions(self, board, available_moves):
        """
        Evaluate each available move using a weighted heuristic:
        - Center (12) has highest base value
        - Corners (0,4,20,24) next
        - Edge centers (2,10,14,22) next
        - Others lowest
        Plus threat potential from _count_threats
        """
        # Position weights (based on number of winning combos they participate in)
        position_weights = {
            12: 12,   # center (most combos)
            # Corners
            0: 3, 4: 3, 20: 3, 24: 3,
            # Edge centers (middle of each edge)
            2: 6, 10: 6, 14: 6, 22: 6,
            # Other edge positions
            1: 4, 3: 4, 5: 4, 9: 4, 15: 4, 19: 4, 21: 4, 23: 4,
            # Inner positions (not center)
            6: 4, 7: 4, 8: 4, 11: 4, 13: 4, 16: 4, 17: 4, 18: 4
        }
        
        best_score = -float('inf')
        best_moves = []
        
        for move in available_moves:
            score = position_weights.get(move, 1)
            immediate, potential = self._count_threats(board, move, self.symbol)
            score += immediate * 50 + potential * 10
            
            # Also consider blocking opponent's immediate threats (already handled above, but double-check)
            opp_immediate, _ = self._count_threats(board, move, self.opponent)
            if opp_immediate > 0:
                score += 30  # Bonus for blocking opponent's threat
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        
        return random.choice(best_moves)
