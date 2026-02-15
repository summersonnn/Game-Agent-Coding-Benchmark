"""
Agent Code: A2-TicTacToe
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-14 16:45:38
"""



import random

class TicTacToeAgent:
    WIN_LINES = [
        # Rows
        (0,1,2), (1,2,3), (2,3,4),
        (5,6,7), (6,7,8), (7,8,9),
        (10,11,12), (11,12,13), (12,13,14),
        (15,16,17), (16,17,18), (17,18,19),
        (20,21,22), (21,22,23), (22,23,24),
        # Columns
        (0,5,10), (5,10,15), (10,15,20),
        (1,6,11), (6,11,16), (11,16,21),
        (2,7,12), (7,12,17), (12,17,22),
        (3,8,13), (8,13,18), (13,18,23),
        (4,9,14), (9,14,19), (14,19,24),
        # Diagonals (down-right)
        (0,6,12), (1,7,13), (2,8,14),
        (5,11,17), (6,12,18), (7,13,19),
        (10,16,22), (11,17,23), (12,18,24),
        # Diagonals (down-left)
        (4,8,12), (3,7,11), (2,6,10),
        (9,13,17), (8,12,16), (7,11,15),
        (14,18,22), (13,17,21), (12,16,20)
    ]
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
    
    def make_move(self, board):
        available = [i for i in range(25) if board[i] == ' ']
        if not available:
            return None
        
        # Step 1: Check for immediate win
        for move in available:
            board[move] = self.symbol
            if self._check_winner(board) == self.symbol:
                board[move] = ' '
                return move
            board[move] = ' '
        
        # Step 2: Block opponent's immediate win
        opp_symbol = 'O' if self.symbol == 'X' else 'X'
        for move in available:
            board[move] = opp_symbol
            if self._check_winner(board) == opp_symbol:
                board[move] = ' '
                return move
            board[move] = ' '
        
        # Step 3: Use minimax with adaptive depth
        empty_count = len(available)
        empty_after = empty_count - 1
        if empty_after <= 5:
            depth = 4
        elif empty_after <= 10:
            depth = 3
        else:
            depth = 2
        
        best_move = None
        best_score = -float('inf')
        for move in available:
            board[move] = self.symbol
            score = self._minimax(board, depth, False, -float('inf'), float('inf'), self.symbol, opp_symbol)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
    
    def _check_winner(self, board):
        for line in self.WIN_LINES:
            a, b, c = line
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None
    
    def _evaluate(self, board, our_symbol, opp_symbol):
        score = 0
        for line in self.WIN_LINES:
            our = 0
            opp = 0
            for idx in line:
                if board[idx] == our_symbol:
                    our += 1
                elif board[idx] == opp_symbol:
                    opp += 1
            if opp == 0:
                if our == 2:
                    score += 10
                elif our == 1:
                    score += 1
            elif our == 0:
                if opp == 2:
                    score -= 10
                elif opp == 1:
                    score -= 1
        return score
    
    def _minimax(self, board, depth, maximizing, alpha, beta, our_symbol, opp_symbol):
        winner = self._check_winner(board)
        if winner == our_symbol:
            return 1000000
        if winner == opp_symbol:
            return -1000000
        if winner == 'DRAW':
            return 0
        
        if depth == 0:
            return self._evaluate(board, our_symbol, opp_symbol)
        
        empty_cells = [i for i in range(25) if board[i] == ' ']
        
        if maximizing:
            best = -float('inf')
            for cell in empty_cells:
                board[cell] = our_symbol
                score = self._minimax(board, depth-1, False, alpha, beta, our_symbol, opp_symbol)
                board[cell] = ' '
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if beta <= alpha:
                    break
            return best
        else:
            best = float('inf')
            for cell in empty_cells:
                board[cell] = opp_symbol
                score = self._minimax(board, depth-1, True, alpha, beta, our_symbol, opp_symbol)
                board[cell] = ' '
                if score < best:
                    best = score
                if best < beta:
                    beta = best
                if beta <= alpha:
                    break
            return best
