"""
Agent Code: A5-Connect4RandomStart
Model: z-ai/glm-5@preset/fp8-speedy
Run: 2
Generated: 2026-02-12 14:50:42
"""

import time

class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'Y' if symbol == 'R' else 'R'
        self.rows = 6
        self.cols = 7
        self.time_limit = 0.95

    def make_move(self, board):
        self.start_time = time.time()
        
        valid_moves = [c for c in range(self.cols) if board[0][c] == ' ']
        if not valid_moves:
            return 0

        # Move ordering: center columns are usually better
        move_order = {3: 0, 2: 1, 4: 1, 1: 2, 5: 2, 0: 3, 6: 3}
        valid_moves.sort(key=lambda x: move_order[x])

        # Check for immediate win or block
        for col in valid_moves:
            row = self.get_next_open_row(board, col)
            board[row][col] = self.symbol
            if self.check_win(board, self.symbol):
                return col
            board[row][col] = ' '

        for col in valid_moves:
            row = self.get_next_open_row(board, col)
            board[row][col] = self.opponent
            if self.check_win(board, self.opponent):
                return col
            board[row][col] = ' '

        best_move = valid_moves[0]
        
        # Iterative Deepening
        for depth in range(1, 20):
            if time.time() - self.start_time > self.time_limit * 0.8:
                break
            
            try:
                current_move, _ = self.minimax(board, depth, -float('inf'), float('inf'), True, valid_moves)
                if current_move is not None:
                    best_move = current_move
            except TimeoutError:
                break
            except Exception:
                # Defensive: if unexpected error in minimax, fallback to current best
                break
                
        return best_move

    def minimax(self, board, depth, alpha, beta, maximizing_player, valid_moves):
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError()

        # Terminal checks
        if self.check_win(board, self.symbol):
            return None, 10000000 + depth
        if self.check_win(board, self.opponent):
            return None, -10000000 - depth
        
        current_valid_moves = [c for c in valid_moves if board[0][c] == ' ']
        
        if depth == 0 or not current_valid_moves:
            return None, self.score_position(board)

        # Re-order moves for pruning efficiency
        move_order = {3: 0, 2: 1, 4: 1, 1: 2, 5: 2, 0: 3, 6: 3}
        current_valid_moves.sort(key=lambda x: move_order[x])

        if maximizing_player:
            value = -float('inf')
            best_col = current_valid_moves[0]
            for col in current_valid_moves:
                row = self.get_next_open_row(board, col)
                board[row][col] = self.symbol
                _, score = self.minimax(board, depth - 1, alpha, beta, False, current_valid_moves)
                board[row][col] = ' '
                
                if score > value:
                    value = score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = float('inf')
            best_col = current_valid_moves[0]
            for col in current_valid_moves:
                row = self.get_next_open_row(board, col)
                board[row][col] = self.opponent
                _, score = self.minimax(board, depth - 1, alpha, beta, True, current_valid_moves)
                board[row][col] = ' '
                
                if score < value:
                    value = score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value

    def get_next_open_row(self, board, col):
        for r in range(self.rows - 1, -1, -1):
            if board[r][col] == ' ':
                return r
        return -1

    def check_win(self, board, symbol):
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if all(board[r][c+i] == symbol for i in range(4)):
                    return True
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if all(board[r+i][c] == symbol for i in range(4)):
                    return True
        # Diagonal /
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if all(board[r-i][c+i] == symbol for i in range(4)):
                    return True
        # Diagonal \
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if all(board[r+i][c+i] == symbol for i in range(4)):
                    return True
        return False

    def score_position(self, board):
        score = 0

        # Center column preference
        center_col = 3
        center_array = [board[r][center_col] for r in range(self.rows)]
        center_count = center_array.count(self.symbol)
        score += center_count * 3

        # Horizontal
        for r in range(self.rows):
            row_array = [board[r][c] for c in range(self.cols)]
            for c in range(self.cols - 3):
                window = row_array[c:c+4]
                score += self.evaluate_window(window)

        # Vertical
        for c in range(self.cols):
            col_array = [board[r][c] for r in range(self.rows)]
            for r in range(self.rows - 3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window)

        # Positive Diagonal
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window)

        # Negative Diagonal
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window)

        return score

    def evaluate_window(self, window):
        score = 0
        my_piece = self.symbol
        opp_piece = self.opponent

        if window.count(my_piece) == 4:
            score += 100
        elif window.count(my_piece) == 3 and window.count(' ') == 1:
            score += 5
        elif window.count(my_piece) == 2 and window.count(' ') == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(' ') == 1:
            score -= 4

        return score