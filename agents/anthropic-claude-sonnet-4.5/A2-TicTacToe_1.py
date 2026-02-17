"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-sonnet-4.5
Run: 1
Generated: 2026-02-13 14:53:21
"""


import random
import time

class TicTacToeAgent:
    WIN_CONDITIONS = []
    
    @staticmethod
    def _build_wins():
        wc = []
        for r in range(5):
            for c in range(3):
                s = r * 5 + c
                wc.append((s, s+1, s+2))
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                wc.append((s, s+5, s+10))
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                wc.append((s, s+6, s+12))
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                wc.append((s, s+4, s+8))
        return wc

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opp = 'O' if symbol == 'X' else 'X'
        if not TicTacToeAgent.WIN_CONDITIONS:
            TicTacToeAgent.WIN_CONDITIONS = self._build_wins()
        # cell value map for 5x5
        self.cell_value = [0]*25
        for i in range(25):
            r, c = divmod(i, 5)
            # count win conditions this cell participates in
            cnt = sum(1 for wc in self.WIN_CONDITIONS if i in wc)
            self.cell_value[i] = cnt

    def _check_winner(self, board):
        for a, b, c in self.WIN_CONDITIONS:
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _score_board(self, board, symbol):
        opp = 'O' if symbol == 'X' else 'X'
        score = 0
        for a, b, c in self.WIN_CONDITIONS:
            line = [board[a], board[b], board[c]]
            mine = line.count(symbol)
            their = line.count(opp)
            if their == 0:
                if mine == 2: score += 10
                elif mine == 1: score += 1
            elif mine == 0:
                if their == 2: score -= 10
                elif their == 1: score -= 1
        return score

    def _minimax(self, board, depth, alpha, beta, maximizing, start_time, time_limit):
        if time.time() - start_time > time_limit:
            raise TimeoutError()
        
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 100 + depth, None
        if winner == self.opp:
            return -100 - depth, None
        if winner == 'DRAW':
            return 0, None
        
        moves = [i for i in range(25) if board[i] == ' ']
        
        if depth == 0:
            return self._score_board(board, self.symbol), None
        
        # Order moves by cell value for better pruning
        moves.sort(key=lambda x: self.cell_value[x], reverse=True)
        
        best_move = moves[0]
        if maximizing:
            best_val = -999
            sym = self.symbol
        else:
            best_val = 999
            sym = self.opp
            
        for m in moves:
            board[m] = sym
            val, _ = self._minimax(board, depth-1, alpha, beta, not maximizing, start_time, time_limit)
            board[m] = ' '
            if maximizing:
                if val > best_val:
                    best_val, best_move = val, m
                alpha = max(alpha, val)
            else:
                if val < best_val:
                    best_val, best_move = val, m
                beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_move

    def make_move(self, board):
        board = list(board)
        moves = [i for i in range(25) if board[i] == ' ']
        if not moves:
            return None
        
        # Immediate win
        for m in moves:
            board[m] = self.symbol
            if self._check_winner(board) == self.symbol:
                board[m] = ' '
                return m
            board[m] = ' '
        
        # Immediate block
        for m in moves:
            board[m] = self.opp
            if self._check_winner(board) == self.opp:
                board[m] = ' '
                return m
            board[m] = ' '
        
        # Iterative deepening minimax
        start = time.time()
        time_limit = 0.85
        best_move = max(moves, key=lambda x: self.cell_value[x])
        
        try:
            for depth in range(1, 10):
                val, move = self._minimax(board, depth, -999, 999, True, start, time_limit)
                if move is not None:
                    best_move = move
                if abs(val) >= 100:
                    break
        except TimeoutError:
            pass
        
        return best_move