"""
Agent Code: A2-TicTacToe
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        # Generate win conditions
        self.win_conditions = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 5, start + 10))
        # Diag down-right
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_conditions.append((start, start + 6, start + 12))
        # Diag down-left
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_conditions.append((start, start + 4, start + 8))

    def check_winner(self, board):
        for combo in self.win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        if ' ' not in board:
            return 'DRAW'
        return None

    def evaluate(self, board):
        my_score = 0
        opp_score = 0
        for combo in self.win_conditions:
            marks = [board[p] for p in combo]
            own = sum(1 for m in marks if m == self.symbol)
            opp = sum(1 for m in marks if m == self.opponent)
            if own > 0 and opp > 0:
                continue
            if own > 0:
                my_score += 10 ** own
            if opp > 0:
                opp_score += 10 ** opp
        return my_score - opp_score

    def minimax(self, board, depth, alpha, beta, maximizing):
        winner = self.check_winner(board)
        if winner is not None:
            empty_cells = board.count(' ')
            if winner == self.symbol:
                return 1000 + max(empty_cells, 3)
            elif winner == self.opponent:
                return -(1000 + max(empty_cells, 3))
            elif winner == 'DRAW':
                return 0
        if depth == 0:
            return self.evaluate(board)
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if maximizing:
            max_eval = float('-inf')
            for move in available_moves:
                board[move] = self.symbol
                eval_ = self.minimax(board, depth - 1, alpha, beta, False)
                board[move] = ' '
                max_eval = max(max_eval, eval_)
                alpha = max(alpha, eval_)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available_moves:
                board[move] = self.opponent
                eval_ = self.minimax(board, depth - 1, alpha, beta, True)
                board[move] = ' '
                min_eval = min(min_eval, eval_)
                beta = min(beta, eval_)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return None
        num_empty = len(available_moves)
        if num_empty > 20:
            max_depth = 3
        elif num_empty > 12:
            max_depth = 4
        elif num_empty > 6:
            max_depth = 5
        else:
            max_depth = 7
        best_score = float('-inf')
        best_move = None
        for move in available_moves:
            board[move] = self.symbol
            score = self.minimax(board, max_depth - 1, float('-inf'), float('inf'), False)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
