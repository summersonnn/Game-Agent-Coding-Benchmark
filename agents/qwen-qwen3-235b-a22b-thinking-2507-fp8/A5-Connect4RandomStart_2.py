"""
Agent Code: A5-Connect4RandomStart
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-12 14:50:42
"""



class Connect4Agent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        for col in range(7):
            if board[0][col] != ' ':
                continue
            board_sim = [row[:] for row in board]
            r = self.drop_disc(board_sim, col, self.symbol)
            if r is None:
                continue
            if self.check_win(board_sim, self.symbol):
                return col
        
        valid_cols = [col for col in range(7) if board[0][col] == ' ']
        if not valid_cols:
            return 0
        
        max_depth = 4
        best_move = valid_cols[0]
        best_value = -10**9
        alpha = -10**9
        beta = 10**9
        
        for col in valid_cols:
            board_sim = [row[:] for row in board]
            r = self.drop_disc(board_sim, col, self.symbol)
            if r is None:
                continue
            value = self.minimax(board_sim, 1, alpha, beta, False, self.symbol, max_depth)
            if value > best_value:
                best_value = value
                best_move = col
            if value > alpha:
                alpha = value
            if beta <= alpha:
                break
        return best_move

    def minimax(self, board, depth, alpha, beta, is_maximizing, root_symbol, max_depth):
        root_opponent = 'Y' if root_symbol == 'R' else 'R'
        if self.check_win(board, root_symbol):
            return 100000
        if self.check_win(board, root_opponent):
            return -100000
        if self.is_full(board):
            return 0
        
        if depth == max_depth:
            return self.evaluate(board, root_symbol)
        
        current_symbol = root_symbol if is_maximizing else root_opponent
        
        if is_maximizing:
            max_eval = -10**9
            for col in range(7):
                if board[0][col] != ' ':
                    continue
                r = self.drop_disc(board, col, current_symbol)
                if self.check_win(board, current_symbol):
                    board[r][col] = ' '
                    return 100000
                eval = self.minimax(board, depth + 1, alpha, beta, False, root_symbol, max_depth)
                board[r][col] = ' '
                if eval > max_eval:
                    max_eval = eval
                if eval > alpha:
                    alpha = eval
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 10**9
            for col in range(7):
                if board[0][col] != ' ':
                    continue
                r = self.drop_disc(board, col, current_symbol)
                if self.check_win(board, current_symbol):
                    board[r][col] = ' '
                    return -100000
                eval = self.minimax(board, depth + 1, alpha, beta, True, root_symbol, max_depth)
                board[r][col] = ' '
                if eval < min_eval:
                    min_eval = eval
                if eval < beta:
                    beta = eval
                if beta <= alpha:
                    break
            return min_eval

    def evaluate(self, board, root_symbol):
        root_opponent = 'Y' if root_symbol == 'R' else 'R'
        score = 0
        
        for r in range(6):
            for c in range(4):
                segment = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]]
                count_root = segment.count(root_symbol)
                count_opp = segment.count(root_opponent)
                if count_root > 0 and count_opp > 0:
                    continue
                if count_opp == 0:
                    if count_root == 3:
                        score += 100
                    elif count_root == 2:
                        score += 10
                    elif count_root == 1:
                        score += 1
                if count_root == 0:
                    if count_opp == 3:
                        score -= 100
                    elif count_opp == 2:
                        score -= 10
                    elif count_opp == 1:
                        score -= 1
        
        for r in range(3):
            for c in range(7):
                segment = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]]
                count_root = segment.count(root_symbol)
                count_opp = segment.count(root_opponent)
                if count_root > 0 and count_opp > 0:
                    continue
                if count_opp == 0:
                    if count_root == 3:
                        score += 100
                    elif count_root == 2:
                        score += 10
                    elif count_root == 1:
                        score += 1
                if count_root == 0:
                    if count_opp == 3:
                        score -= 100
                    elif count_opp == 2:
                        score -= 10
                    elif count_opp == 1:
                        score -= 1
        
        for r in range(3, 6):
            for c in range(4):
                segment = [board[r][c], board[r-1][c+1], board[r-2][c+2], board[r-3][c+3]]
                count_root = segment.count(root_symbol)
                count_opp = segment.count(root_opponent)
                if count_root > 0 and count_opp > 0:
                    continue
                if count_opp == 0:
                    if count_root == 3:
                        score += 100
                    elif count_root == 2:
                        score += 10
                    elif count_root == 1:
                        score += 1
                if count_root == 0:
                    if count_opp == 3:
                        score -= 100
                    elif count_opp == 2:
                        score -= 10
                    elif count_opp == 1:
                        score -= 1
        
        for r in range(3):
            for c in range(4):
                segment = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]]
                count_root = segment.count(root_symbol)
                count_opp = segment.count(root_opponent)
                if count_root > 0 and count_opp > 0:
                    continue
                if count_opp == 0:
                    if count_root == 3:
                        score += 100
                    elif count_root == 2:
                        score += 10
                    elif count_root == 1:
                        score += 1
                if count_root == 0:
                    if count_opp == 3:
                        score -= 100
                    elif count_opp == 2:
                        score -= 10
                    elif count_opp == 1:
                        score -= 1
        
        return score

    def drop_disc(self, board, col, symbol):
        for r in range(5, -1, -1):
            if board[r][col] == ' ':
                board[r][col] = symbol
                return r
        return None

    def check_win(self, board, symbol):
        for r in range(6):
            for c in range(4):
                if board[r][c] == symbol and board[r][c+1] == symbol and board[r][c+2] == symbol and board[r][c+3] == symbol:
                    return True
        for r in range(3):
            for c in range(7):
                if board[r][c] == symbol and board[r+1][c] == symbol and board[r+2][c] == symbol and board[r+3][c] == symbol:
                    return True
        for r in range(3, 6):
            for c in range(4):
                if board[r][c] == symbol and board[r-1][c+1] == symbol and board[r-2][c+2] == symbol and board[r-3][c+3] == symbol:
                    return True
        for r in range(3):
            for c in range(4):
                if board[r][c] == symbol and board[r+1][c+1] == symbol and board[r+2][c+2] == symbol and board[r+3][c+3] == symbol:
                    return True
        return False

    def is_full(self, board):
        return all(board[0][c] != ' ' for c in range(7))
