"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.lines = self._get_all_lines()
        self.cell_lines = self._get_cell_lines()
        self.cell_values = self._compute_cell_values()
    
    def _get_all_lines(self):
        lines = []
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))
        return lines
    
    def _get_cell_lines(self):
        cell_lines = [[] for _ in range(25)]
        for line in self.lines:
            for cell in line:
                cell_lines[cell].append(line)
        return cell_lines
    
    def _compute_cell_values(self):
        cell_values = [0] * 25
        for line in self.lines:
            for cell in line:
                cell_values[cell] += 1
        return cell_values
    
    def make_move(self, board):
        available = [i for i, cell in enumerate(board) if cell == ' ']
        if not available:
            return None
        
        for move in available:
            if self.is_winning_move(board, move):
                return move
        
        opponent = 'O' if self.symbol == 'X' else 'X'
        for move in available:
            if self.is_opponent_winning_move(board, move, opponent):
                return move
        
        for move in available:
            if self.creates_fork(board, move):
                return move
        
        best_value = -1
        best_moves = []
        for move in available:
            value = self.cell_values[move]
            if value > best_value:
                best_value = value
                best_moves = [move]
            elif value == best_value:
                best_moves.append(move)
        return random.choice(best_moves)
    
    def is_winning_move(self, board, move):
        for line in self.cell_lines[move]:
            count = 0
            for cell in line:
                if cell == move:
                    continue
                if board[cell] == self.symbol:
                    count += 1
            if count == 2:
                return True
        return False
    
    def is_opponent_winning_move(self, board, move, opponent):
        for line in self.cell_lines[move]:
            count = 0
            for cell in line:
                if cell == move:
                    continue
                if board[cell] == opponent:
                    count += 1
            if count == 2:
                return True
        return False
    
    def creates_fork(self, board, move):
        fork_count = 0
        for line in self.cell_lines[move]:
            count = 0
            empty_count = 0
            for cell in line:
                if cell == move:
                    count += 1
                else:
                    if board[cell] == self.symbol:
                        count += 1
                    elif board[cell] == ' ':
                        empty_count += 1
            if count == 2 and empty_count == 1:
                fork_count += 1
                if fork_count >= 2:
                    return True
        return False
