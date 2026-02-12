"""
Agent Code: A5-Connect4RandomStart
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-12 14:50:42
"""

import time

import random
import time

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.time_limit = 0.95  # seconds, leave some margin
        self.transposition_table = {}
        self.killer_moves = [[], []]  # Two killer moves per depth
        self.history_table = {}  # History heuristic
        
    def make_move(self, board):
        start_time = time.time()
        best_move = None
        best_score = float('-inf')
        
        # Get valid moves ordered by center preference
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return 0  # Fallback
        
        # Order moves for better pruning
        ordered_moves = self.order_moves(board, valid_moves, 0, is_maximizing=True)
        
        # Iterative deepening
        depth = 1
        while time.time() - start_time < self.time_limit:
            current_best_move = ordered_moves[0]
            current_best_score = float('-inf')
            
            alpha = float('-inf')
            beta = float('inf')
            
            for move in ordered_moves:
                new_board = self.simulate_move(board, move, self.symbol)
                score = self.minimax(new_board, depth-1, False, alpha, beta, start_time)
                
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move
                
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            
            # Update best if we completed the depth
            if time.time() - start_time < self.time_limit:
                best_move = current_best_move
                best_score = current_best_score
                depth += 1
            else:
                break
        
        # If we haven't found a move, use the first valid one
        return best_move if best_move is not None else valid_moves[0]
    
    def minimax(self, board, depth, is_maximizing, alpha, beta, start_time):
        # Check timeout
        if time.time() - start_time >= self.time_limit:
            return 0
        
        # Check for terminal states
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 1000 + depth  # Prefer faster wins
        elif winner == self.opponent:
            return -1000 - depth  # Avoid faster losses
        elif self.is_board_full(board):
            return 0
        
        if depth == 0:
            return self.evaluate_board(board)
        
        # Transposition table lookup
        board_key = self.get_board_key(board)
        if board_key in self.transposition_table:
            entry = self.transposition_table[board_key]
            if entry['depth'] >= depth:
                if entry['flag'] == 'exact':
                    return entry['score']
                elif entry['flag'] == 'lower':
                    alpha = max(alpha, entry['score'])
                elif entry['flag'] == 'upper':
                    beta = min(beta, entry['score'])
                if alpha >= beta:
                    return entry['score']
        
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return 0
        
        # Order moves
        ordered_moves = self.order_moves(board, valid_moves, depth, is_maximizing)
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in ordered_moves:
                new_board = self.simulate_move(board, move, self.symbol)
                eval_score = self.minimax(new_board, depth-1, False, alpha, beta, start_time)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                # Update history heuristic
                self.history_table[move] = self.history_table.get(move, 0) + (2 ** depth)
                
                if beta <= alpha:
                    # Store killer move
                    if move not in self.killer_moves[depth % 2]:
                        self.killer_moves[depth % 2].insert(0, move)
                        if len(self.killer_moves[depth % 2]) > 2:
                            self.killer_moves[depth % 2].pop()
                    break
            
            # Store in transposition table
            flag = 'exact'
            if max_eval <= alpha:
                flag = 'upper'
            elif max_eval >= beta:
                flag = 'lower'
            self.transposition_table[board_key] = {
                'score': max_eval,
                'depth': depth,
                'flag': flag
            }
            return max_eval
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                new_board = self.simulate_move(board, move, self.opponent)
                eval_score = self.minimax(new_board, depth-1, True, alpha, beta, start_time)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                # Update history heuristic
                self.history_table[move] = self.history_table.get(move, 0) + (2 ** depth)
                
                if beta <= alpha:
                    # Store killer move
                    if move not in self.killer_moves[depth % 2]:
                        self.killer_moves[depth % 2].insert(0, move)
                        if len(self.killer_moves[depth % 2]) > 2:
                            self.killer_moves[depth % 2].pop()
                    break
            
            # Store in transposition table
            flag = 'exact'
            if min_eval <= alpha:
                flag = 'upper'
            elif min_eval >= beta:
                flag = 'lower'
            self.transposition_table[board_key] = {
                'score': min_eval,
                'depth': depth,
                'flag': flag
            }
            return min_eval
    
    def evaluate_board(self, board):
        """Evaluate the board from the perspective of the agent."""
        score = 0
        
        # Center column preference
        center_column = 3
        for r in range(6):
            if board[r][center_column] == self.symbol:
                score += 3
            elif board[r][center_column] == self.opponent:
                score -= 3
        
        # Evaluate all possible 4-in-a-row windows
        for r in range(6):
            for c in range(7):
                # Check horizontal
                if c <= 3:
                    window = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]]
                    score += self.evaluate_window(window)
                
                # Check vertical
                if r <= 2:
                    window = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]]
                    score += self.evaluate_window(window)
                
                # Check diagonal /
                if r <= 2 and c <= 3:
                    window = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]]
                    score += self.evaluate_window(window)
                
                # Check diagonal \
                if r >= 3 and c <= 3:
                    window = [board[r][c], board[r-1][c+1], board[r-2][c+2], board[r-3][c+3]]
                    score += self.evaluate_window(window)
        
        return score
    
    def evaluate_window(self, window):
        """Evaluate a 4-cell window."""
        score = 0
        my_count = window.count(self.symbol)
        opp_count = window.count(self.opponent)
        empty_count = window.count(' ')
        
        if my_count == 4:
            score += 100
        elif my_count == 3 and empty_count == 1:
            score += 5
        elif my_count == 2 and empty_count == 2:
            score += 2
        
        if opp_count == 4:
            score -= 100
        elif opp_count == 3 and empty_count == 1:
            score -= 4  # Slightly less than our 3-in-a-row (defensive bias)
        elif opp_count == 2 and empty_count == 2:
            score -= 2
        
        return score
    
    def get_valid_moves(self, board):
        """Get list of valid column indices."""
        return [c for c in range(7) if board[0][c] == ' ']
    
    def simulate_move(self, board, col, player):
        """Return a new board with the move made."""
        new_board = [row[:] for row in board]
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = player
                break
        return new_board
    
    def order_moves(self, board, moves, depth, is_maximizing):
        """Order moves for better alpha-beta pruning."""
        player = self.symbol if is_maximizing else self.opponent
        move_scores = []
        
        for move in moves:
            score = 0
            
            # Prefer center columns
            score += 3 - abs(3 - move)
            
            # Check for immediate win
            new_board = self.simulate_move(board, move, player)
            if self.check_winner(new_board) == player:
                score += 1000
            
            # Check for immediate block (opponent would win next)
            opponent = self.opponent if is_maximizing else self.symbol
            opp_board = self.simulate_move(board, move, opponent)
            if self.check_winner(opp_board) == opponent:
                score += 500
            
            # Killer moves
            if move in self.killer_moves[depth % 2]:
                score += 100
            
            # History heuristic
            score += self.history_table.get(move, 0)
            
            move_scores.append((move, score))
        
        # Sort by score (descending)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]
    
    def get_board_key(self, board):
        """Create a string key for the board state."""
        return ''.join([''.join(row) for row in board])
    
    def check_winner(self, board):
        """Check for a winner on the board."""
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        
        # Vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and \
                   board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        
        return None
    
    def is_board_full(self, board):
        """Check if the board is full."""
        return all(board[0][c] != ' ' for c in range(7))


# Simple test agent for testing
class RandomAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
    
    def make_move(self, board):
        valid_moves = [c for c in range(7) if board[0][c] == ' ']
        return random.choice(valid_moves) if valid_moves else 0


# Test the agent
if __name__ == "__main__":
    # Create a test game
    game = Connect4Game()
    smart_agent = Connect4Agent("SmartBot", "Y")
    random_agent = RandomAgent("RandomBot", "R")
    
    # Play a game
    winner = game.play_game(random_agent, smart_agent)
    print(f"Winner: {winner}")
    
    # Print final board
    for row in game.board:
        print('|' + '|'.join(row) + '|')
