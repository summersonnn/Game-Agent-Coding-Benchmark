"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        
        # Precompute all winning lines (3-in-a-row) for the 5x5 grid
        self.win_lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 1, start + 2))
        # Columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 5, start + 10))
        # Diagonals (Down-Right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 6, start + 12))
        # Diagonals (Down-Left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_lines.append((start, start + 4, start + 8))

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not available_moves:
            return -1
        
        if len(available_moves) == 1:
            return available_moves[0]
            
        best_score = -10000000
        best_moves = []
        
        # Heuristic ordering: Center, Inner Ring, Others
        # This helps Alpha-Beta pruning cut off branches faster
        def move_priority(m):
            if m == 12: return 0
            # Check if cell is in the inner 3x3 ring
            if 6 <= m <= 18 and m % 5 in [1, 2, 3] and m // 5 in [1, 2, 3]: return 1
            return 2
            
        ordered_moves = sorted(available_moves, key=move_priority)
        
        for move in ordered_moves:
            board[move] = self.symbol
            # Depth 3 is chosen as a balance between performance and lookahead
            score = self.minimax(board, 3, -10000000, 10000000, False)
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
                
        return random.choice(best_moves)

    def minimax(self, board, depth, alpha, beta, is_maximizing):
        # Check for terminal states
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 10000 + depth # Win sooner is better
        if winner == self.opponent_symbol:
            return -10000 - depth # Lose later is better
            
        if depth == 0:
            return self.evaluate(board)
            
        moves = [i for i, spot in enumerate(board) if spot == ' ']
        if not moves:
            return 0 # Draw

        if is_maximizing:
            max_eval = -10000000
            for move in moves:
                board[move] = self.symbol
                eval_score = self.minimax(board, depth - 1, alpha, beta, False)
                board[move] = ' '
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 10000000
            for move in moves:
                board[move] = self.opponent_symbol
                eval_score = self.minimax(board, depth - 1, alpha, beta, True)
                board[move] = ' '
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def check_winner(self, board):
        for line in self.win_lines:
            if board[line[0]] == board[line[1]] == board[line[2]] != ' ':
                return board[line[0]]
        return None

    def evaluate(self, board):
        score = 0
        for line in self.win_lines:
            vals = [board[i] for i in line]
            my_count = vals.count(self.symbol)
            opp_count = vals.count(self.opponent_symbol)
            empty_count = vals.count(' ')
            
            if my_count == 3:
                score += 100
            elif my_count == 2 and empty_count == 1:
                score += 10
            elif my_count == 1 and empty_count == 2:
                score += 1
                
            if opp_count == 3:
                score -= 100
            elif opp_count == 2 and empty_count == 1:
                score -= 10
            elif opp_count == 1 and empty_count == 2:
                score -= 1
        return score
