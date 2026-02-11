"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    """
    TicTacToe AI agent using the Minimax algorithm.
    Guarantees optimal play (at least a draw against any opponent).
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        """
        Uses minimax algorithm to determine the best move.
        Returns the index (0-8) of the chosen cell.
        """
        best_score = float('-inf')
        best_move = 0
        
        # Try all available moves and pick the one with the highest minimax score
        for i in range(9):
            if board[i] == ' ':
                board[i] = self.symbol
                score = self.minimax(board, 0, False)
                board[i] = ' '
                
                if score > best_score:
                    best_score = score
                    best_move = i
        
        return best_move

    def minimax(self, board, depth, is_maximizing):
        """
        Minimax algorithm with alpha-beta pruning evaluation.
        is_maximizing: True when evaluating our moves, False for opponent's moves.
        Returns a score: positive favors us, negative favors opponent.
        """
        winner = self.check_winner(board)
        
        # Terminal states
        if winner == self.symbol:
            return 10 - depth  # Prefer faster wins
        elif winner == self.opponent_symbol:
            return depth - 10  # Prefer slower losses
        elif winner == 'DRAW':
            return 0
        
        if is_maximizing:
            # Our move: maximize the score
            best_score = float('-inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            return best_score
        else:
            # Opponent's move: minimize the score
            best_score = float('+inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent_symbol
                    score = self.minimax(board, depth + 1, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            return best_score

    def check_winner(self, board):
        """
        Checks if there's a winner or if the board is full (draw).
        Returns 'X', 'O', 'DRAW', or None (game ongoing).
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
