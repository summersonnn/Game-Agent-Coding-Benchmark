"""
Agent Code: A2-TicTacToe
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-11 21:03:27
"""



import random

class TicTacToeAgent:
    """
    An optimal Tic Tac Toe agent using minimax with alpha-beta pruning and caching.
    Implements perfect play and accounts for tie-breaker scoring (win quickly, lose slowly).
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.cache = {}  # Transposition table for memoization

    def make_move(self, board):
        """Return the index (0-8) of the best move."""
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        if not empty_cells:
            return None
        
        # If only one move available, play it immediately
        if len(empty_cells) == 1:
            return empty_cells[0]
        
        # Use minimax to find optimal move
        _, move = self.minimax(board, -float('inf'), float('inf'), True)
        return move if move is not None else random.choice(empty_cells)

    def minimax(self, board, alpha, beta, maximizing):
        """
        Minimax with alpha-beta pruning.
        Returns (score, best_move) where score is from perspective of self.symbol.
        Scoring: win = +max(empty+1, 3), loss = -max(empty+1, 3), draw = 0.
        """
        board_key = tuple(board)
        if board_key in self.cache:
            return self.cache[board_key]
        
        # Check terminal states
        winner = self.check_winner(board)
        if winner == self.symbol:
            empty = board.count(' ')
            score = max(empty + 1, 3)  # +1 because we count the winning move as made
            return score, None
        elif winner == self.opponent:
            empty = board.count(' ')
            score = -max(empty + 1, 3)
            return score, None
        elif winner == 'DRAW':
            return 0, None
        
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        current_player = self.symbol if maximizing else self.opponent
        
        best_move = None
        if maximizing:
            best_score = -float('inf')
            for move in empty_cells:
                new_board = board.copy()
                new_board[move] = self.symbol
                score, _ = self.minimax(new_board, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
        else:
            best_score = float('inf')
            for move in empty_cells:
                new_board = board.copy()
                new_board[move] = self.opponent
                score, _ = self.minimax(new_board, alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
        
        self.cache[board_key] = (best_score, best_move)
        return best_score, best_move

    def check_winner(self, board):
        """Return 'X' or 'O' if there's a winner, 'DRAW' if board full with no winner, else None."""
        win_combos = [
            (0,1,2), (3,4,5), (6,7,8),  # rows
            (0,3,6), (1,4,7), (2,5,8),  # columns
            (0,4,8), (2,4,6)             # diagonals
        ]
        for a,b,c in win_combos:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None
