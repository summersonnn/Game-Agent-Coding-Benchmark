"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder-next@preset/fp8
Run: 1
Generated: 2026-02-14 16:45:38
"""



import random

EMPTY = ' '

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return None

        # If it's the very first move (only one empty cell is marked, rest empty),
        # and it's not the center, prefer center (position 12)
        empty_count = len(available_moves)
        if empty_count == 24:  # First move for X (engine placed one mark)
            # Find the engine's random first move
            first_move = next(i for i, c in enumerate(board) if c != EMPTY)
            if first_move == 12:
                # Center is already taken, pick corner or edge strategically
                corners = [0, 4, 20, 24]
                available_corners = [c for c in corners if c in available_moves]
                if available_corners:
                    return random.choice(available_corners)
                # Fallback to center-adjacent
                adjacents = [6, 7, 8, 11, 13, 16, 17, 18]
                return random.choice([a for a in adjacents if a in available_moves])
            else:
                # Prefer center if possible
                if 12 in available_moves:
                    return 12
                # Otherwise prefer corners
                corners = [0, 4, 20, 24]
                available_corners = [c for c in corners if c in available_moves]
                if available_corners:
                    return random.choice(available_corners)

        # Minimax with alpha-beta pruning and depth limit for larger board
        def minimax(board, depth, alpha, beta, is_maximizing):
            winner = self.check_winner(board)
            if winner == self.symbol:
                return 1000 - depth
            elif winner == self.opponent_symbol:
                return -1000 + depth
            elif winner == 'DRAW':
                return 0
            
            if depth >= 3:  # Limited depth for performance
                return self.evaluate_board(board)

            if is_maximizing:
                max_eval = float('-inf')
                for move in [i for i, spot in enumerate(board) if spot == EMPTY]:
                    board[move] = self.symbol
                    eval_score = minimax(board, depth + 1, alpha, beta, False)
                    board[move] = EMPTY
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
                return max_eval
            else:
                min_eval = float('inf')
                for move in [i for i, spot in enumerate(board) if spot == EMPTY]:
                    board[move] = self.opponent_symbol
                    eval_score = minimax(board, depth + 1, alpha, beta, True)
                    board[move] = EMPTY
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
                return min_eval

        # First check for immediate win or block
        # Check if we can win in one move
        for move in available_moves:
            board[move] = self.symbol
            if self.check_winner(board) == self.symbol:
                board[move] = EMPTY
                return move
            board[move] = EMPTY
        
        # Check if opponent can win in one move and block
        for move in available_moves:
            board[move] = self.opponent_symbol
            if self.check_winner(board) == self.opponent_symbol:
                board[move] = EMPTY
                return move
            board[move] = EMPTY

        # If no immediate tactical moves, use minimax for strategic moves
        best_move = None
        best_value = float('-inf')
        
        # Sort moves by heuristics to improve pruning
        moves = sorted(available_moves, key=lambda m: self.move_priority(board, m), reverse=True)
        
        for move in moves:
            board[move] = self.symbol
            value = minimax(board, 0, float('-inf'), float('inf'), False)
            board[move] = EMPTY
            
            if value > best_value:
                best_value = value
                best_move = move
        
        # If no good move found (shouldn't happen), pick random
        return best_move if best_move is not None else random.choice(available_moves)

    def check_winner(self, board):
        win_conditions = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                win_conditions.append((start, start + 4, start + 8))

        for combo in win_conditions:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        if EMPTY not in board:
            return 'DRAW'
        return None

    def evaluate_board(self, board):
        score = 0
        
        # Evaluate all potential winning lines
        win_conditions = []
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 1, start + 2))
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 5, start + 10))
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 6, start + 12))
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                win_conditions.append((start, start + 4, start + 8))

        for combo in win_conditions:
            line = [board[i] for i in combo]
            x_count = line.count(self.symbol)
            o_count = line.count(self.opponent_symbol)
            
            if x_count > 0 and o_count == 0:
                score += 10 ** x_count
            elif o_count > 0 and x_count == 0:
                score -= 10 ** o_count
        
        # Bonus for center control
        if board[12] == self.symbol:
            score += 50
        elif board[12] == self.opponent_symbol:
            score -= 50
            
        # Bonus for corners
        corners = [0, 4, 20, 24]
        for corner in corners:
            if board[corner] == self.symbol:
                score += 10
            elif board[corner] == self.opponent_symbol:
                score -= 10
        
        return score

    def move_priority(self, board, move):
        # Prioritize moves that are central or create threats
        priority = 0
        
        # Center is most valuable
        if move == 12:
            priority += 50
        
        # Corners next
        if move in [0, 4, 20, 24]:
            priority += 20
        
        # Edges adjacent to center
        if move in [6, 7, 8, 11, 13, 16, 17, 18]:
            priority += 10
        
        # Check if this move creates a two-in-a-row opportunity
        board[move] = self.symbol
        if self.check_two_in_row(board, self.symbol):
            priority += 30
        board[move] = EMPTY
        
        # Check if opponent would get two-in-a-row if we don't play here
        board[move] = self.opponent_symbol
        if self.check_two_in_row(board, self.opponent_symbol):
            priority += 40
        board[move] = EMPTY
        
        return priority

    def check_two_in_row(self, board, symbol):
        win_conditions = []
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 1, start + 2))
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 5, start + 10))
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 6, start + 12))
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                win_conditions.append((start, start + 4, start + 8))

        for combo in win_conditions:
            line = [board[i] for i in combo]
            if line.count(symbol) == 2 and line.count(EMPTY) == 1:
                return True
        return False
