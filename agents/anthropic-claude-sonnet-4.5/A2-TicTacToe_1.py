"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-sonnet-4.5
Run: 1
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
    def make_move(self, board):
        """Use minimax with alpha-beta pruning to find the optimal move."""
        best_score = float('-inf')
        best_move = None
        
        for i in range(9):
            if board[i] == ' ':
                # Simulate this move
                board[i] = self.symbol
                score = self.minimax(board, 0, False, float('-inf'), float('inf'))
                board[i] = ' '  # Undo move
                
                if score > best_score:
                    best_score = score
                    best_move = i
        
        return best_move if best_move is not None else 0
    
    def minimax(self, board, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with alpha-beta pruning."""
        winner = self.check_winner(board)
        
        # Terminal states
        if winner == self.symbol:
            return 10 - depth  # Prefer faster wins
        elif winner == self.opponent:
            return depth - 10  # Prefer slower losses
        elif winner == 'DRAW':
            return 0
        
        if is_maximizing:
            max_score = float('-inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    max_score = max(max_score, score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            return max_score
        else:
            min_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    score = self.minimax(board, depth + 1, True, alpha, beta)
                    board[i] = ' '
                    min_score = min(min_score, score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            return min_score
    
    def check_winner(self, board):
        """Check if there's a winner or draw."""
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6),              # Diagonals
        ]
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        if ' ' not in board:
            return 'DRAW'
        return None
