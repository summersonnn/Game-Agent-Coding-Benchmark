"""
Agent Code: A5-Connect4RandomStart
Model: google-gemini-3-flash-preview
Run: 2
Generated: 2026-02-12 14:51:12
"""

import random

class Connect4Agent:
    def __init__(self, name, symbol):
        """
        Initialize the agent.
        name: str - The name of the agent.
        symbol: str - The character representing the agent's disc ('R' or 'Y').
        """
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
        self.rows = 6
        self.cols = 7

    def make_move(self, board):
        """
        Decide the next move using Minimax with Alpha-Beta pruning.
        Depth is set to 4 to ensure completion within the 1s time limit.
        """
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        
        # If only one move is possible, take it immediately
        if len(valid_moves) == 1:
            return valid_moves[0]

        best_score = -float('inf')
        best_col = random.choice(valid_moves)

        # Depth 4 provides a strong balance of lookahead and speed
        for col in valid_moves:
            temp_board = [row[:] for row in board]
            self._drop_piece(temp_board, col, self.symbol)
            score = self._minimax(temp_board, 4, -float('inf'), float('inf'), False)
            
            if score > best_score:
                best_score = score
                best_col = col

        return best_col

    def _minimax(self, board, depth, alpha, beta, maximizing_player):
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        is_terminal = self._is_terminal(board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if self._check_win(board, self.symbol):
                    return 10000000
                elif self._check_win(board, self.opponent_symbol):
                    return -10000000
                else: # Draw
                    return 0
            else:
                return self._score_board(board, self.symbol)

        if maximizing_player:
            value = -float('inf')
            for col in valid_moves:
                b_copy = [row[:] for row in board]
                self._drop_piece(b_copy, col, self.symbol)
                value = max(value, self._minimax(b_copy, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for col in valid_moves:
                b_copy = [row[:] for row in board]
                self._drop_piece(b_copy, col, self.opponent_symbol)
                value = min(value, self._minimax(b_copy, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def _drop_piece(self, board, col, symbol):
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return r, col
        return None

    def _check_win(self, board, s):
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == s and board[r][c+1] == s and board[r][c+2] == s and board[r][c+3] == s:
                    return True
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if board[r][c] == s and board[r+1][c] == s and board[r+2][c] == s and board[r+3][c] == s:
                    return True
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if board[r][c] == s and board[r-1][c+1] == s and board[r-2][c+2] == s and board[r-3][c+3] == s:
                    return True
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if board[r][c] == s and board[r+1][c+1] == s and board[r+2][c+2] == s and board[r+3][c+3] == s:
                    return True
        return False

    def _is_terminal(self, board):
        return self._check_win(board, self.symbol) or \
               self._check_win(board, self.opponent_symbol) or \
               all(board[0][c] != ' ' for c in range(self.cols))

    def _score_board(self, board, symbol):
        score = 0
        opp_symbol = self.opponent_symbol

        # Central Column Preference (Strategic weight)
        center_array = [board[r][self.cols//2] for r in range(self.rows)]
        center_count = center_array.count(symbol)
        score += center_count * 3

        # Score segments of 4
        for r in range(self.rows):
            row_array = board[r]
            for c in range(self.cols - 3):
                window = row_array[c:c+4]
                score += self._evaluate_window(window, symbol, opp_symbol)

        for c in range(self.cols):
            col_array = [board[r][c] for r in range(self.rows)]
            for r in range(self.rows - 3):
                window = col_array[r:r+4]
                score += self._evaluate_window(window, symbol, opp_symbol)

        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol, opp_symbol)

        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+3-i][c+i] for i in range(4)]
                score += self._evaluate_window(window, symbol, opp_symbol)

        return score

    def _evaluate_window(self, window, symbol, opp_symbol):
        score = 0
        if window.count(symbol) == 4:
            score += 1000
        elif window.count(symbol) == 3 and window.count(' ') == 1:
            score += 10
        elif window.count(symbol) == 2 and window.count(' ') == 2:
            score += 2

        if window.count(opp_symbol) == 3 and window.count(' ') == 1:
            score -= 80  # Heavily prioritize blocking opponent 3-in-a-rows
            
        return score