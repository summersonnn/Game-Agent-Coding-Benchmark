"""
Agent Code: A2-TicTacToe
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 2
Generated: 2026-02-17 13:30:08
"""

import math

import random
import math

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        
        # Precompute all possible winning triplets (3 in a row) on 5x5 board
        self.winning_triplets = self._generate_winning_triplets()
        
    def _generate_winning_triplets(self):
        """Generate all possible 3-in-a-row positions on 5x5 board"""
        triplets = []
        
        # Horizontal triplets
        for row in range(5):
            for col in range(3):
                start = row * 5 + col
                triplets.append((start, start + 1, start + 2))
        
        # Vertical triplets
        for col in range(5):
            for row in range(3):
                start = row * 5 + col
                triplets.append((start, start + 5, start + 10))
        
        # Diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(3):
                start = row * 5 + col
                triplets.append((start, start + 6, start + 12))
        
        # Diagonal (top-right to bottom-left)
        for row in range(3):
            for col in range(2, 5):
                start = row * 5 + col
                triplets.append((start, start + 4, start + 8))
        
        return triplets
    
    def _check_win(self, board, player):
        """Check if player has won on the given board"""
        for triplet in self.winning_triplets:
            if all(board[i] == player for i in triplet):
                return True
        return False
    
    def _get_empty_cells(self, board):
        """Return list of indices of empty cells"""
        return [i for i, cell in enumerate(board) if cell == ' ']
    
    def _evaluate_position(self, board, player):
        """Evaluate the board position for the given player"""
        score = 0
        opponent = 'O' if player == 'X' else 'X'
        
        # Check all winning triplets
        for triplet in self.winning_triplets:
            cells = [board[i] for i in triplet]
            player_count = cells.count(player)
            opponent_count = cells.count(opponent)
            empty_count = cells.count(' ')
            
            if player_count == 3:
                score += 1000  # Winning move
            elif player_count == 2 and empty_count == 1:
                score += 100   # Two in a row
            elif player_count == 1 and empty_count == 2:
                score += 10    # One in a row
                
            if opponent_count == 2 and empty_count == 1:
                score -= 150   # Block opponent's two in a row
            elif opponent_count == 1 and empty_count == 2:
                score -= 5     # Minor opponent threat
        
        # Center control (positions 6,7,8,11,12,13,16,17,18)
        center_positions = [6,7,8,11,12,13,16,17,18]
        for pos in center_positions:
            if board[pos] == player:
                score += 2
            elif board[pos] == opponent:
                score -= 2
        
        # Corner control (positions 0,4,20,24)
        corner_positions = [0,4,20,24]
        for pos in corner_positions:
            if board[pos] == player:
                score += 1
            elif board[pos] == opponent:
                score -= 1
        
        return score
    
    def _minimax(self, board, depth, is_maximizing, alpha, beta, player):
        """Minimax algorithm with alpha-beta pruning"""
        # Check terminal states
        if self._check_win(board, self.symbol):
            return 1000, None
        if self._check_win(board, self.opponent_symbol):
            return -1000, None
        
        empty_cells = self._get_empty_cells(board)
        if not empty_cells or depth == 0:
            return self._evaluate_position(board, player), None
        
        if is_maximizing:
            best_score = -math.inf
            best_move = None
            for move in empty_cells:
                new_board = board[:]
                new_board[move] = player
                score, _ = self._minimax(new_board, depth - 1, False, alpha, beta, 
                                        self.opponent_symbol if player == self.symbol else self.symbol)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move
        else:
            best_score = math.inf
            best_move = None
            for move in empty_cells:
                new_board = board[:]
                new_board[move] = player
                score, _ = self._minimax(new_board, depth - 1, True, alpha, beta,
                                        self.opponent_symbol if player == self.symbol else self.symbol)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move
    
    def make_move(self, board):
        """Make a move using a combination of strategies"""
        empty_cells = self._get_empty_cells(board)
        
        # If only one move left, take it
        if len(empty_cells) == 1:
            return empty_cells[0]
        
        # Check for immediate win
        for move in empty_cells:
            test_board = board[:]
            test_board[move] = self.symbol
            if self._check_win(test_board, self.symbol):
                return move
        
        # Check for immediate block (opponent can win next move)
        for move in empty_cells:
            test_board = board[:]
            test_board[move] = self.opponent_symbol
            if self._check_win(test_board, self.opponent_symbol):
                return move
        
        # Use minimax for deeper analysis
        # Adjust depth based on number of empty cells to stay within time limits
        if len(empty_cells) > 15:
            depth = 2  # Early game - faster evaluation
        elif len(empty_cells) > 8:
            depth = 3  # Mid game
        else:
            depth = 4  # Late game - deeper analysis
        
        _, best_move = self._minimax(board, depth, True, -math.inf, math.inf, self.symbol)
        
        if best_move is not None:
            return best_move
        
        # Fallback: choose move with highest immediate evaluation
        best_score = -math.inf
        best_move = empty_cells[0]
        for move in empty_cells:
            test_board = board[:]
            test_board[move] = self.symbol
            score = self._evaluate_position(test_board, self.symbol)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
