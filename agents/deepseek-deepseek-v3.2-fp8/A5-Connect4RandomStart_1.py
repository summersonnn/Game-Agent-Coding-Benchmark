"""
Agent Code: A5-Connect4RandomStart
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 3
Generated: 2026-02-12 14:50:42
"""

import math
import time

import random
import math
import time

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.time_limit = 0.95  # Stay under 1s limit
        self.max_depth = 8  # Maximum search depth
        
    def make_move(self, board):
        start_time = time.time()
        
        # Get all valid moves
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return 0  # Shouldn't happen, but fallback
        
        # If we're Yellow (first to move), check for immediate wins
        if self.symbol == 'Y':
            # Check for winning move
            for col in valid_moves:
                if self.is_winning_move(board, col, self.symbol):
                    return col
            
            # Check if opponent can win next move (block)
            for col in valid_moves:
                if self.is_winning_move(board, col, self.opponent):
                    return col
        
        # For Red (second move), check if we can win immediately
        if self.symbol == 'R':
            for col in valid_moves:
                if self.is_winning_move(board, col, self.symbol):
                    return col
        
        # Use iterative deepening with time limit
        best_move = valid_moves[0]
        best_score = -math.inf
        
        for depth in range(1, self.max_depth + 1):
            if time.time() - start_time > self.time_limit:
                break
                
            current_best_move = None
            current_best_score = -math.inf
            
            # Sort moves by center preference for better pruning
            sorted_moves = sorted(valid_moves, 
                                key=lambda x: abs(x - 3))
            
            for col in sorted_moves:
                if time.time() - start_time > self.time_limit:
                    break
                    
                row = self.get_next_empty_row(board, col)
                if row is None:
                    continue
                    
                # Make the move
                board[row][col] = self.symbol
                
                # Evaluate with minimax
                score = self.minimax(board, depth - 1, -math.inf, math.inf, False, start_time)
                
                # Undo the move
                board[row][col] = ' '
                
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = col
            
            if current_best_move is not None:
                best_move = current_best_move
                best_score = current_best_score
        
        return best_move
    
    def minimax(self, board, depth, alpha, beta, maximizing, start_time):
        # Time check
        if time.time() - start_time > self.time_limit:
            return 0
        
        # Terminal state evaluation
        if self.check_win(board, self.symbol):
            return 10000 + depth  # Prefer faster wins
        if self.check_win(board, self.opponent):
            return -10000 - depth  # Prefer slower losses
        if self.is_board_full(board):
            return 0
        if depth == 0:
            return self.evaluate_board(board)
        
        valid_moves = self.get_valid_moves(board)
        
        if maximizing:
            max_eval = -math.inf
            for col in valid_moves:
                row = self.get_next_empty_row(board, col)
                if row is None:
                    continue
                    
                board[row][col] = self.symbol
                eval_score = self.minimax(board, depth - 1, alpha, beta, False, start_time)
                board[row][col] = ' '
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Beta cutoff
                    
            return max_eval
        else:
            min_eval = math.inf
            for col in valid_moves:
                row = self.get_next_empty_row(board, col)
                if row is None:
                    continue
                    
                board[row][col] = self.opponent
                eval_score = self.minimax(board, depth - 1, alpha, beta, True, start_time)
                board[row][col] = ' '
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha cutoff
                    
            return min_eval
    
    def evaluate_board(self, board):
        """Heuristic evaluation of board position"""
        score = 0
        
        # Prefer center columns (especially important for RandomStart)
        center_array = [board[r][3] for r in range(6)]
        center_count = center_array.count(self.symbol)
        score += center_count * 3
        
        # Evaluate all possible windows of 4
        for r in range(6):
            for c in range(7):
                # Check horizontal
                if c <= 3:
                    window = [board[r][c+i] for i in range(4)]
                    score += self.evaluate_window(window)
                
                # Check vertical
                if r <= 2:
                    window = [board[r+i][c] for i in range(4)]
                    score += self.evaluate_window(window)
                
                # Check diagonal /
                if r >= 3 and c <= 3:
                    window = [board[r-i][c+i] for i in range(4)]
                    score += self.evaluate_window(window)
                
                # Check diagonal \
                if r <= 2 and c <= 3:
                    window = [board[r+i][c+i] for i in range(4)]
                    score += self.evaluate_window(window)
        
        return score
    
    def evaluate_window(self, window):
        """Evaluate a 4-cell window"""
        score = 0
        
        my_count = window.count(self.symbol)
        opp_count = window.count(self.opponent)
        empty_count = window.count(' ')
        
        if my_count == 3 and empty_count == 1:
            score += 100  # Almost winning
        elif my_count == 2 and empty_count == 2:
            score += 10   # Potential line
        elif opp_count == 3 and empty_count == 1:
            score -= 90   # Block opponent's win next move
        
        return score
    
    def get_valid_moves(self, board):
        """Get list of columns that are not full"""
        return [c for c in range(7) if board[0][c] == ' ']
    
    def get_next_empty_row(self, board, col):
        """Get the next empty row in a column"""
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                return r
        return None
    
    def is_winning_move(self, board, col, player):
        """Check if dropping in column would result in a win"""
        row = self.get_next_empty_row(board, col)
        if row is None:
            return False
        
        # Temporarily place the piece
        board[row][col] = player
        is_win = self.check_win(board, player)
        board[row][col] = ' '
        
        return is_win
    
    def check_win(self, board, player):
        """Check if player has won"""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if all(board[r][c+i] == player for i in range(4)):
                    return True
        
        # Vertical
        for r in range(3):
            for c in range(7):
                if all(board[r+i][c] == player for i in range(4)):
                    return True
        
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if all(board[r-i][c+i] == player for i in range(4)):
                    return True
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if all(board[r+i][c+i] == player for i in range(4)):
                    return True
        
        return False
    
    def is_board_full(self, board):
        """Check if board is completely filled"""
        return all(board[0][c] != ' ' for c in range(7))


# Test function to verify the agent works
def test_agent():
    game = Connect4Game()
    agent_yellow = Connect4Agent("SmartYellow", "Y")
    agent_red = Connect4Agent("SmartRed", "R")
    
    print("Initial board (Red placed randomly):")
    for row in game.board:
        print('|' + '|'.join(row) + '|')
    
    winner = game.play_game(agent_red, agent_yellow)
    print(f"\nWinner: {winner}")
    
    print("\nFinal board:")
    for row in game.board:
        print('|' + '|'.join(row) + '|')


# Uncomment to test
# if __name__ == "__main__":
#     test_agent()
