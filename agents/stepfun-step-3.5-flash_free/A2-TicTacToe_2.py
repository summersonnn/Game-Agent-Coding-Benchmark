"""
Agent Code: A2-TicTacToe
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    """
    An optimal Tic Tac Toe agent using minimax with alpha-beta pruning.
    Guarantees at least a draw against any opponent.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        # Win conditions for quick reference
        self.win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]

    def make_move(self, board):
        """Return the optimal move (0-8) for the current board state."""
        available = [i for i, spot in enumerate(board) if spot == ' ']
        if not available:
            return None
        
        # If first move as X, take center if available (slight optimization)
        if board.count(' ') == 9 and self.symbol == 'X':
            return 4
        if board.count(' ') == 8 and self.symbol == 'O' and board[4] == 'X':
            # If X took center, take a corner
            corners = [0, 2, 6, 8]
            for corner in corners:
                if board[corner] == ' ':
                    return corner
        
        # Use minimax with alpha-beta pruning
        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        for move in available:
            new_board = board.copy()
            new_board[move] = self.symbol
            score = self._minimax(new_board, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
                
        return best_move if best_move is not None else random.choice(available)

    def _minimax(self, board, alpha, beta, is_maximizing):
        """Minimax with alpha-beta pruning. Returns score from current player's perspective."""
        result = self._evaluate(board)
        if result is not None:
            return result
            
        if is_maximizing:
            max_score = -float('inf')
            for move in self._get_available_moves(board):
                new_board = board.copy()
                new_board[move] = self.symbol
                score = self._minimax(new_board, alpha, beta, False)
                max_score = max(max_score, score)
                alpha = max(alpha, max_score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = float('inf')
            for move in self._get_available_moves(board):
                new_board = board.copy()
                new_board[move] = self.opponent
                score = self._minimax(new_board, alpha, beta, True)
                min_score = min(min_score, score)
                beta = min(beta, min_score)
                if beta <= alpha:
                    break
            return min_score

    def _evaluate(self, board):
        """Evaluate terminal board. Returns score or None if game continues."""
        # Check for winner
        for a, b, c in self.win_conditions:
            if board[a] == board[b] == board[c] != ' ':
                if board[a] == self.symbol:
                    # Agent wins: prefer winning quickly (more empty cells)
                    empty = board.count(' ')
                    return 10 + max(empty, 3)
                else:
                    # Opponent wins: prefer losing slowly (fewer empty cells)
                    empty = board.count(' ')
                    return -10 - max(empty, 3)
        
        # Check for draw
        if ' ' not in board:
            return 0
            
        return None  # Game continues

    def _get_available_moves(self, board):
        """Return list of empty cell indices."""
        return [i for i, spot in enumerate(board) if spot == ' ']
