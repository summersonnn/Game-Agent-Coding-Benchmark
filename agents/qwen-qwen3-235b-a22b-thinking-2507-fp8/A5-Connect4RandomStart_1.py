"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-12 14:50:42
"""

import time

import time
import random

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'Y' if symbol == 'R' else 'R'
    
    def copy_board(self, board):
        return [row[:] for row in board]
    
    def drop_disc(self, board, col, disc):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = disc
                return
    
    def check_winner(self, board):
        # Horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return board[r][c]
        # Vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return board[r][c]
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return board[r][c]
        # Diagonal \
        for r in range(3):
            for c in range(4):
                if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return board[r][c]
        return None

    def is_full(self, board):
        return all(board[0][c] != ' ' for c in range(7))
    
    def count_empty(self, board):
        count = 0
        for r in range(6):
            for c in range(7):
                if board[r][c] == ' ':
                    count += 1
        return count

    def evaluate_window(self, window, player, opponent):
        if opponent in window and player in window:
            return 0
        count = window.count(player)
        if count > 0:
            if count == 4:
                return 10000
            elif count == 3:
                return 100
            elif count == 2:
                return 10
            elif count == 1:
                return 1
        count_opp = window.count(opponent)
        if count_opp > 0:
            if count_opp == 4:
                return -10000
            elif count_opp == 3:
                return -100
            elif count_opp == 2:
                return -10
            elif count_opp == 1:
                return -1
        return 0

    def evaluate(self, board, player):
        opponent = 'Y' if player == 'R' else 'R'
        score = 0
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c + i] for i in range(4)]
                score += self.evaluate_window(window, player, opponent)
        # Vertical
        for r in range(3):
            for c in range(7):
                window = [board[r + i][c] for i in range(4)]
                score += self.evaluate_window(window, player, opponent)
        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r + i][c + i] for i in range(4)]
                score += self.evaluate_window(window, player, opponent)
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                window = [board[r - i][c + i] for i in range(4)]
                score += self.evaluate_window(window, player, opponent)
        return score

    def minimax(self, board, depth, alpha, beta, maximizing_player, start_time, time_limit):
        if time.time() - start_time > time_limit:
            return None
        
        winner = self.check_winner(board)
        if winner:
            empty = self.count_empty(board)
            X = max(empty, 3)
            if winner == self.symbol:
                return 100000 + X
            else:
                return -(100000 + X)
        
        if self.is_full(board):
            return 0
        
        if depth == 0:
            return self.evaluate(board, self.symbol)
        
        valid_moves = [col for col in range(7) if board[0][col] == ' ']
        valid_moves.sort(key=lambda col: abs(col - 3))
        
        if maximizing_player:
            value = -10**18
            for col in valid_moves:
                board_copy = self.copy_board(board)
                self.drop_disc(board_copy, col, self.symbol)
                child_value = self.minimax(board_copy, depth - 1, alpha, beta, False, start_time, time_limit)
                if child_value is None:
                    return None
                if child_value > value:
                    value = child_value
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:
            value = 10**18
            for col in valid_moves:
                board_copy = self.copy_board(board)
                self.drop_disc(board_copy, col, self.opponent_symbol)
                child_value = self.minimax(board_copy, depth - 1, alpha, beta, True, start_time, time_limit)
                if child_value is None:
                    return None
                if child_value < value:
                    value = child_value
                if value < beta:
                    beta = value
                if beta <= alpha:
                    break
            return value

    def make_move(self, board):
        immediate_win_moves = []
        blocking_moves = []
        valid_moves = []
        for col in range(7):
            if board[0][col] != ' ':
                continue
            valid_moves.append(col)
            board_copy = self.copy_board(board)
            self.drop_disc(board_copy, col, self.symbol)
            if self.check_winner(board_copy) == self.symbol:
                immediate_win_moves.append(col)
            board_copy2 = self.copy_board(board)
            self.drop_disc(board_copy2, col, self.opponent_symbol)
            if self.check_winner(board_copy2) == self.opponent_symbol:
                blocking_moves.append(col)
        
        if immediate_win_moves:
            return immediate_win_moves[0]
        if blocking_moves:
            return blocking_moves[0]
        
        if not valid_moves:
            return random.choice(range(7))
        
        start_time = time.time()
        time_limit = 0.9
        best_move = None
        
        for depth in range(1, 15):
            current_best_move = None
            current_best_value = -10**18
            moves = valid_moves[:]
            if best_move is not None and best_move in moves:
                moves.remove(best_move)
                moves = [best_move] + moves
            else:
                moves.sort(key=lambda col: abs(col - 3))
            
            for col in moves:
                board_copy = self.copy_board(board)
                self.drop_disc(board_copy, col, self.symbol)
                value = self.minimax(board_copy, depth - 1, -10**18, 10**18, False, start_time, time_limit)
                if value is None:
                    break
                if value > current_best_value:
                    current_best_value = value
                    current_best_move = col
            else:
                best_move = current_best_move
                continue
            break
        
        if best_move is None:
            return random.choice(valid_moves)
        return best_move
