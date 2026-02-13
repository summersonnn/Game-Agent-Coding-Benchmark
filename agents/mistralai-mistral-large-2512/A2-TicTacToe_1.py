"""
Agent Code: A2-TicTacToe
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        # Precompute all possible winning lines for faster checking
        self.win_lines = self._generate_win_lines()

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

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']

        # If only one move available, take it
        if len(available_moves) == 1:
            return available_moves[0]

        # Check for immediate winning move
        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.symbol
            if self._check_win(temp_board, self.symbol):
                return move

        # Block opponent's immediate winning move
        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.opponent_symbol
            if self._check_win(temp_board, self.opponent_symbol):
                return move

        # Center control is important in 5x5 board
        center_moves = [12, 6, 8, 16, 18]
        for move in center_moves:
            if move in available_moves:
                return move

        # Use minimax with alpha-beta pruning for optimal move
        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        # Limit depth for performance (especially important in 5x5 board)
        depth_limit = 3 if len(available_moves) > 15 else 5

        for move in available_moves:
            new_board = board.copy()
            new_board[move] = self.symbol
            score = self._minimax(new_board, depth_limit - 1, False, alpha, beta)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break

        return best_move if best_move is not None else random.choice(available_moves)

    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 10 + depth  # Prefer faster wins
        elif winner == self.opponent_symbol:
            return -10 - depth  # Prefer slower losses
        elif winner == 'DRAW' or depth == 0:
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for move in [i for i, spot in enumerate(board) if spot == ' ']:
                new_board = board.copy()
                new_board[move] = self.symbol
                score = self._minimax(new_board, depth - 1, False, alpha, beta)
                best_score = max(score, best_score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score
        else:
            best_score = float('inf')
            for move in [i for i, spot in enumerate(board) if spot == ' ']:
                new_board = board.copy()
                new_board[move] = self.opponent_symbol
                score = self._minimax(new_board, depth - 1, True, alpha, beta)
                best_score = min(score, best_score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score

    def _check_win(self, board, player):
        for line in self.win_lines:
            if all(board[pos] == player for pos in line):
                return True
        return False

    def _check_winner(self, board):
        for player in [self.symbol, self.opponent_symbol]:
            if self._check_win(board, player):
                return player
        if ' ' not in board:
            return 'DRAW'
        return None
