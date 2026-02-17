"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3.5-plus-02-15
Run: 2
Generated: 2026-02-16 18:33:25
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_lines = []
        self.cell_to_lines = [[] for _ in range(25)]
        self._precompute_lines()

    def _precompute_lines(self):
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                line = (start, start + 1, start + 2)
                self.win_lines.append(line)
                for idx in line:
                    self.cell_to_lines[idx].append(line)
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                line = (start, start + 5, start + 10)
                self.win_lines.append(line)
                for idx in line:
                    self.cell_to_lines[idx].append(line)
        # Diagonals \
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                line = (start, start + 6, start + 12)
                self.win_lines.append(line)
                for idx in line:
                    self.cell_to_lines[idx].append(line)
        # Diagonals /
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                line = (start, start + 4, start + 8)
                self.win_lines.append(line)
                for idx in line:
                    self.cell_to_lines[idx].append(line)

    def _check_win(self, board, last_move):
        for line in self.cell_to_lines[last_move]:
            a, b, c = line
            if board[a] == board[b] == board[c] != ' ':
                return board[a]
        return None

    def _evaluate(self, board):
        score = 0
        for a, b, c in self.win_lines:
            v1, v2, v3 = board[a], board[b], board[c]
            # My potential
            if v1 == self.symbol and v2 == self.symbol and v3 == ' ': score += 10
            elif v1 == self.symbol and v3 == self.symbol and v2 == ' ': score += 10
            elif v2 == self.symbol and v3 == self.symbol and v1 == ' ': score += 10
            elif v1 == self.symbol and v2 == ' ' and v3 == ' ': score += 1
            elif v2 == self.symbol and v1 == ' ' and v3 == ' ': score += 1
            elif v3 == self.symbol and v1 == ' ' and v2 == ' ': score += 1
            
            # Opponent potential
            if v1 == self.opponent and v2 == self.opponent and v3 == ' ': score -= 10
            elif v1 == self.opponent and v3 == self.opponent and v2 == ' ': score -= 10
            elif v2 == self.opponent and v3 == self.opponent and v1 == ' ': score -= 10
            elif v1 == self.opponent and v2 == ' ' and v3 == ' ': score -= 1
            elif v2 == self.opponent and v1 == ' ' and v3 == ' ': score -= 1
            elif v3 == self.opponent and v1 == ' ' and v2 == ' ': score -= 1
        return score

    def _minimax(self, board, depth, is_maximizing, alpha, beta, last_move, empty_count):
        winner = self._check_win(board, last_move)
        if winner == self.symbol:
            return 10000 + depth
        if winner == self.opponent:
            return -10000 - depth
        if empty_count == 0 or depth == 0:
            return self._evaluate(board)

        moves = [i for i, x in enumerate(board) if x == ' ']
        # Move ordering: prioritize moves near the last move to improve pruning
        moves.sort(key=lambda x: abs(x - last_move))

        if is_maximizing:
            max_eval = -float('inf')
            for move in moves:
                board[move] = self.symbol
                eval = self._minimax(board, depth - 1, False, alpha, beta, move, empty_count - 1)
                board[move] = ' '
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                board[move] = self.opponent
                eval = self._minimax(board, depth - 1, True, alpha, beta, move, empty_count - 1)
                board[move] = ' '
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, board):
        available_moves = [i for i, x in enumerate(board) if x == ' ']
        if not available_moves:
            return 0
        
        empty_count = len(available_moves)

        # 1. Immediate Win
        for move in available_moves:
            board[move] = self.symbol
            if self._check_win(board, move) == self.symbol:
                board[move] = ' '
                return move
            board[move] = ' '

        # 2. Immediate Block
        for move in available_moves:
            board[move] = self.opponent
            if self._check_win(board, move) == self.opponent:
                board[move] = ' '
                return move
            board[move] = ' '

        # 3. Minimax Search
        best_score = -float('inf')
        best_move = available_moves[0]
        
        # Order root moves: Center first
        available_moves.sort(key=lambda x: abs(x - 12))
        
        # Dynamic depth based on branching factor to respect time limit
        search_depth = 4 if empty_count < 20 else 3
        
        for move in available_moves:
            board[move] = self.symbol
            score = self._minimax(board, search_depth - 1, False, -float('inf'), float('inf'), move, empty_count - 1)
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
