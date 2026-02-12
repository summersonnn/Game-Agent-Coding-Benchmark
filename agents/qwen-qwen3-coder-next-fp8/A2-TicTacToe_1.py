"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder-next
Run: 1
Generated: 2026-02-11 20:47:17
"""



import random

# Constants (matching the game implementation)
EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'

    def make_move(self, board):
        try:
            # Get available moves
            available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
            if not available_moves:
                return None
            
            # Use minimax with alpha-beta pruning for optimal play
            best_move = self._get_best_move(board, self.symbol)
            
            # If minimax fails or returns invalid move, fallback to best strategy
            if best_move is None or board[best_move] != EMPTY:
                # Fallback: try to win, then block, then center, then corners, then random
                return self._heuristic_move(board, available_moves)
            
            return best_move
        except Exception:
            # On any error, use heuristic as fallback
            available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
            return self._heuristic_move(board, available_moves)
    
    def _get_best_move(self, board, player):
        """Minimax with alpha-beta pruning"""
        opponent = O_MARK if player == X_MARK else X_MARK
        
        def minimax(board, depth, alpha, beta, is_maximizing):
            # Check terminal states
            winner = self._check_winner(board)
            if winner == player:
                return 1000 - depth
            elif winner == opponent:
                return depth - 1000
            elif winner == 'DRAW':
                return 0
            
            if is_maximizing:
                max_eval = float('-inf')
                for i in range(9):
                    if board[i] == EMPTY:
                        board[i] = player
                        eval_score = minimax(board, depth + 1, alpha, beta, False)
                        board[i] = EMPTY
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                return max_eval
            else:
                min_eval = float('inf')
                for i in range(9):
                    if board[i] == EMPTY:
                        board[i] = opponent
                        eval_score = minimax(board, depth + 1, alpha, beta, True)
                        board[i] = EMPTY
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                return min_eval
        
        # Find best move for current player
        best_score = float('-inf')
        best_move = None
        
        for i in range(9):
            if board[i] == EMPTY:
                board[i] = player
                score = minimax(board, 0, float('-inf'), float('inf'), False)
                board[i] = EMPTY
                
                if score > best_score:
                    best_score = score
                    best_move = i
        
        return best_move
    
    def _check_winner(self, board):
        """Check for winner or draw"""
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        
        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        
        if EMPTY not in board:
            return 'DRAW'
        return None
    
    def _heuristic_move(self, board, available_moves):
        """Fallback strategy when minimax fails"""
        opponent = O_MARK if self.symbol == X_MARK else X_MARK
        
        # 1. Check if we can win immediately
        for move in available_moves:
            board[move] = self.symbol
            if self._check_winner(board) == self.symbol:
                board[move] = EMPTY
                return move
            board[move] = EMPTY
        
        # 2. Block opponent from winning immediately
        for move in available_moves:
            board[move] = opponent
            if self._check_winner(board) == opponent:
                board[move] = EMPTY
                return move
            board[move] = EMPTY
        
        # 3. Take center if available
        if board[4] == EMPTY:
            return 4
        
        # 4. Take corners if available
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if board[c] == EMPTY]
        if available_corners:
            return random.choice(available_corners)
        
        # 5. Take edges if available
        edges = [1, 3, 5, 7]
        available_edges = [e for e in edges if board[e] == EMPTY]
        if available_edges:
            return random.choice(available_edges)
        
        # 6. Random available move
        return random.choice(available_moves)
