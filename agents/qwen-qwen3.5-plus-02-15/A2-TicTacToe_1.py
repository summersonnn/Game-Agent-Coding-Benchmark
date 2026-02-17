"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3.5-plus-02-15
Run: 1
Generated: 2026-02-16 18:33:25
"""

import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_lines = self._generate_win_lines()

    def _generate_win_lines(self):
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                idx = r * 5 + c
                lines.append((idx, idx + 1, idx + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                idx = r * 5 + c
                lines.append((idx, idx + 5, idx + 10))
        # Diagonals (\)
        for r in range(3):
            for c in range(3):
                idx = r * 5 + c
                lines.append((idx, idx + 6, idx + 12))
        # Diagonals (/)
        for r in range(3):
            for c in range(2, 5):
                idx = r * 5 + c
                lines.append((idx, idx + 4, idx + 8))
        return lines

    def _move_priority(self, m):
        r, c = divmod(m, 5)
        return abs(r - 2) + abs(c - 2)

    def make_move(self, board):
        empty_indices = [i for i, v in enumerate(board) if v == ' ']
        if not empty_indices:
            return 0
        
        # 1. Check for immediate win
        for move in empty_indices:
            board[move] = self.symbol
            if self._check_win(board, self.symbol):
                board[move] = ' '
                return move
            board[move] = ' '
        
        # 2. Check for immediate block
        for move in empty_indices:
            board[move] = self.opponent
            if self._check_win(board, self.opponent):
                board[move] = ' '
                return move
            board[move] = ' '
            
        # 3. Minimax search
        best_move = empty_indices[0]
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        depth_limit = 4
        
        # Move ordering: prefer center
        empty_indices.sort(key=self._move_priority)
        
        for move in empty_indices:
            board[move] = self.symbol
            score = self._minimax(board, 0, False, alpha, beta, depth_limit)
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            
        return best_move

    def _check_win(self, board, player):
        for line in self.win_lines:
            if board[line[0]] == board[line[1]] == board[line[2]] == player:
                return True
        return False

    def _minimax(self, board, depth, is_maximizing, alpha, beta, max_depth):
        if self._check_win(board, self.symbol):
            return 1000 - depth
        if self._check_win(board, self.opponent):
            return -1000 + depth
        
        empty_indices = [i for i, v in enumerate(board) if v == ' ']
        if not empty_indices:
            return 0
        
        if depth >= max_depth:
            return self._evaluate(board)
        
        # Move ordering for pruning efficiency
        empty_indices.sort(key=self._move_priority)
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in empty_indices:
                board[move] = self.symbol
                eval = self._minimax(board, depth + 1, False, alpha, beta, max_depth)
                board[move] = ' '
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in empty_indices:
                board[move] = self.opponent
                eval = self._minimax(board, depth + 1, True, alpha, beta, max_depth)
                board[move] = ' '
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, board):
        score = 0
        for line in self.win_lines:
            v0, v1, v2 = board[line[0]], board[line[1]], board[line[2]]
            my_count = 0
            opp_count = 0
            for v in (v0, v1, v2):
                if v == self.symbol:
                    my_count += 1
                elif v == self.opponent:
                    opp_count += 1
            
            if my_count > 0 and opp_count == 0:
                if my_count == 1: score += 10
                elif my_count == 2: score += 100
            elif opp_count > 0 and my_count == 0:
                if opp_count == 1: score -= 10
                elif opp_count == 2: score -= 100
        return score