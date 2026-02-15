"""
Agent Code: A2-TicTacToe
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-14 16:45:38
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.WINNING_LINES = self._generate_winning_lines()
    
    def _generate_winning_lines(self):
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))
        # Columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))
        # Diagonals (top-left to bottom-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))
        # Diagonals (top-right to bottom-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))
        return lines
    
    def make_move(self, board):
        available = [i for i, v in enumerate(board) if v == ' ']
        if not available:
            return None
        
        # 1. Check for immediate winning move
        for move in available:
            test_board = board[:]
            test_board[move] = self.symbol
            if self._check_winner(test_board) == self.symbol:
                return move
        
        # 2. Check if opponent can win next and block
        for move in available:
            test_board = board[:]
            test_board[move] = self.opponent
            if self._check_winner(test_board) == self.opponent:
                return move
        
        # 3. Use positional evaluation
        best_score = -float('inf')
        best_move = available[0]
        
        for move in available:
            score = self._evaluate_position(board, move)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _check_winner(self, board):
        for line in self.WINNING_LINES:
            if board[line[0]] == board[line[1]] == board[line[2]] != ' ':
                return board[line[0]]
        if ' ' not in board:
            return 'DRAW'
        return None
    
    def _evaluate_position(self, board, move):
        score = 0
        test_board = board[:]
        test_board[move] = self.symbol
        
        # Analyze all winning lines containing this move
        for line in self.WINNING_LINES:
            if move not in line:
                continue
            
            my_count = sum(1 for i in line if test_board[i] == self.symbol)
            opp_count = sum(1 for i in line if test_board[i] == self.opponent)
            
            if my_count == 3:
                score += 1000
            elif my_count == 2 and opp_count == 0:
                score += 50
            elif my_count == 1 and opp_count == 0:
                score += 5
            
            if opp_count == 2 and my_count == 0:
                score -= 30
            elif opp_count == 1 and my_count == 0:
                score -= 2
        
        # Position bonuses
        center = 12
        if move == center:
            score += 30
        
        corners = [0, 4, 20, 24]
        if move in corners:
            score += 10
        
        near_center = [6, 8, 11, 13, 16, 18]
        if move in near_center:
            score += 5
        
        return score
