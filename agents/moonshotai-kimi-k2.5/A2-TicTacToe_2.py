"""
Agent Code: A2-TicTacToe
Model: moonshotai/kimi-k2.5
Run: 2
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        
    def make_move(self, board):
        # Check for immediate win
        move = self._find_winning_move(board, self.symbol)
        if move is not None:
            return move
            
        # Block opponent's immediate win
        move = self._find_winning_move(board, self.opponent)
        if move is not None:
            return move
            
        # Use minimax with alpha-beta pruning for optimal play
        best_score = float('-inf')
        best_moves = []
        alpha = float('-inf')
        beta = float('inf')
        
        for i in range(9):
            if board[i] == ' ':
                board[i] = self.symbol
                score = self._minimax(board, 0, False, alpha, beta)
                board[i] = ' '
                if score > best_score:
                    best_score = score
                    best_moves = [i]
                elif score == best_score:
                    best_moves.append(i)
                alpha = max(alpha, score)
                
        return random.choice(best_moves) if best_moves else self._random_move(board)
    
    def _find_winning_move(self, board, player):
        for i in range(9):
            if board[i] == ' ':
                board[i] = player
                winner = self._check_winner(board)
                board[i] = ' '
                if winner == player:
                    return i
        return None
    
    def _check_winner(self, board):
        for a, b, c in self.lines:
            if board[a] == board[b] == board[c] != ' ':
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
            max_eval = float('-inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval_score = self._minimax(board, depth + 1, False, alpha, beta)
                    board[i] = ' '
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
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
                        break
            return min_eval
    
    def _random_move(self, board):
        available = [i for i, spot in enumerate(board) if spot == ' ']
        return random.choice(available) if available else 0
