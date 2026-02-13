"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-sonnet-4.5
Run: 1
Generated: 2026-02-13 14:53:21
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_lines = self._generate_win_lines()
    
    def _generate_win_lines(self):
        """Generate all possible winning combinations (3 in a row)."""
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append([start, start + 1, start + 2])
        # Columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append([start, start + 5, start + 10])
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append([start, start + 6, start + 12])
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append([start, start + 4, start + 8])
        return lines
    
    def make_move(self, board):
        available = [i for i in range(25) if board[i] == ' ']
        if not available:
            return 0
        
        # Priority 1: Win immediately if possible
        win_move = self._find_winning_move(board, self.symbol)
        if win_move is not None:
            return win_move
        
        # Priority 2: Block opponent's winning move
        block_move = self._find_winning_move(board, self.opponent)
        if block_move is not None:
            return block_move
        
        # Priority 3: Create a fork (multiple threats)
        fork_move = self._find_fork_move(board, self.symbol)
        if fork_move is not None:
            return fork_move
        
        # Priority 4: Block opponent's fork
        opponent_fork = self._find_fork_move(board, self.opponent)
        if opponent_fork is not None:
            return opponent_fork
        
        # Priority 5: Make the best strategic move
        return self._find_best_strategic_move(board, available)
    
    def _find_winning_move(self, board, symbol):
        """Find a move that completes 3-in-a-row for the given symbol."""
        for line in self.win_lines:
            cells = [board[i] for i in line]
            if cells.count(symbol) == 2 and cells.count(' ') == 1:
                for i in line:
                    if board[i] == ' ':
                        return i
        return None
    
    def _find_fork_move(self, board, symbol):
        """Find a move that creates two or more winning threats."""
        for move in range(25):
            if board[move] != ' ':
                continue
            
            # Simulate the move
            test_board = board[:]
            test_board[move] = symbol
            
            # Count how many winning threats this creates
            threats = 0
            for line in self.win_lines:
                cells = [test_board[i] for i in line]
                # A threat is 2 of our symbols with 1 empty
                if cells.count(symbol) == 2 and cells.count(' ') == 1:
                    threats += 1
            
            # Fork = 2 or more threats
            if threats >= 2:
                return move
        
        return None
    
    def _find_best_strategic_move(self, board, available):
        """Evaluate all available moves and choose the best one."""
        best_score = -999999
        best_moves = []
        
        for move in available:
            score = self._evaluate_move(board, move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        
        return random.choice(best_moves) if best_moves else available[0]
    
    def _evaluate_move(self, board, move):
        """Score a move based on strategic value."""
        score = 0
        test_board = board[:]
        test_board[move] = self.symbol
        
        # Analyze impact on all winning lines
        for line in self.win_lines:
            if move not in line:
                continue
            
            orig_cells = [board[i] for i in line]
            new_cells = [test_board[i] for i in line]
            
            # Reward creating threats (2 in a row)
            if new_cells.count(self.symbol) == 2 and new_cells.count(' ') == 1:
                score += 50
            # Reward building potential (1 in a row with 2 empty)
            elif new_cells.count(self.symbol) == 1 and new_cells.count(' ') == 2:
                score += 10
            
            # Reward blocking opponent's threats
            if orig_cells.count(self.opponent) == 2 and orig_cells.count(' ') == 1:
                score += 40
            elif orig_cells.count(self.opponent) == 1 and orig_cells.count(' ') == 2:
                score += 5
        
        # Positional bonuses
        if move == 12:  # Center position
            score += 15
        
        # Favor positions closer to center
        row, col = move // 5, move % 5
        center_distance = abs(row - 2) + abs(col - 2)
        score += (4 - center_distance) * 3
        
        return score
