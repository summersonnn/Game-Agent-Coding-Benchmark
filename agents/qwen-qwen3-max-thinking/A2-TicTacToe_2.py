"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-max-thinking
Run: 2
Generated: 2026-02-13 14:53:21
"""


class TicTacToeAgent:
    # Precomputed winning lines (48 total combinations for 3-in-a-row on 5x5)
    WINNING_LINES = [
        # Rows (15 lines: 5 rows × 3 sequences each)
        [0, 1, 2], [1, 2, 3], [2, 3, 4],
        [5, 6, 7], [6, 7, 8], [7, 8, 9],
        [10, 11, 12], [11, 12, 13], [12, 13, 14],
        [15, 16, 17], [16, 17, 18], [17, 18, 19],
        [20, 21, 22], [21, 22, 23], [22, 23, 24],
        # Columns (15 lines: 5 columns × 3 sequences each)
        [0, 5, 10], [5, 10, 15], [10, 15, 20],
        [1, 6, 11], [6, 11, 16], [11, 16, 21],
        [2, 7, 12], [7, 12, 17], [12, 17, 22],
        [3, 8, 13], [8, 13, 18], [13, 18, 23],
        [4, 9, 14], [9, 14, 19], [14, 19, 24],
        # Diagonals down-right (9 lines: 3×3 grid of starting positions)
        [0, 6, 12], [1, 7, 13], [2, 8, 14],
        [5, 11, 17], [6, 12, 18], [7, 13, 19],
        [10, 16, 22], [11, 17, 23], [12, 18, 24],
        # Diagonals down-left (9 lines: 3×3 grid of starting positions)
        [2, 6, 10], [3, 7, 11], [4, 8, 12],
        [7, 11, 15], [8, 12, 16], [9, 13, 17],
        [12, 16, 20], [13, 17, 21], [14, 18, 22]
    ]
    
    # Precomputed: for each cell, indices of lines it belongs to
    CELL_LINES = [[] for _ in range(25)]
    for line_idx, line in enumerate(WINNING_LINES):
        for cell in line:
            CELL_LINES[cell].append(line_idx)
    
    # Precomputed strategic value: number of winning lines each cell participates in
    CELL_VALUES = [0] * 25
    for line in WINNING_LINES:
        for cell in line:
            CELL_VALUES[cell] += 1

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
    
    def make_move(self, board):
        empty_cells = [i for i in range(25) if board[i] == ' ']
        
        # 1. Win immediately if possible
        for cell in empty_cells:
            if self._would_win(board, cell, self.symbol):
                return cell
        
        # 2. Block opponent's immediate win
        for cell in empty_cells:
            if self._would_win(board, cell, self.opponent):
                return cell
        
        # 3. Create a fork (move that creates 2+ winning threats)
        forks = []
        for cell in empty_cells:
            if self._creates_fork(board, cell, self.symbol):
                forks.append(cell)
        if forks:
            return max(forks, key=lambda c: self.CELL_VALUES[c])
        
        # 4. Block opponent's fork threats
        opponent_fork_cells = []
        for cell in empty_cells:
            if self._creates_fork(board, cell, self.opponent):
                opponent_fork_cells.append(cell)
        
        if opponent_fork_cells:
            # Try to block by creating our own threat (forces opponent to respond)
            threat_moves = [c for c in empty_cells if self._creates_threat(board, c, self.symbol)]
            blocking_threats = [c for c in threat_moves if c in opponent_fork_cells]
            if blocking_threats:
                return max(blocking_threats, key=lambda c: self.CELL_VALUES[c])
            # Otherwise block the highest-value fork cell
            return max(opponent_fork_cells, key=lambda c: self.CELL_VALUES[c])
        
        # 5. Create a threat (complete 2-in-a-row with empty third cell)
        threat_moves = [c for c in empty_cells if self._creates_threat(board, c, self.symbol)]
        if threat_moves:
            return max(threat_moves, key=lambda c: self.CELL_VALUES[c])
        
        # 6. Block opponent's threats (prevent their 2-in-a-row completion)
        opponent_threats = [c for c in empty_cells if self._creates_threat(board, c, self.opponent)]
        if opponent_threats:
            return max(opponent_threats, key=lambda c: self.CELL_VALUES[c])
        
        # 7. Take center (highest strategic value cell)
        if 12 in empty_cells:
            return 12
        
        # 8. Default: highest strategic value cell
        return max(empty_cells, key=lambda c: self.CELL_VALUES[c])
    
    def _would_win(self, board, cell, symbol):
        """Check if placing symbol at cell completes a winning line."""
        for line_idx in self.CELL_LINES[cell]:
            line = self.WINNING_LINES[line_idx]
            if board[line[0]] == board[line[1]] == board[line[2]] == symbol:
                return True
        return False
    
    def _creates_threat(self, board, cell, symbol):
        """Check if placing symbol at cell creates a 2-in-a-row with one empty spot."""
        for line_idx in self.CELL_LINES[cell]:
            line = self.WINNING_LINES[line_idx]
            marks = [board[i] for i in line]
            if marks.count(symbol) == 2 and marks.count(' ') == 1:
                return True
        return False
    
    def _creates_fork(self, board, cell, symbol):
        """Check if placing symbol at cell creates 2+ simultaneous winning threats."""
        threat_count = 0
        for line_idx in self.CELL_LINES[cell]:
            line = self.WINNING_LINES[line_idx]
            marks = [board[i] for i in line]
            if marks.count(symbol) == 2 and marks.count(' ') == 1:
                threat_count += 1
                if threat_count >= 2:
                    return True
        return False