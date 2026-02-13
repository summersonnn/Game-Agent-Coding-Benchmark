"""
Agent Code: A2-TicTacToe
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.lines = self._generate_lines()
        # Precompute which lines contain each cell for faster lookup
        self.cell_to_lines = [[] for _ in range(25)]
        for i, line in enumerate(self.lines):
            for cell in line:
                self.cell_to_lines[cell].append(i)
        
    def _generate_lines(self):
        """Generate all possible winning lines (3-in-a-row) on 5x5 board."""
        lines = []
        # Horizontal lines: 5 rows × 3 positions per row
        for r in range(5):
            base = r * 5
            for c in range(3):
                lines.append([base + c, base + c + 1, base + c + 2])
        # Vertical lines: 5 cols × 3 positions per col
        for c in range(5):
            for r in range(3):
                lines.append([r * 5 + c, (r + 1) * 5 + c, (r + 2) * 5 + c])
        # Diagonal down-right: 3×3 grid of starting positions
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append([start, start + 6, start + 12])
        # Diagonal down-left: 3×3 grid of starting positions
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append([start, start + 4, start + 8])
        return lines
    
    def _line_status(self, board, line):
        """Analyze a line: returns (my_count, opp_count, empty_count, empty_pos)."""
        my_count = opp_count = empty_count = 0
        empty_pos = None
        for pos in line:
            cell = board[pos]
            if cell == self.symbol:
                my_count += 1
            elif cell == self.opponent:
                opp_count += 1
            else:
                empty_count += 1
                empty_pos = pos
        return my_count, opp_count, empty_count, empty_pos
    
    def make_move(self, board):
        available = [i for i, x in enumerate(board) if x == ' ']
        if not available:
            return None
        
        # Priority 1: Win immediately if possible
        for move in available:
            for line_idx in self.cell_to_lines[move]:
                line = self.lines[line_idx]
                my_c, opp_c, empty_c, empty_p = self._line_status(board, line)
                if my_c == 2 and empty_c == 1 and empty_p == move:
                    return move
        
        # Priority 2: Block opponent's immediate win
        blocks = []
        for move in available:
            for line_idx in self.cell_to_lines[move]:
                line = self.lines[line_idx]
                my_c, opp_c, empty_c, empty_p = self._line_status(board, line)
                if opp_c == 2 and empty_c == 1 and empty_p == move:
                    blocks.append(move)
                    break
        if blocks:
            return blocks[0]
        
        # Priority 3: Create a fork (two separate threats)
        for move in available:
            board[move] = self.symbol
            threat_ends = set()
            for line_idx in self.cell_to_lines[move]:
                line = self.lines[line_idx]
                my_c, opp_c, empty_c, empty_p = self._line_status(board, line)
                if my_c == 2 and empty_c == 1:
                    threat_ends.add(empty_p)
            board[move] = ' '
            if len(threat_ends) >= 2:
                return move
        
        # Priority 4: Block opponent's fork
        opp_forks = []
        for move in available:
            board[move] = self.opponent
            threat_ends = set()
            for line_idx in self.cell_to_lines[move]:
                line = self.lines[line_idx]
                my_c, opp_c, empty_c, empty_p = self._line_status(board, line)
                if opp_c == 2 and empty_c == 1:
                    threat_ends.add(empty_p)
            board[move] = ' '
            if len(threat_ends) >= 2:
                opp_forks.append(move)
        
        if opp_forks:
            # Try to block fork while creating our own threat
            for move in available:
                if move in opp_forks:
                    board[move] = self.symbol
                    creates_threat = False
                    for line_idx in self.cell_to_lines[move]:
                        line = self.lines[line_idx]
                        my_c, opp_c, empty_c, empty_p = self._line_status(board, line)
                        if my_c == 2 and empty_c == 1:
                            creates_threat = True
                            break
                    board[move] = ' '
                    if creates_threat:
                        return move
            return opp_forks[0]
        
        # Priority 5: Heuristic evaluation for remaining moves
        best_score = -float('inf')
        best_move = available[0]
        
        for move in available:
            score = 0
            
            # Simulate our move
            board[move] = self.symbol
            
            # Bonus for creating threats
            for line_idx in self.cell_to_lines[move]:
                line = self.lines[line_idx]
                my_c, opp_c, empty_c, empty_p = self._line_status(board, line)
                if my_c == 2 and empty_c == 1:
                    score += 10  # One threat
            
            board[move] = ' '
            
            # Bonus for blocking opponent threats
            board[move] = self.opponent
            for line_idx in self.cell_to_lines[move]:
                line = self.lines[line_idx]
                my_c, opp_c, empty_c, empty_p = self._line_status(board, line)
                if opp_c == 2 and empty_c == 1:
                    score += 5  # Block opponent threat
                    break
            board[move] = ' '
            
            # Positional bonus: prefer center and cells in many active lines
            r, c = divmod(move, 5)
            # Manhattan distance from center (2,2)
            dist = abs(r - 2) + abs(c - 2)
            score += (4 - dist) * 2
            
            # Bonus for cells that participate in unblocked lines
            for line_idx in self.cell_to_lines[move]:
                line = self.lines[line_idx]
                my_c, opp_c, empty_c, empty_p = self._line_status(board, line)
                if opp_c == 0:  # Line not blocked by opponent
                    score += 1
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
