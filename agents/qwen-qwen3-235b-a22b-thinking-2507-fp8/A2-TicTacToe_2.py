"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-11 21:03:27
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    @staticmethod
    def check_winner(board):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for combo in win_conditions:
            a, b, c = combo
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    @staticmethod
    def minimax(board, depth, alpha, beta, is_maximizing, agent_symbol):
        winner = TicTacToeAgent.check_winner(board)
        opponent_symbol = 'X' if agent_symbol == 'O' else 'O'
        
        if winner == agent_symbol:
            empty_cells = board.count(' ')
            return 10 + empty_cells
        elif winner == opponent_symbol:
            empty_cells = board.count(' ')
            return -(10 + empty_cells)
        elif winner == 'DRAW':
            return 0

        available_moves = [i for i, cell in enumerate(board) if cell == ' ']
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in available_moves:
                new_board = board.copy()
                new_board[move] = agent_symbol
                eval = TicTacToeAgent.minimax(new_board, depth + 1, alpha, beta, False, agent_symbol)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available_moves:
                new_board = board.copy()
                new_board[move] = opponent_symbol
                eval = TicTacToeAgent.minimax(new_board, depth + 1, alpha, beta, True, agent_symbol)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return random.choice(available_moves) if available_moves else None

        for move in available_moves:
            new_board = board.copy()
            new_board[move] = self.symbol
            if TicTacToeAgent.check_winner(new_board) == self.symbol:
                return move

        opponent_symbol = 'X' if self.symbol == 'O' else 'O'
        for move in available_moves:
            new_board = board.copy()
            new_board[move] = opponent_symbol
            if TicTacToeAgent.check_winner(new_board) == opponent_symbol:
                return move

        best_score = -float('inf')
        best_move = available_moves[0]
        alpha = -float('inf')
        beta = float('inf')
        
        for move in available_moves:
            new_board = board.copy()
            new_board[move] = self.symbol
            score = TicTacToeAgent.minimax(new_board, 0, alpha, beta, False, self.symbol)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
        
        return best_move
