"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-5@preset/fp8
Run: 2
Generated: 2026-02-11 21:23:38
"""



class TicTacToeAgent:
    """
    An optimal Tic Tac Toe agent using the Minimax algorithm with Alpha-Beta pruning.
    It is designed to never lose and to win as early as possible to maximize the tie-breaker score.
    """

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        # All possible winning lines (rows, columns, diagonals)
        self.win_lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]

    def check_winner(self, board):
        """
        Checks the board state for a winner or a draw.
        Returns:
            'X' or 'O': The winner.
            'DRAW': If the board is full with no winner.
            None: If the game is still ongoing.
        """
        for a, b, c in self.win_lines:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def minimax(self, board, depth, is_maximizing, alpha, beta):
        """
        Recursive Minimax algorithm with Alpha-Beta pruning.
        Returns a score for the current board state.
        Scores are adjusted by depth to prioritize faster wins and slower losses.
        """
        winner = self.check_winner(board)
        
        if winner == self.symbol:
            # Positive score: higher for wins achieved earlier (smaller depth)
            return 10 - depth
        elif winner == self.opponent:
            # Negative score: higher (less negative) for losses delayed (larger depth)
            return depth - 10
        elif winner == 'DRAW':
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    best_score = max(score, best_score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    score = self.minimax(board, depth + 1, True, alpha, beta)
                    board[i] = ' '
                    best_score = min(score, best_score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
            return best_score

    def make_move(self, board):
        """
        Determines the best move for the current board state.
        """
        # Optimization: If board is empty, take the center (strongest position).
        # This avoids unnecessary computation for the first move.
        if board.count(' ') == 9:
            return 4

        best_move = -1
        best_score = -float('inf')
        
        # Iterate through all available moves to find the one with the highest minimax score
        for i in range(9):
            if board[i] == ' ':
                board[i] = self.symbol
                score = self.minimax(board, 0, False, -float('inf'), float('inf'))
                board[i] = ' '
                
                if score > best_score:
                    best_score = score
                    best_move = i
                    
        return best_move
