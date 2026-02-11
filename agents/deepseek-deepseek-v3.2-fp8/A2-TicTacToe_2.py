"""
Agent Code: A2-TicTacToe
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-11 20:47:17
"""

import math

import random
import math

class TicTacToeAgent:
    """
    A strategic Tic Tac Toe agent using minimax with alpha-beta pruning.
    """
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
    def make_move(self, board):
        """
        Return the optimal move using minimax with alpha-beta pruning.
        """
        # Get all available moves
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        
        # If it's the first move (empty board or almost empty), use opening strategy
        if len(available_moves) >= 8:
            return self._opening_move(board)
        
        # Use minimax with alpha-beta pruning for optimal play
        best_move = -1
        best_score = -math.inf
        
        for move in available_moves:
            # Make the move
            new_board = board.copy()
            new_board[move] = self.symbol
            
            # Calculate score for this move
            score = self._minimax(new_board, 0, False, -math.inf, math.inf)
            
            # Update best move
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning.
        Returns a score for the current board state.
        """
        # Check for terminal states
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 10 - depth  # Win sooner is better
        elif winner == self.opponent:
            return depth - 10  # Lose later is better
        elif not self._has_empty_cells(board):
            return 0  # Draw
        
        if is_maximizing:
            max_score = -math.inf
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self._minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    max_score = max(max_score, score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break  # Beta cutoff
            return max_score
        else:
            min_score = math.inf
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    score = self._minimax(board, depth + 1, True, alpha, beta)
                    board[i] = ' '
                    min_score = min(min_score, score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break  # Alpha cutoff
            return min_score
    
    def _check_winner(self, board):
        """
        Check if there's a winner on the board.
        Returns 'X', 'O', or None.
        """
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] and board[a] != ' ':
                return board[a]
        return None
    
    def _has_empty_cells(self, board):
        """Check if there are any empty cells on the board."""
        return ' ' in board
    
    def _opening_move(self, board):
        """
        Strategic opening moves.
        """
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        
        # If we're X (first player)
        if self.symbol == 'X':
            # Always start with center or corner for optimal play
            if 4 in available_moves:  # Center
                return 4
            # Otherwise choose a corner
            corners = [0, 2, 6, 8]
            valid_corners = [c for c in corners if c in available_moves]
            if valid_corners:
                return random.choice(valid_corners)
        
        # If we're O (second player)
        else:
            # If center is taken, take a corner opposite to X's move
            x_positions = [i for i, spot in enumerate(board) if spot == 'X']
            if len(x_positions) == 1:
                x_move = x_positions[0]
                # If X took center, take a corner
                if x_move == 4:
                    corners = [0, 2, 6, 8]
                    valid_corners = [c for c in corners if c in available_moves]
                    if valid_corners:
                        return random.choice(valid_corners)
                # If X took a corner, take center or opposite corner
                elif x_move in [0, 2, 6, 8]:
                    if 4 in available_moves:
                        return 4
                    # Take opposite corner
                    opposite_corners = {0: 8, 2: 6, 6: 2, 8: 0}
                    opposite = opposite_corners.get(x_move)
                    if opposite in available_moves:
                        return opposite
        
        # Fallback: choose randomly among available moves
        return random.choice(available_moves)
