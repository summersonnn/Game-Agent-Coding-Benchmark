"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-coder@preset/fp8
Run: 2
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    """
    An AI agent for 5x5 Tic Tac Toe that uses minimax with alpha-beta pruning
    to make intelligent moves.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'

    def make_move(self, board):
        """
        Return the index (0-24) of the cell you want to mark.
        board: List of 25 strings representing the current board state.
              Each element is ' ' (empty), 'X', or 'O'.
        """
        # Check for winning move
        win_move = self.find_winning_move(board, self.symbol)
        if win_move is not None:
            return win_move
            
        # Check for blocking opponent's winning move
        block_move = self.find_winning_move(board, self.opponent_symbol)
        if block_move is not None:
            return block_move
            
        # Use minimax for deeper strategy
        try:
            move = self.minimax(board, 3, True, float('-inf'), float('inf'))[1]
            if move is not None and board[move] == ' ':
                return move
        except:
            pass
            
        # Fallback to available moves
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        return random.choice(available_moves) if available_moves else None

    def find_winning_move(self, board, player):
        """Find a move that results in an immediate win for the player."""
        for i in range(25):
            if board[i] == ' ':
                new_board = board[:]
                new_board[i] = player
                if self.check_winner(new_board) == player:
                    return i
        return None

    def check_winner(self, board):
        """Check if there's a winner on the board."""
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
        return None

    def evaluate_board(self, board):
        """Evaluate the board position."""
        winner = self.check_winner(board)
        if winner == self.symbol:
            return 100
        elif winner == self.opponent_symbol:
            return -100
        elif winner == 'DRAW' or ' ' not in board:
            return 0
            
        # Heuristic evaluation based on potential winning lines
        score = 0
        win_patterns = []
        
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                win_patterns.append([start, start + 1, start + 2])
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                win_patterns.append([start, start + 5, start + 10])
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                win_patterns.append([start, start + 6, start + 12])
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                win_patterns.append([start, start + 4, start + 8])
                
        for pattern in win_patterns:
            symbols = [board[i] for i in pattern]
            player_count = symbols.count(self.symbol)
            opponent_count = symbols.count(self.opponent_symbol)
            empty_count = symbols.count(' ')
            
            # Only consider lines that are still winnable
            if player_count > 0 and opponent_count == 0:
                score += 10 ** player_count
            elif opponent_count > 0 and player_count == 0:
                score -= 10 ** opponent_count
                
        return score

    def minimax(self, board, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with alpha-beta pruning."""
        winner = self.check_winner(board)
        if depth == 0 or winner is not None or ' ' not in board:
            if winner == self.symbol:
                return 100 + depth, None
            elif winner == self.opponent_symbol:
                return -100 - depth, None
            elif winner == 'DRAW' or ' ' not in board:
                return 0, None
            else:
                return self.evaluate_board(board), None

        best_move = None
        
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(25):
                if board[i] == ' ':
                    board[i] = self.symbol
                    eval_score, _ = self.minimax(board, depth - 1, False, alpha, beta)
                    board[i] = ' '  # Undo move
                    
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = i
                        
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for i in range(25):
                if board[i] == ' ':
                    board[i] = self.opponent_symbol
                    eval_score, _ = self.minimax(board, depth - 1, True, alpha, beta)
                    board[i] = ' '  # Undo move
                    
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = i
                        
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            return min_eval, best_move
