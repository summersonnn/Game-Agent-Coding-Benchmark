"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-sonnet-4.5
Run: 2
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    """
    Minimax-based TicTacToe agent with alpha-beta pruning for optimal play.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
    
    def make_move(self, board):
        """
        Returns the optimal move using minimax algorithm with alpha-beta pruning.
        """
        best_score = float('-inf')
        best_move = None
        
        # Prioritize center, corners, then edges for better alpha-beta pruning
        move_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        
        for i in move_order:
            if board[i] == ' ':
                board_copy = board[:]
                board_copy[i] = self.symbol
                score = self.minimax(board_copy, 0, False, float('-inf'), float('inf'))
                if score > best_score:
                    best_score = score
                    best_move = i
                if best_score >= 10:  # Found a winning move, no need to search further
                    break
        
        # Fallback to first available move
        if best_move is None:
            for i in range(9):
                if board[i] == ' ':
                    return i
        
        return best_move
    
    def minimax(self, board, depth, is_maximizing, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning.
        Returns score: positive for favorable positions, negative for unfavorable.
        """
        winner = self.check_winner(board)
        
        if winner == self.symbol:
            return 10 - depth  # Prefer faster wins
        elif winner == self.opponent:
            return depth - 10  # Prefer slower losses
        elif winner == 'DRAW':
            return 0
        
        if is_maximizing:
            best_score = float('-inf')
            for i in range(9):
                if board[i] == ' ':
                    board_copy = board[:]
                    board_copy[i] = self.symbol
                    score = self.minimax(board_copy, depth + 1, False, alpha, beta)
                    best_score = max(score, best_score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break  # Beta cutoff
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board_copy = board[:]
                    board_copy[i] = self.opponent
                    score = self.minimax(board_copy, depth + 1, True, alpha, beta)
                    best_score = min(score, best_score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break  # Alpha cutoff
            return best_score
    
    def check_winner(self, board):
        """
        Check if there's a winner or draw.
        Returns 'X', 'O', 'DRAW', or None.
        """
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
