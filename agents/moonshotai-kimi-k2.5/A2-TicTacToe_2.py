"""
Agent Code: A2-TicTacToe
Model: moonshotai/kimi-k2.5
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
        # Precompute all winning lines (tuples of 3 indices)
        self.lines = []
        # Rows: 5 rows, 3 possible horizontal triplets per row
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.lines.append((start, start + 1, start + 2))
        # Cols: 5 cols, 3 possible vertical triplets per col
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.lines.append((start, start + 5, start + 10))
        # Diagonals down-right: 3x3 grid of starting positions
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.lines.append((start, start + 6, start + 12))
        # Diagonals down-left: 3 rows, cols 2-4
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.lines.append((start, start + 4, start + 8))
    
    def check_winner(self, board, symbol):
        """Check if symbol has won on the given board."""
        for line in self.lines:
            if board[line[0]] == board[line[1]] == board[line[2]] == symbol:
                return True
        return False
    
    def get_valid_moves(self, board):
        """Get list of empty cell indices."""
        return [i for i, cell in enumerate(board) if cell == ' ']
    
    def evaluate(self, board):
        """Heuristic evaluation of board state."""
        # Terminal states
        if self.check_winner(board, self.symbol):
            return 1000
        if self.check_winner(board, self.opponent):
            return -1000
        
        score = 0
        
        # Evaluate threats (2 in a row with open 3rd) and potential threats
        for line in self.lines:
            cells = [board[i] for i in line]
            my_count = cells.count(self.symbol)
            opp_count = cells.count(self.opponent)
            empty_count = cells.count(' ')
            
            if my_count == 2 and empty_count == 1:
                score += 10  # Immediate threat
            elif opp_count == 2 and empty_count == 1:
                score -= 15  # Opponent threat (blocking is urgent)
            elif my_count == 1 and empty_count == 2:
                score += 1   # Potential development
            elif opp_count == 1 and empty_count == 2:
                score -= 1
        
        # Position weights - center and corners are strategically valuable
        weights = [2, 1, 2, 1, 2,
                   1, 3, 3, 3, 1,
                   2, 3, 5, 3, 2,
                   1, 3, 3, 3, 1,
                   2, 1, 2, 1, 2]
        
        for i, cell in enumerate(board):
            if cell == self.symbol:
                score += weights[i]
            elif cell == self.opponent:
                score -= weights[i]
        
        return score
    
    def minimax(self, board, depth, is_maximizing, alpha, beta):
        """Alpha-beta pruning minimax algorithm."""
        # Check terminal states
        if self.check_winner(board, self.symbol):
            return 100 + depth  # Prefer quicker wins
        if self.check_winner(board, self.opponent):
            return -100 - depth  # Prefer longer losses
        if depth == 0:
            return self.evaluate(board)
        
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return 0  # Draw
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in valid_moves:
                board[move] = self.symbol
                eval = self.minimax(board, depth - 1, False, alpha, beta)
                board[move] = ' '
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid_moves:
                board[move] = self.opponent
                eval = self.minimax(board, depth - 1, True, alpha, beta)
                board[move] = ' '
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    def find_fork(self, board, symbol):
        """Find a move that creates two separate winning threats (fork)."""
        valid_moves = self.get_valid_moves(board)
        
        for move in valid_moves:
            threat_count = 0
            board[move] = symbol
            
            # Count threats created by this move
            for line in self.lines:
                if move in line:
                    cells = [board[i] for i in line]
                    if cells.count(symbol) == 2 and cells.count(' ') == 1:
                        threat_count += 1
            
            board[move] = ' '
            
            if threat_count >= 2:
                return move
        
        return None
    
    def make_move(self, board):
        """Determine the best move using strategic rules and minimax."""
        valid_moves = self.get_valid_moves(board)
        
        if not valid_moves:
            return None
        
        # 1. Win immediately if possible
        for move in valid_moves:
            board[move] = self.symbol
            wins = self.check_winner(board, self.symbol)
            board[move] = ' '
            if wins:
                return move
        
        # 2. Block opponent's immediate win
        for move in valid_moves:
            board[move] = self.opponent
            opp_wins = self.check_winner(board, self.opponent)
            board[move] = ' '
            if opp_wins:
                return move
        
        # 3. Create a fork (two threats) if possible
        fork = self.find_fork(board, self.symbol)
        if fork is not None:
            return fork
        
        # 4. Block opponent's fork
        opp_fork = self.find_fork(board, self.opponent)
        if opp_fork is not None:
            return opp_fork
        
        # 5. Use minimax with alpha-beta pruning for deeper evaluation
        # Adjust depth based on game phase for performance
        move_count = 25 - len(valid_moves)
        if len(valid_moves) <= 10:
            depth = 4
        elif len(valid_moves) <= 16:
            depth = 3
        else:
            depth = 2
        
        best_move = valid_moves[0]
        best_score = float('-inf')
        
        # Move ordering: prioritize center, then corners for better pruning
        center = 12
        corners = [0, 4, 20, 24]
        
        def move_priority(m):
            if m == center:
                return 100
            if m in corners:
                return 50
            return 0
        
        sorted_moves = sorted(valid_moves, key=move_priority, reverse=True)
        
        for move in sorted_moves:
            board[move] = self.symbol
            score = self.minimax(board, depth - 1, False, float('-inf'), float('inf'))
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
