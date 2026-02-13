"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-code-fast-1
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    """
    TicTacToeAgent implementation with a strategy to prioritize winning moves,
    blocking opponent wins, and selecting moves based on a heuristic score.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        # Precompute all possible winning lines (three in a row)
        self.win_lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                self.win_lines.append((r*5 + c, r*5 + c + 1, r*5 + c + 2))
        # Columns
        for c in range(5):
            for r in range(3):
                self.win_lines.append((r*5 + c, (r+1)*5 + c, (r+2)*5 + c))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                self.win_lines.append((r*5 + c, (r+1)*5 + (c+1), (r+2)*5 + (c+2)))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                self.win_lines.append((r*5 + c, (r+1)*5 + (c-1), (r+2)*5 + (c-2)))

    def make_move(self, board):
        available_moves = [i for i in range(25) if board[i] == ' ']
        if not available_moves:
            return None  # Though unlikely
        
        # 1. Check for immediate win
        for move in available_moves:
            if self.is_winning(board, move, self.symbol):
                return move
        
        # 2. Check for blocking opponent's win
        for move in available_moves:
            if self.is_winning(board, move, self.opponent):
                return move
        
        # 3. Otherwise, choose the move with the highest heuristic score
        best_move = None
        best_score = -1
        for move in available_moves:
            score = self.evaluate_move(board, move)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def is_winning(self, board, position, symbol):
        # Temporarily place the symbol and check if it wins
        original = board[position]
        board[position] = symbol
        won = any(all(board[i] == symbol for i in line) for line in self.win_lines)
        board[position] = original  # Revert
        return won

    def evaluate_move(self, board, move):
        score = 0
        # Bonus for center (position 12)
        if move == 12:
            score += 5
        # Evaluate based on potential in lines containing the move
        for line in self.win_lines:
            if move in line:
                cells = [board[i] for i in line]
                my_count = cells.count(self.symbol)
                opp_count = cells.count(self.opponent)
                empty_count = cells.count(' ')
                if opp_count == 0:  # No opponent marks in the line
                    if my_count == 1 and empty_count == 2:
                        score += 1  # Potential for one in a row
                    elif my_count == 2 and empty_count == 1:
                        score += 10  # Near win
        return score
