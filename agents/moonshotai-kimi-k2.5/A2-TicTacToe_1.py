"""
Agent Code: A2-TicTacToe
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        # Winning combinations
        self.win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        
    def make_move(self, board):
        available = [i for i, cell in enumerate(board) if cell == ' ']
        
        if not available:
            return None
        
        # Immediate win check
        for move in available:
            board[move] = self.symbol
            if self._check_winner(board) == self.symbol:
                return move
            board[move] = ' '
        
        # Immediate block check
        for move in available:
            board[move] = self.opponent
            if self._check_winner(board) == self.opponent:
                return move
            board[move] = ' '
        
        # Minimax with alpha-beta pruning for optimal play
        best_score = -float('inf')
        best_move = available[0]
        alpha = -float('inf')
        beta = float('inf')
        
        for move in available:
            board[move] = self.symbol
            score = self._minimax(board, 0, False, alpha, beta)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
                
        return best_move
    
    def _check_winner(self, board):
        for a, b, c in self.win_conditions:
            if board[a] == board[b] == board[c] and board[a] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None
        
    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        result = self._check_winner(board)
        if result == self.symbol:
            return 10 - depth
        elif result == self.opponent:
            return depth - 10
        elif result == 'DRAW':
            return 0
            
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval = self._minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent
                    eval = self._minimax(board, depth + 1, True, alpha, beta)
                    board[i] = ' '
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
            return min_eval
