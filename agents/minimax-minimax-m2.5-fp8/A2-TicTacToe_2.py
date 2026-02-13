"""
Agent Code: A2-TicTacToe
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_lines = self._generate_win_lines()
        self.center_squares = [6, 7, 8, 11, 12, 13, 16, 17, 18]
    
    def _generate_win_lines(self):
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                lines.append((r * 5 + c, r * 5 + c + 1, r * 5 + c + 2))
        # Columns
        for c in range(5):
            for r in range(3):
                lines.append((r * 5 + c, (r + 1) * 5 + c, (r + 2) * 5 + c))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                lines.append((r * 5 + c, (r + 1) * 5 + c + 1, (r + 2) * 5 + c + 2))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                lines.append((r * 5 + c, (r + 1) * 5 + c - 1, (r + 2) * 5 + c - 2))
        return lines
    
    def _get_line_state(self, line, board):
        counts = {self.symbol: 0, self.opponent: 0, ' ': 0}
        for idx in line:
            counts[board[idx]] += 1
        return counts
    
    def make_move(self, board):
        empty_moves = [i for i in range(25) if board[i] == ' ']
        
        if not empty_moves:
            return None
        
        # Priority 1: Check for winning move
        for move in empty_moves:
            for line in self.win_lines:
                if move in line and all(board[idx] == self.symbol for idx in line if idx != move):
                    # This move completes a win
                    if all(board[idx] == self.symbol or idx == move for idx in line):
                        return move
        
        # Priority 2: Check for blocking move
        for move in empty_moves:
            for line in self.win_lines:
                if move in line:
                    # Check if opponent would win with this move
                    would_win = True
                    for idx in line:
                        if idx != move and board[idx] != self.opponent:
                            would_win = False
                            break
                    if would_win:
                        return move
        
        # Priority 3: Evaluate positions using heuristic scoring
        best_score = -1
        best_move = empty_moves[0]
        
        for move in empty_moves:
            score = 0
            for line in self.win_lines:
                if move in line:
                    line_state = self._get_line_state(line, board)
                    
                    # Prioritize moves that create two in a row with open end
                    if line_state[self.symbol] == 2 and line_state[' '] == 1:
                        score += 10
                    # Block opponent's two in a row
                    elif line_state[self.opponent] == 2 and line_state[' '] == 1:
                        score += 5
                    # Slight preference for center squares
                    elif move in self.center_squares:
                        score += 2
            
            if score > best_score:
                best_score = score
                best_move = move
            elif score == best_score and move in self.center_squares:
                best_move = move
        
        return best_move
