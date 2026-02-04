"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 4
Generated: 2026-02-04 16:49:47
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        opponent_symbol = 'O' if self.symbol == 'X' else 'X'

        def get_winner(board):
            win_conditions = [
                (0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6)
            ]
            for (a, b, c) in win_conditions:
                if board[a] != EMPTY and board[a] == board[b] == board[c]:
                    return board[a]
            if EMPTY not in board:
                return 'DRAW'
            return None

        def minimax(board, depth, alpha, beta, is_maximizing):
            winner = get_winner(board)
            if winner == self.symbol:
                return 10 - depth
            elif winner == opponent_symbol:
                return depth - 10
            elif winner == 'DRAW':
                return 0

            available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
            if is_maximizing:
                max_eval = -float('inf')
                for move in available_moves:
                    board[move] = self.symbol
                    eval = minimax(board, depth + 1, alpha, beta, False)
                    board[move] = EMPTY
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
                return max_eval
            else:
                min_eval = float('inf')
                for move in available_moves:
                    board[move] = opponent_symbol
                    eval = minimax(board, depth + 1, alpha, beta, True)
                    board[move] = EMPTY
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
                return min_eval

        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return None

        best_score = -float('inf')
        best_move = None
        alpha = -float('inf')
        beta = float('inf')
        for move in available_moves:
            board[move] = self.symbol
            score = minimax(board, 1, alpha, beta, False)
            board[move] = EMPTY

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_move
