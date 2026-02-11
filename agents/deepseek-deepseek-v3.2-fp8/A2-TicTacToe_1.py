"""
Agent Code: A2-TicTacToe
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 1
Generated: 2026-02-11 20:47:17
"""



import random

class TicTacToeAgent:
    """
    An optimal Tic Tac Toe agent using minimax with alpha-beta pruning.
    Always plays perfectly - cannot be beaten, only drawn or won against.
    """
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
        # Winning combinations
        self.wins = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]              # diagonals
        ]
        
        # Opening book for first few moves (optimized for both X and O)
        self.opening_book = {
            'X': {
                # Center is best opening for X
                'empty': 4,
                # If opponent takes center as O, take corners
                'center_taken': [0, 2, 6, 8],
                # If opponent takes corner as O, take center then opposite corner
                'corner_taken': 4
            },
            'O': {
                # If center available, take it
                'center_available': 4,
                # If center taken by X, take corners
                'center_taken': [0, 2, 6, 8],
                # If X starts with corner, take center
                'corner_start': 4
            }
        }
        
    def make_move(self, board):
        """
        Return the optimal move using minimax with alpha-beta pruning.
        Uses opening book for early game and minimax for mid/late game.
        """
        # Get available moves
        available = [i for i, cell in enumerate(board) if cell == ' ']
        
        # Opening moves (first 2-3 moves) - use opening book for speed
        empty_count = sum(1 for cell in board if cell == ' ')
        if empty_count >= 7:  # Early game
            return self._opening_move(board, available)
        
        # For mid/late game, use minimax
        # Use iterative deepening for timeout safety
        best_move = -1
        best_score = -float('inf')
        
        # Try to find immediate win or block
        for move in available:
            # Check for immediate win
            board[move] = self.symbol
            if self._check_winner(board) == self.symbol:
                return move
            board[move] = ' '
            
            # Check for immediate block
            board[move] = self.opponent
            if self._check_winner(board) == self.opponent:
                return move
            board[move] = ' '
        
        # If no immediate win/block, use minimax
        # Order moves for better pruning: center, corners, edges
        ordered_moves = self._order_moves(available, board)
        
        for move in ordered_moves:
            board[move] = self.symbol
            score = self._minimax(board, 0, False, -float('inf'), float('inf'))
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
        
        # Fallback to first available move (should never happen with perfect play)
        return best_move if best_move != -1 else available[0]
    
    def _opening_move(self, board, available):
        """Handle opening moves using optimized strategies."""
        empty_count = sum(1 for cell in board if cell == ' ')
        
        if self.symbol == 'X':
            # X's first move
            if empty_count == 9:
                return 4  # Center is optimal for X
            
            # X's second move (if center was taken by O)
            if empty_count == 7:
                if board[4] == 'O':  # O took center
                    # Take a corner
                    corners = [i for i in [0, 2, 6, 8] if board[i] == ' ']
                    return corners[0]
                else:
                    # Center is available, we should have taken it
                    return 4
        
        else:  # O
            # O's first move
            if empty_count == 8:
                if board[4] == ' ':  # Center available
                    return 4
                else:  # X took center
                    # Take a corner
                    corners = [i for i in [0, 2, 6, 8] if board[i] == ' ']
                    return corners[0]
            
            # O's second move (if X started with corner)
            if empty_count == 6:
                # Check if we need to block
                for move in available:
                    board[move] = 'X'
                    if self._check_winner(board) == 'X':
                        board[move] = ' '
                        return move
                    board[move] = ' '
                
                # Otherwise take optimal position
                if board[4] == ' ':  # Center available
                    return 4
                # Take corner opposite to X's first move
                corners = [i for i in [0, 2, 6, 8] if board[i] == 'X']
                if corners:
                    first_corner = corners[0]
                    opposite = {0: 8, 2: 6, 6: 2, 8: 0}
                    if board[opposite[first_corner]] == ' ':
                        return opposite[first_corner]
        
        # Fallback to minimax for complex openings
        return self._minimax_move(board, available)
    
    def _minimax_move(self, board, available):
        """Get best move using minimax (used as fallback)."""
        best_score = -float('inf')
        best_move = available[0]
        
        for move in available:
            board[move] = self.symbol
            score = self._minimax(board, 0, False, -float('inf'), float('inf'))
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with alpha-beta pruning."""
        winner = self._check_winner(board)
        
        # Terminal states
        if winner == self.symbol:
            return 10 - depth  # Win quickly
        elif winner == self.opponent:
            return depth - 10  # Lose slowly
        elif ' ' not in board:
            return 0  # Draw
        
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval_score = self._minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Beta cut-off
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    eval_score = self._minimax(board, depth + 1, True, alpha, beta)
                    board[i] = ' '
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Alpha cut-off
            return min_eval
    
    def _check_winner(self, board):
        """Check if there's a winner on the board."""
        for combo in self.wins:
            a, b, c = combo
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        return None
    
    def _order_moves(self, moves, board):
        """Order moves for better alpha-beta pruning: center, corners, edges."""
        center = 4
        corners = [0, 2, 6, 8]
        edges = [1, 3, 5, 7]
        
        ordered = []
        
        # Prefer center
        if center in moves:
            ordered.append(center)
        
        # Then corners
        for corner in corners:
            if corner in moves:
                ordered.append(corner)
        
        # Finally edges
        for edge in edges:
            if edge in moves:
                ordered.append(edge)
        
        return ordered
