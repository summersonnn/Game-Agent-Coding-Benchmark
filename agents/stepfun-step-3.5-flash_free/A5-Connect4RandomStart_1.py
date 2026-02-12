"""
Agent Code: A5-Connect4RandomStart
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-12 14:50:42
"""

import math

import random
import math

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        
        # Center column preference for move ordering
        self.center_preference = [3, 2, 4, 1, 5, 0, 6]
    
    def make_move(self, board):
        """Main move selection function"""
        player = self.symbol
        opponent = self.opponent_symbol
        
        # Helper functions defined inside to have access to player/opponent
        def get_valid_moves(board_state):
            """Return list of valid column indices (0-6)"""
            return [c for c in range(7) if board_state[0][c] == ' ']
        
        def is_winner(board_state, symbol):
            """Check if symbol has 4 in a row"""
            # Horizontal
            for r in range(6):
                for c in range(4):
                    if (board_state[r][c] == symbol and 
                        board_state[r][c+1] == symbol and 
                        board_state[r][c+2] == symbol and 
                        board_state[r][c+3] == symbol):
                        return True
            
            # Vertical
            for r in range(3):
                for c in range(7):
                    if (board_state[r][c] == symbol and 
                        board_state[r+1][c] == symbol and 
                        board_state[r+2][c] == symbol and 
                        board_state[r+3][c] == symbol):
                        return True
            
            # Diagonal /
            for r in range(3, 6):
                for c in range(4):
                    if (board_state[r][c] == symbol and 
                        board_state[r-1][c+1] == symbol and 
                        board_state[r-2][c+2] == symbol and 
                        board_state[r-3][c+3] == symbol):
                        return True
            
            # Diagonal \
            for r in range(3):
                for c in range(4):
                    if (board_state[r][c] == symbol and 
                        board_state[r+1][c+1] == symbol and 
                        board_state[r+2][c+2] == symbol and 
                        board_state[r+3][c+3] == symbol):
                        return True
            
            return False
        
        def evaluate_window(window, player, opponent):
            """Evaluate a 4-cell window"""
            player_count = window.count(player)
            opponent_count = window.count(opponent)
            empty_count = window.count(' ')
            
            # Winning conditions
            if player_count == 4:
                return 10000
            if opponent_count == 4:
                return -10000
            
            # Strategic patterns
            if player_count == 3 and empty_count == 1:
                return 100
            if player_count == 2 and empty_count == 2:
                return 10
            if player_count == 1 and empty_count == 3:
                return 1
            
            if opponent_count == 3 and empty_count == 1:
                return -100
            if opponent_count == 2 and empty_count == 2:
                return -10
            if opponent_count == 1 and empty_count == 3:
                return -1
            
            return 0
        
        def evaluate_board(board_state, player):
            """Evaluate entire board for player"""
            opponent = 'Y' if player == 'R' else 'R'
            score = 0
            
            # Center column preference bonus
            center_col = 3
            for r in range(6):
                if board_state[r][center_col] == player:
                    score += 3
                elif board_state[r][center_col] == opponent:
                    score -= 3
            
            # Evaluate all windows
            # Horizontal
            for r in range(6):
                for c in range(4):
                    window = [board_state[r][c], board_state[r][c+1], 
                             board_state[r][c+2], board_state[r][c+3]]
                    score += evaluate_window(window, player, opponent)
            
            # Vertical
            for r in range(3):
                for c in range(7):
                    window = [board_state[r][c], board_state[r+1][c], 
                             board_state[r+2][c], board_state[r+3][c]]
                    score += evaluate_window(window, player, opponent)
            
            # Diagonal /
            for r in range(3, 6):
                for c in range(4):
                    window = [board_state[r][c], board_state[r-1][c+1], 
                             board_state[r-2][c+2], board_state[r-3][c+3]]
                    score += evaluate_window(window, player, opponent)
            
            # Diagonal \
            for r in range(3):
                for c in range(4):
                    window = [board_state[r][c], board_state[r+1][c+1], 
                             board_state[r+2][c+2], board_state[r+3][c+3]]
                    score += evaluate_window(window, player, opponent)
            
            return score
        
        def get_winning_move(board_state, symbol):
            """Find a move that results in immediate win for symbol"""
            for col in range(7):
                if board_state[0][col] != ' ':
                    continue
                
                # Find row where disc would land
                for r in range(5, -1, -1):
                    if board_state[r][col] == ' ':
                        board_state[r][col] = symbol
                        if is_winner(board_state, symbol):
                            board_state[r][col] = ' '
                            return col
                        board_state[r][col] = ' '
                        break
            return None
        
        def make_move_on_board(board_state, col, symbol):
            """Simulate dropping a disc in column (modifies board_state)"""
            for r in range(5, -1, -1):
                if board_state[r][col] == ' ':
                    board_state[r][col] = symbol
                    return
        
        # Step 1: Check for immediate winning move
        win_move = get_winning_move([row[:] for row in board], player)
        if win_move is not None:
            return win_move
        
        # Step 2: Check if opponent can win (must block)
        block_move = get_winning_move([row[:] for row in board], opponent)
        if block_move is not None:
            return block_move
        
        # Step 3: Use minimax with adaptive depth
        empty_cells = sum(row.count(' ') for row in board)
        
        # Adaptive depth based on remaining moves
        if empty_cells < 10:
            depth = 6
        elif empty_cells < 20:
            depth = 5
        elif empty_cells < 30:
            depth = 4
        else:
            depth = 3
        
        # Minimax with alpha-beta pruning
        def minimax(board_state, depth, alpha, beta, maximizing):
            valid_moves = get_valid_moves(board_state)
            
            # Terminal check
            if (depth == 0 or not valid_moves or 
                is_winner(board_state, player) or 
                is_winner(board_state, opponent)):
                return None, evaluate_board(board_state, player)
            
            # Sort moves by center preference for better pruning
            valid_moves.sort(key=lambda x: self.center_preference.index(x))
            
            if maximizing:
                max_eval = -math.inf
                best_move = valid_moves[0]
                for col in valid_moves:
                    new_board = [row[:] for row in board_state]
                    make_move_on_board(new_board, col, player)
                    
                    _, eval = minimax(new_board, depth-1, alpha, beta, False)
                    
                    if eval > max_eval:
                        max_eval = eval
                        best_move = col
                    
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
                return best_move, max_eval
            else:
                min_eval = math.inf
                for col in valid_moves:
                    new_board = [row[:] for row in board_state]
                    make_move_on_board(new_board, col, opponent)
                    
                    _, eval = minimax(new_board, depth-1, alpha, beta, True)
                    
                    if eval < min_eval:
                        min_eval = eval
                    
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
                return None, min_eval
        
        # Get best move from minimax
        best_move, _ = minimax(board, depth, -math.inf, math.inf, True)
        
        # Fallback if something goes wrong
        if best_move is None:
            valid_moves = get_valid_moves(board)
            return random.choice(valid_moves) if valid_moves else 0
        
        return best_move
