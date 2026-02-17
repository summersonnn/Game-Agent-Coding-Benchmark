"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3.5-397b-a17b
Run: 1
Generated: 2026-02-16 18:23:36
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.winning_lines = self._generate_winning_lines()
        self.lines_map = self._generate_lines_map()

    def _generate_winning_lines(self):
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))
        # Diagonals \
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))
        # Diagonals /
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))
        return lines

    def _generate_lines_map(self):
        lines_map = {i: [] for i in range(25)}
        for line in self.winning_lines:
            for cell in line:
                lines_map[cell].append(line)
        return lines_map

    def make_move(self, board):
        available = [i for i, x in enumerate(board) if x == ' ']
        if not available:
            return 0

        # 1. Check for immediate win
        for move in available:
            board[move] = self.symbol
            if self._check_win(board, self.symbol, move):
                board[move] = ' '
                return move
            board[move] = ' '

        # 2. Check for immediate block
        for move in available:
            board[move] = self.opponent
            if self._check_win(board, self.opponent, move):
                board[move] = ' '
                return move
            board[move] = ' '

        # 3. Minimax Search
        remaining = len(available)
        # Adaptive depth to ensure we finish within time limit
        if remaining > 16:
            depth_limit = 4
        elif remaining > 10:
            depth_limit = 6
        else:
            depth_limit = 8

        best_score = -float('inf')
        best_move = available[0]
        
        # Order moves by proximity to center to improve pruning
        available.sort(key=lambda x: abs(x // 5 - 2) + abs(x % 5 - 2))

        for move in available:
            board[move] = self.symbol
            score = self._minimax(board, 0, False, -float('inf'), float('inf'), depth_limit, move, self.symbol)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move

    def _check_win(self, board, player, last_move):
        for line in self.lines_map[last_move]:
            if board[line[0]] == board[line[1]] == board[line[2]] == player:
                return True
        return False

    def _minimax(self, board, depth, is_maximizing, alpha, beta, max_depth, last_move, player_who_moved):
        # Check if the last move resulted in a win
        if self._check_win(board, player_who_moved, last_move):
            if player_who_moved == self.symbol:
                return 10000 - depth
            else:
                return -10000 + depth
        
        # Check for draw
        if ' ' not in board:
            return 0
        
        # Depth limit reached
        if depth >= max_depth:
            return self._evaluate(board)
        
        available = [i for i, x in enumerate(board) if x == ' ']
        # Move ordering
        available.sort(key=lambda x: abs(x // 5 - 2) + abs(x % 5 - 2))
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in available:
                board[move] = self.symbol
                eval = self._minimax(board, depth + 1, False, alpha, beta, max_depth, move, self.symbol)
                board[move] = ' '
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available:
                board[move] = self.opponent
                eval = self._minimax(board, depth + 1, True, alpha, beta, max_depth, move, self.opponent)
                board[move] = ' '
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, board):
        score = 0
        for line in self.winning_lines:
            a, b, c = line
            vals = [board[a], board[b], board[c]]
            my_count = vals.count(self.symbol)
            opp_count = vals.count(self.opponent)
            
            if my_count == 2 and opp_count == 0:
                score += 100
            elif my_count == 1 and opp_count == 0:
                score += 10
            
            if opp_count == 2 and my_count == 0:
                score -= 100
            elif opp_count == 1 and my_count == 0:
                score -= 10
        return score
