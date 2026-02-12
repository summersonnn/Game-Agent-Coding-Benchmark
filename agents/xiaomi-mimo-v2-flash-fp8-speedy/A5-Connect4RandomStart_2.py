"""
Agent Code: A5-Connect4RandomStart
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 2
Generated: 2026-02-12 14:50:42
"""



import random

class Connect4Agent:
    LINES = None
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        if Connect4Agent.LINES is None:
            Connect4Agent.LINES = self._precompute_lines()
    
    def _precompute_lines(self):
        lines = []
        # Horizontal
        for r in range(6):
            for c in range(4):
                lines.append([(r, c), (r, c+1), (r, c+2), (r, c+3)])
        # Vertical
        for r in range(3):
            for c in range(7):
                lines.append([(r, c), (r+1, c), (r+2, c), (r+3, c)])
        # Diagonal \
        for r in range(3):
            for c in range(4):
                lines.append([(r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)])
        # Diagonal /
        for r in range(3, 6):
            for c in range(4):
                lines.append([(r, c), (r-1, c+1), (r-2, c+2), (r-3, c+3)])
        return lines

    def get_valid_moves(self, board):
        return [col for col in range(7) if board[0][col] == ' ']
    
    def simulate_move(self, board, col, player):
        new_board = [row[:] for row in board]
        for r in range(5, -1, -1):
            if new_board[r][col] == ' ':
                new_board[r][col] = player
                return new_board
        return None
    
    def check_win_for_player(self, board, player):
        for line in self.LINES:
            if all(board[r][c] == player for (r, c) in line):
                return True
        return False
    
    def is_terminal(self, board):
        if all(board[0][col] != ' ' for col in range(7)):
            return True
        if self.check_win_for_player(board, self.symbol):
            return True
        opponent = 'Y' if self.symbol == 'R' else 'R'
        if self.check_win_for_player(board, opponent):
            return True
        return False
    
    def evaluate_board(self, board, player):
        opponent = 'Y' if player == 'R' else 'R'
        if self.check_win_for_player(board, player):
            return 100000
        if self.check_win_for_player(board, opponent):
            return -100000
        if all(board[0][col] != ' ' for col in range(7)):
            return 0
        
        score = 0
        for line in self.LINES:
            cells = [board[r][c] for (r, c) in line]
            player_count = cells.count(player)
            opponent_count = cells.count(opponent)
            empty_count = cells.count(' ')
            
            if player_count > 0 and opponent_count > 0:
                continue
                
            if player_count == 3 and empty_count == 1:
                score += 100
            elif player_count == 2 and empty_count == 2:
                score += 10
            elif player_count == 1 and empty_count == 3:
                score += 1
                
            if opponent_count == 3 and empty_count == 1:
                score -= 100
            elif opponent_count == 2 and empty_count == 2:
                score -= 10
            elif opponent_count == 1 and empty_count == 3:
                score -= 1
                
        return score

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        if depth == 0 or self.is_terminal(board):
            return self.evaluate_board(board, self.symbol), None
        
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return 0, None
        
        if maximizing_player:
            best_value = -float('inf')
            best_move = random.choice(valid_moves)
            for col in valid_moves:
                new_board = self.simulate_move(board, col, self.symbol)
                value, _ = self.minimax(new_board, depth-1, alpha, beta, False)
                if value > best_value:
                    best_value = value
                    best_move = col
                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break
            return best_value, best_move
        else:
            best_value = float('inf')
            best_move = random.choice(valid_moves)
            opponent = 'Y' if self.symbol == 'R' else 'R'
            for col in valid_moves:
                new_board = self.simulate_move(board, col, opponent)
                value, _ = self.minimax(new_board, depth-1, alpha, beta, True)
                if value < best_value:
                    best_value = value
                    best_move = col
                beta = min(beta, best_value)
                if beta <= alpha:
                    break
            return best_value, best_move

    def make_move(self, board):
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return 0
        
        # Check for immediate win
        for col in valid_moves:
            new_board = self.simulate_move(board, col, self.symbol)
            if self.check_win_for_player(new_board, self.symbol):
                return col
        
        # Check for immediate block
        opponent = 'Y' if self.symbol == 'R' else 'R'
        for col in valid_moves:
            new_board = self.simulate_move(board, col, opponent)
            if self.check_win_for_player(new_board, opponent):
                return col
        
        # Use minimax for deeper strategy
        _, best_move = self.minimax(board, 4, -float('inf'), float('inf'), True)
        if best_move is None:
            best_move = random.choice(valid_moves)
        return best_move
