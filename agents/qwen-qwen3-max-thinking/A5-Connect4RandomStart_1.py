"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-13 14:10:12
"""

import copy

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        opponent = 'Y' if self.symbol == 'R' else 'R'
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        if not valid_cols:
            return 0
        
        # Check for immediate winning move
        for col in valid_cols:
            if self._is_winning_move(board, col, self.symbol):
                return col
        
        # Check for opponent's immediate winning move (block)
        for col in valid_cols:
            if self._is_winning_move(board, col, opponent):
                return col
        
        # Search with negamax (depth=2 for 3-ply total search)
        ordered_cols = sorted(valid_cols, key=lambda c: abs(c - 3))
        best_col = ordered_cols[0]
        best_score = -10**9
        alpha = -10**9
        beta = 10**9
        
        for col in ordered_cols:
            new_board = copy.deepcopy(board)
            row = self._get_row(new_board, col)
            if row is None:
                continue
            new_board[row][col] = self.symbol
            if self._move_wins(new_board, row, col, self.symbol):
                score = 10**9
            else:
                score = -self._negamax(new_board, 2, -beta, -alpha, opponent)
            if score > best_score:
                best_score = score
                best_col = col
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break
        return best_col

    def _get_row(self, board, col):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                return r
        return None

    def _is_winning_move(self, board, col, player):
        temp_board = [row[:] for row in board]
        row = self._get_row(temp_board, col)
        if row is None:
            return False
        temp_board[row][col] = player
        return self._move_wins(temp_board, row, col, player)

    def _move_wins(self, board, row, col, player):
        # Horizontal
        count = 1
        c = col - 1
        while c >= 0 and board[row][c] == player:
            count += 1
            c -= 1
        c = col + 1
        while c < 7 and board[row][c] == player:
            count += 1
            c += 1
        if count >= 4:
            return True
        
        # Vertical (only downward - gravity ensures above is empty)
        count = 1
        r = row + 1
        while r < 6 and board[r][col] == player:
            count += 1
            r += 1
        if count >= 4:
            return True
        
        # Diagonal \ (down-right + up-left)
        count = 1
        r, c = row + 1, col + 1
        while r < 6 and c < 7 and board[r][c] == player:
            count += 1
            r += 1
            c += 1
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and board[r][c] == player:
            count += 1
            r -= 1
            c -= 1
        if count >= 4:
            return True
        
        # Diagonal / (down-left + up-right)
        count = 1
        r, c = row + 1, col - 1
        while r < 6 and c >= 0 and board[r][c] == player:
            count += 1
            r += 1
            c -= 1
        r, c = row - 1, col + 1
        while r >= 0 and c < 7 and board[r][c] == player:
            count += 1
            r -= 1
            c += 1
        if count >= 4:
            return True
        
        return False

    def _negamax(self, board, depth, alpha, beta, player):
        opponent = 'Y' if player == 'R' else 'R'
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        if not valid_cols:
            return 0
        if depth == 0:
            return self._evaluate_board(board, player)
        
        best_value = -10**9
        ordered_cols = sorted(valid_cols, key=lambda c: abs(c - 3))
        
        for col in ordered_cols:
            new_board = copy.deepcopy(board)
            row = self._get_row(new_board, col)
            if row is None:
                continue
            new_board[row][col] = player
            if self._move_wins(new_board, row, col, player):
                value = 10**9
            else:
                value = -self._negamax(new_board, depth - 1, -beta, -alpha, opponent)
            if value > best_value:
                best_value = value
            if best_value > alpha:
                alpha = best_value
            if alpha >= beta:
                break
        return best_value

    def _evaluate_board(self, board, player):
        opponent = 'Y' if player == 'R' else 'R'
        score = 0
        
        # Horizontal windows
        for r in range(6):
            for c in range(4):
                window = [board[r][c+i] for i in range(4)]
                score += self._evaluate_window(window, player, opponent)
        
        # Vertical windows
        for c in range(7):
            for r in range(3):
                window = [board[r+i][c] for i in range(4)]
                score += self._evaluate_window(window, player, opponent)
        
        # Diagonal \ windows
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window, player, opponent)
        
        # Diagonal / windows
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += self._evaluate_window(window, player, opponent)
        
        return score

    def _evaluate_window(self, window, player, opponent):
        count_player = window.count(player)
        count_opponent = window.count(opponent)
        count_empty = 4 - count_player - count_opponent
        
        if count_player == 4:
            return 10000
        elif count_player == 3 and count_empty == 1:
            return 100
        elif count_player == 2 and count_empty == 2:
            return 10
        elif count_player == 1 and count_empty == 3:
            return 1
        elif count_opponent == 4:
            return -10000
        elif count_opponent == 3 and count_empty == 1:
            return -100
        elif count_opponent == 2 and count_empty == 2:
            return -10
        elif count_opponent == 1 and count_empty == 3:
            return -1
        return 0