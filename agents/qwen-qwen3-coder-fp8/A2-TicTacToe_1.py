"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder@preset/fp8
Run: 1
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        # Check for winning move
        for i in range(25):
            if board[i] == ' ':
                board[i] = self.symbol
                if self._check_winner(board, self.symbol):
                    board[i] = ' '  # Reset the board
                    return i
                board[i] = ' '  # Reset the board

        # Block opponent's winning move
        for i in range(25):
            if board[i] == ' ':
                board[i] = self.opponent_symbol
                if self._check_winner(board, self.opponent_symbol):
                    board[i] = ' '  # Reset the board
                    return i
                board[i] = ' '  # Reset the board

        # If no immediate win or block, use minimax with depth limit
        best_score = -float('inf')
        best_move = None
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        
        if not available_moves:
            return None
            
        # If it's the first move and we're O, take center if available
        if board.count('X') == 1 and board.count('O') == 0:
            if board[12] == ' ':
                return 12
            # Otherwise take a corner
            corners = [0, 4, 20, 24]
            available_corners = [c for c in corners if board[c] == ' ']
            if available_corners:
                return random.choice(available_corners)

        # Try to take center if available
        if board[12] == ' ':
            return 12
            
        # Use minimax with depth limit for better performance
        for move in available_moves:
            board[move] = self.symbol
            score = self._minimax(board, 4, False)  # Depth limit of 4
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
                
        if best_move is not None:
            return best_move
            
        # Fallback to random move
        return random.choice(available_moves) if available_moves else None

    def _minimax(self, board, depth, is_maximizing):
        winner = self._check_game_state(board)
        if winner == self.symbol:
            return 10 + depth
        elif winner == self.opponent_symbol:
            return -10 - depth
        elif winner == 'DRAW' or depth == 0:
            return 0
            
        if is_maximizing:
            best_score = -float('inf')
            for i in range(25):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self._minimax(board, depth - 1, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(25):
                if board[i] == ' ':
                    board[i] = self.opponent_symbol
                    score = self._minimax(board, depth - 1, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            return best_score

    def _check_game_state(self, board):
        # Check for winner
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
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        if ' ' not in board:
            return 'DRAW'
        return None

    def _check_winner(self, board, player):
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
            if board[combo[0]] == board[combo[1]] == board[combo[2]] == player:
                return True
        return False
