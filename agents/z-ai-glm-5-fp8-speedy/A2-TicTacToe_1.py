"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-5@preset/fp8-speedy
Run: 1
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        # Precompute all possible winning lines (triplets)
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
                lines.append((r * 5 + c, r * 5 + c + 5, r * 5 + c + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                lines.append((r * 5 + c, r * 5 + c + 6, r * 5 + c + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                lines.append((r * 5 + c, r * 5 + c + 4, r * 5 + c + 8))
        return lines

    def make_move(self, board):
        # 1. Check for immediate winning move
        for i in range(25):
            if board[i] == ' ':
                board[i] = self.symbol
                if self._check_win(board, self.symbol):
                    return i
                board[i] = ' ' # Undo

        # 2. Check for immediate blocking move
        for i in range(25):
            if board[i] == ' ':
                board[i] = self.opponent_symbol
                if self._check_win(board, self.opponent_symbol):
                    board[i] = ' ' # Undo
                    return i
                board[i] = ' ' # Undo

        # 3. Use Minimax with Alpha-Beta Pruning
        empty_count = board.count(' ')
        # Adjust depth based on game progress to ensure we stay within time limits
        depth = 4
        if empty_count < 15: 
            depth = 5
        if empty_count < 10: 
            depth = 6
        
        best_move = -1
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        # Order moves by proximity to center to improve pruning efficiency
        available_moves = [i for i, v in enumerate(board) if v == ' ']
        available_moves.sort(key=lambda x: abs(x // 5 - 2) + abs(x % 5 - 2))

        for move in available_moves:
            board[move] = self.symbol
            score = self._minimax(board, depth - 1, alpha, beta, False)
            board[move] = ' '
            
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
            
        return best_move

    def _minimax(self, board, depth, alpha, beta, is_maximizing):
        winner = self._get_winner(board)
        if winner is not None:
            if winner == self.symbol:
                # Add empty cells count to prioritize faster wins (Tie-Breaker)
                return 10000 + board.count(' ')
            elif winner == self.opponent_symbol:
                # Subtract empty cells count to prioritize later losses (Tie-Breaker)
                return -10000 - board.count(' ')
            else: # Draw
                return 0
        
        if depth == 0:
            return self._evaluate(board)

        available_moves = [i for i, v in enumerate(board) if v == ' ']
        available_moves.sort(key=lambda x: abs(x // 5 - 2) + abs(x % 5 - 2))

        if is_maximizing:
            max_eval = -float('inf')
            for move in available_moves:
                board[move] = self.symbol
                eval_val = self._minimax(board, depth - 1, alpha, beta, False)
                board[move] = ' '
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in available_moves:
                board[move] = self.opponent_symbol
                eval_val = self._minimax(board, depth - 1, alpha, beta, True)
                board[move] = ' '
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    def _check_win(self, board, player):
        for a, b, c in self.win_lines:
            if board[a] == player and board[b] == player and board[c] == player:
                return True
        return False

    def _get_winner(self, board):
        for a, b, c in self.win_lines:
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _evaluate(self, board):
        score = 0
        for a, b, c in self.win_lines:
            line = [board[a], board[b], board[c]]
            my_count = line.count(self.symbol)
            opp_count = line.count(self.opponent_symbol)
            
            if my_count > 0 and opp_count > 0:
                continue # Line is blocked, no value
            
            if my_count == 2:
                score += 50  # Strong threat
            elif my_count == 1:
                score += 5   # Potential
                
            if opp_count == 2:
                score -= 50  # Dangerous threat from opponent
            elif opp_count == 1:
                score -= 5   # Opponent potential
                
        return score
