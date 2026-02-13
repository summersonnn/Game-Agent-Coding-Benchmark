"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-sonnet-4.5
Run: 2
Generated: 2026-02-13 14:53:21
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
        # Pre-compute all win conditions (3-in-a-row)
        self.win_conditions = []
        
        # Rows (horizontal)
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 1, start + 2))
        
        # Columns (vertical)
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 5, start + 10))
        
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 6, start + 12))
        
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_conditions.append((start, start + 4, start + 8))
    
    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return 0
        
        # Score all available moves and pick the best
        best_score = -float('inf')
        best_moves = []
        
        for move in available_moves:
            score = self.score_move(board, move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        
        return random.choice(best_moves)
    
    def score_move(self, board, move):
        """Evaluate the strategic value of a move"""
        score = 0
        
        # Priority 1: Win immediately
        if self.is_winning_move(board, move, self.symbol):
            return 1000000
        
        # Priority 2: Block opponent's winning move
        if self.is_winning_move(board, move, self.opponent):
            return 100000
        
        # Simulate making the move
        test_board = board[:]
        test_board[move] = self.symbol
        
        # Priority 3: Create multiple threats (fork)
        our_threats = self.count_threats(test_board, self.symbol)
        if our_threats >= 2:
            score += 10000
        else:
            score += our_threats * 1000
        
        # Priority 4: Block opponent's fork
        opp_test_board = board[:]
        opp_test_board[move] = self.opponent
        opp_threats_if_they_play = self.count_threats(opp_test_board, self.opponent)
        if opp_threats_if_they_play >= 2:
            score += 5000
        
        # Priority 5: Block opponent threats
        original_opp_threats = self.count_threats(board, self.opponent)
        new_opp_threats = self.count_threats(test_board, self.opponent)
        threats_blocked = original_opp_threats - new_opp_threats
        score += threats_blocked * 500
        
        # Priority 6: Prefer center positions (more strategic options)
        if move == 12:  # Center of board
            score += 50
        elif move in [6, 7, 8, 11, 13, 16, 17, 18]:  # Inner 3x3
            score += 25
        
        # Priority 7: Prefer positions involved in more win conditions
        win_conditions_count = sum(1 for combo in self.win_conditions if move in combo)
        score += win_conditions_count * 3
        
        return score
    
    def is_winning_move(self, board, move, player):
        """Check if placing player's mark at move position results in a win"""
        test_board = board[:]
        test_board[move] = player
        
        for combo in self.win_conditions:
            if (test_board[combo[0]] == test_board[combo[1]] == 
                test_board[combo[2]] == player):
                return True
        return False
    
    def count_threats(self, board, player):
        """Count how many 2-in-a-row threats exist for player"""
        threats = 0
        for combo in self.win_conditions:
            cells = [board[combo[0]], board[combo[1]], board[combo[2]]]
            if cells.count(player) == 2 and cells.count(' ') == 1:
                threats += 1
        return threats
