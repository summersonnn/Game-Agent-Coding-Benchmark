"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-13 14:10:12
"""



class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'R' if symbol == 'Y' else 'Y'
        self.lines = self._generate_winning_lines()
    
    def _generate_winning_lines(self):
        """Precompute all 69 possible winning lines (horizontal, vertical, diagonal)."""
        lines = []
        # Horizontal
        for r in range(6):
            for c in range(4):
                lines.append([(r, c+i) for i in range(4)])
        # Vertical
        for r in range(3):
            for c in range(7):
                lines.append([(r+i, c) for i in range(4)])
        # Diagonal (down-right)
        for r in range(3):
            for c in range(4):
                lines.append([(r+i, c+i) for i in range(4)])
        # Diagonal (up-right)
        for r in range(3, 6):
            for c in range(4):
                lines.append([(r-i, c+i) for i in range(4)])
        return lines

    def _simulate_move(self, board, col, symbol):
        """Return new board state after dropping symbol in col (assumes valid move)."""
        new_board = [row[:] for row in board]
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = symbol
                break
        return new_board

    def _is_winning_move(self, board, col, symbol):
        """Check if dropping symbol in col creates a win (optimized for single move)."""
        # Find drop row
        row = None
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                row = r
                break
        if row is None:
            return False
        
        # Check horizontal
        count = 1
        c = col - 1
        while c >= 0 and board[row][c] == symbol:
            count += 1
            c -= 1
        c = col + 1
        while c < 7 and board[row][c] == symbol:
            count += 1
            c += 1
        if count >= 4:
            return True
        
        # Check vertical
        count = 1
        r = row - 1
        while r >= 0 and board[r][col] == symbol:
            count += 1
            r -= 1
        if count >= 4:
            return True
        
        # Check diagonal \
        count = 1
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and board[r][c] == symbol:
            count += 1
            r -= 1
            c -= 1
        r, c = row + 1, col + 1
        while r < 6 and c < 7 and board[r][c] == symbol:
            count += 1
            r += 1
            c += 1
        if count >= 4:
            return True
        
        # Check diagonal /
        count = 1
        r, c = row - 1, col + 1
        while r >= 0 and c < 7 and board[r][c] == symbol:
            count += 1
            r -= 1
            c += 1
        r, c = row + 1, col - 1
        while r < 6 and c >= 0 and board[r][c] == symbol:
            count += 1
            r += 1
            c -= 1
        if count >= 4:
            return True
        
        return False

    def _evaluate_board(self, board):
        """Score threat patterns: 200 for own open-3-thr, -100 for opponent's."""
        score = 0
        for line in self.lines:
            cells = [board[r][c] for r, c in line]
            empty = cells.count(' ')
            own = cells.count(self.symbol)
            opp = cells.count(self.opponent)
            
            # Skip mixed lines (can't form open threats)
            if own > 0 and opp > 0:
                continue
            
            if own == 3 and empty == 1:
                score += 200
            elif own == 2 and empty == 2:
                score += 20
            elif opp == 3 and empty == 1:
                score -= 100
            elif opp == 2 and empty == 2:
                score -= 10
        return score

    def make_move(self, board):
        """Decide next move using threat evaluation and center prioritization."""
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        if not valid_cols:
            return 0  # Should not occur per rules

        # 1. IMMEDIATE WIN CHECK: Prefer winning moves
        for col in valid_cols:
            if self._is_winning_move(board, col, self.symbol):
                return col

        # 2. URGENT BLOCK CHECK: Block any opponent winning opportunity
        for col in valid_cols:
            if self._is_winning_move(board, col, self.opponent):
                return col

        # 3. EVALUATE VALID MOVES
        best_score = -float('inf')
        best_col = valid_cols[0]
        for col in valid_cols:
            new_board = self._simulate_move(board, col, self.symbol)
            # Evaluate board state after move
            threat_score = self._evaluate_board(new_board)
            # Center bonus: 10 for center, decreasing outward
            center_bonus = 10 - abs(col - 3)
            total_score = threat_score + center_bonus
            
            # Prefer higher score, break ties by center proximity
            if total_score > best_score:
                best_score = total_score
                best_col = col
        
        return best_col
