"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 2
Generated: 2026-02-13 14:53:21
"""

import math

import math

EMPTY = ' '

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
        # Precompute all winning lines
        self.win_lines = []
        
        # Horizontal lines: for each row, 3 possible 3-in-a-row starting positions
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append([start, start + 1, start + 2])
        
        # Vertical lines: for each column, 3 possible 3-in-a-row starting positions
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_lines.append([start, start + 5, start + 10])
        
        # Diagonal down-right: top-left 3x3 area
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append([start, start + 6, start + 12])
        
        # Diagonal down-left: top-right 3x3 area
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_lines.append([start, start + 4, start + 8])
        
        # Position weights (center is most valuable)
        self.position_weights = [
            1, 1, 1, 1, 1,
            1, 2, 2, 2, 1,
            1, 2, 3, 2, 1,
            1, 2, 2, 2, 1,
            1, 1, 1, 1, 1
        ]
    
    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        
        if not available_moves:
            return None
        
        # Priority 1: Win immediately
        for move in available_moves:
            board[move] = self.symbol
            if self.check_winner(board) == self.symbol:
                return move
            board[move] = EMPTY
        
        # Priority 2: Block opponent's winning move
        for move in available_moves:
            board[move] = self.opponent
            if self.check_winner(board) == self.opponent:
                board[move] = EMPTY
                return move
            board[move] = EMPTY
        
        # Priority 3: Use minimax for deeper analysis
        empty_count = len(available_moves)
        
        # Adaptive depth: deeper search when fewer moves remain
        if empty_count > 20:
            max_depth = 3
        elif empty_count > 12:
            max_depth = 4
        else:
            max_depth = 5
        
        best_score = -math.inf
        best_move = available_moves[0]
        
        # Sort moves by position weight for better alpha-beta pruning
        available_moves.sort(key=lambda m: -self.position_weights[m])
        
        for move in available_moves:
            board[move] = self.symbol
            score = self.minimax(board, 1, False, -math.inf, math.inf, max_depth)
            board[move] = EMPTY
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def minimax(self, board, depth, is_maximizing, alpha, beta, max_depth):
        winner = self.check_winner(board)
        
        if winner == self.symbol:
            return 10000 - depth  # Prefer quicker wins (lower depth = better)
        elif winner == self.opponent:
            return -10000 + depth  # Prefer delaying losses
        elif depth >= max_depth or board.count(EMPTY) == 0:
            return self.evaluate(board)
        
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        
        # Sort moves by position weight for better alpha-beta pruning
        available_moves.sort(key=lambda m: -self.position_weights[m])
        
        if is_maximizing:
            max_score = -math.inf
            for move in available_moves:
                board[move] = self.symbol
                score = self.minimax(board, depth + 1, False, alpha, beta, max_depth)
                board[move] = EMPTY
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = math.inf
            for move in available_moves:
                board[move] = self.opponent
                score = self.minimax(board, depth + 1, True, alpha, beta, max_depth)
                board[move] = EMPTY
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score
    
    def evaluate(self, board):
        """Heuristic evaluation of the board state."""
        score = 0
        
        for line in self.win_lines:
            my_count = sum(1 for pos in line if board[pos] == self.symbol)
            opp_count = sum(1 for pos in line if board[pos] == self.opponent)
            empty_count = sum(1 for pos in line if board[pos] == EMPTY)
            
            if my_count == 2 and empty_count == 1:
                score += 100  # We have 2 in a row, can win next
            elif my_count == 1 and empty_count == 2 and opp_count == 0:
                score += 10  # We have 1 in a row with no opponent blocking
            elif my_count == 1 and empty_count == 2:
                score += 3   # We have 1 in a row
            elif opp_count == 2 and empty_count == 1:
                score -= 100  # Opponent has 2 in a row, need to block
            elif opp_count == 1 and empty_count == 2 and my_count == 0:
                score -= 10  # Opponent has 1 in a row with no us blocking
            elif opp_count == 1 and empty_count == 2:
                score -= 3   # Opponent has 1 in a row
        
        # Add position weights
        for i, cell in enumerate(board):
            if cell == self.symbol:
                score += self.position_weights[i]
            elif cell == self.opponent:
                score -= self.position_weights[i]
        
        return score
    
    def check_winner(self, board):
        for line in self.win_lines:
            if board[line[0]] == board[line[1]] == board[line[2]] != EMPTY:
                return board[line[0]]
        return None
