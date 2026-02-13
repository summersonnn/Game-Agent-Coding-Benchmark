"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder-next@preset/fp8
Run: 1
Generated: 2026-02-13 14:53:21
"""

from copy import deepcopy

import random
from copy import deepcopy

EMPTY = ' '

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'

    def make_move(self, board):
        try:
            # Get all available moves
            available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
            if not available_moves:
                return None
                
            # If it's the first move of the game (only one empty spot occupied by random X),
            # we want to play smart from our first actual move onward
            # But we need to handle the case where X's first move was random
            
            # Use minimax with alpha-beta pruning for better strategy
            best_move = self.minimax(board, self.symbol, -float('inf'), float('inf'), True)[1]
            
            # If minimax returns None or invalid, fallback to center or corner preferences
            if best_move is None or board[best_move] != EMPTY:
                # Try center (12), then corners (0, 4, 20, 24), then edges
                preferred_moves = [12, 0, 4, 20, 24, 1, 3, 5, 9, 10, 14, 15, 19, 21, 23, 2, 8, 16, 18]
                for move in preferred_moves:
                    if move in available_moves:
                        return move
                
                # Final fallback: random available move
                return random.choice(available_moves)
                
            return best_move
        except Exception:
            # On any error, fallback to random valid move
            available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
            return random.choice(available_moves) if available_moves else None

    def minimax(self, board, player, alpha, beta, is_maximizing):
        # Check for terminal states
        winner = self.check_winner(board)
        if winner == self.symbol:
            return (1000000, None)  # Win for our symbol
        elif winner == ('O' if self.symbol == 'X' else 'X'):
            return (-1000000, None)  # Loss for our symbol
        elif winner == 'DRAW':
            return (0, None)  # Draw

        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return (0, None)

        # Determine opponent symbol
        opponent = 'O' if player == 'X' else 'X'

        if is_maximizing:
            max_eval = -float('inf')
            best_move = None
            
            # Order moves by heuristic to improve pruning (center first)
            ordered_moves = sorted(available_moves, key=lambda m: self.move_heuristic(board, m))
            
            for move in ordered_moves:
                new_board = board.copy()
                new_board[move] = player
                eval_score = self.minimax(new_board, opponent, alpha, beta, False)[0]
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                    
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
                    
            return (max_eval, best_move)
        else:
            min_eval = float('inf')
            best_move = None
            
            # Order moves by heuristic to improve pruning (center first)
            ordered_moves = sorted(available_moves, key=lambda m: self.move_heuristic(board, m))
            
            for move in ordered_moves:
                new_board = board.copy()
                new_board[move] = player
                eval_score = self.minimax(new_board, self.symbol, alpha, beta, True)[0]
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                    
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
                    
            return (min_eval, best_move)

    def check_winner(self, board):
        win_conditions = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                win_conditions.append((start, start + 4, start + 8))

        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        if EMPTY not in board:
            return 'DRAW'
        return None

    def move_heuristic(self, board, move):
        # Prioritize center, corners, then edges
        if move == 12:
            return 0  # Highest priority
        elif move in [0, 4, 20, 24]:
            return 1  # Second priority
        elif move in [1, 3, 5, 9, 10, 14, 15, 19, 21, 23]:
            return 2  # Third priority
        else:
            return 3  # Remaining positions
