"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'


class TicTacToeAgent:
    """
    AI agent for 5x5 Tic Tac Toe with strategic threat detection and positioning.
    
    Strategy:
    1. Win immediately if possible (2 in a row with 1 empty)
    2. Block opponent from winning
    3. Play strongest strategic position based on control and center advantage
    """
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = O_MARK if symbol == X_MARK else X_MARK
        self.winning_combos = self._build_winning_combos()

    def _build_winning_combos(self):
        """Build all possible 3-in-a-row combinations on the 5x5 board."""
        combos = []
        
        # Horizontal (3 in a row)
        for row in range(5):
            for col in range(3):
                idx = row * 5 + col
                combos.append((idx, idx + 1, idx + 2))
        
        # Vertical (3 down a column)
        for col in range(5):
            for row in range(3):
                idx = row * 5 + col
                combos.append((idx, idx + 5, idx + 10))
        
        # Diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(3):
                idx = row * 5 + col
                combos.append((idx, idx + 6, idx + 12))
        
        # Diagonal (top-right to bottom-left)
        for row in range(3):
            for col in range(2, 5):
                idx = row * 5 + col
                combos.append((idx, idx + 4, idx + 8))
        
        return combos

    def _get_empty_moves(self, board):
        """Return list of empty cell indices."""
        return [i for i, cell in enumerate(board) if cell == EMPTY]

    def _find_threats(self, board, symbol):
        """Find positions where symbol has 2-in-a-row (winning/blocking opportunities)."""
        threat_count = {}
        
        for combo in self.winning_combos:
            values = [board[idx] for idx in combo]
            
            # Check if symbol has exactly 2 in this combo with 1 empty
            if values.count(symbol) == 2 and values.count(EMPTY) == 1:
                empty_idx = next(idx for idx in combo if board[idx] == EMPTY)
                threat_count[empty_idx] = threat_count.get(empty_idx, 0) + 1
        
        return threat_count

    def _evaluate_position(self, board, position):
        """Score a position based on strategic value and control."""
        score = 0
        
        # Evaluate contribution to all winning combos
        for combo in self.winning_combos:
            if position not in combo:
                continue
            
            values = [board[idx] for idx in combo]
            my_count = values.count(self.symbol)
            opp_count = values.count(self.opponent)
            
            # Only value combos opponent hasn't dominated
            if opp_count == 0:
                # Pure offensive potential - strongly favor building our lines
                score += my_count * 100
            elif my_count == 0:
                # Defensive value - prevent opponent from dominating
                score += opp_count * 25
        
        # Positional bonuses (prioritize center control)
        position_bonus = {
            12: 150,  # Center - maximum combinations
            7: 80, 8: 80, 11: 80, 13: 80, 17: 80, 18: 80,  # Near-center
            6: 40, 9: 40, 16: 40, 19: 40,  # Mid-edges
            1: 30, 3: 30, 5: 30, 15: 30, 21: 30, 23: 30,  # Edge centers
            0: 20, 4: 20, 20: 20, 24: 20,  # Corners
        }
        score += position_bonus.get(position, 10)
        
        return score

    def make_move(self, board):
        """
        Determine best move with priority:
        1. Win immediately (2 in a row)
        2. Block opponent from winning
        3. Strongest strategic position
        """
        empty_moves = self._get_empty_moves(board)
        
        if not empty_moves:
            return None
        
        # Priority 1: Win if possible
        winning_threats = self._find_threats(board, self.symbol)
        if winning_threats:
            return max(winning_threats.keys(), key=lambda m: winning_threats[m])
        
        # Priority 2: Block opponent from winning
        blocking_threats = self._find_threats(board, self.opponent)
        if blocking_threats:
            return max(blocking_threats.keys(), key=lambda m: blocking_threats[m])
        
        # Priority 3: Play strongest position
        return max(empty_moves, key=lambda pos: self._evaluate_position(board, pos))
