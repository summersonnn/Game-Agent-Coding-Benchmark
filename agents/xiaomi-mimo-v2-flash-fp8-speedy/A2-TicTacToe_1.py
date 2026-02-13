"""
Agent Code: A2-TicTacToe
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 1
Generated: 2026-02-13 14:53:21
"""

import time

import random
import time

class TicTacToeAgent:
    """
    A Tic Tac Toe agent that uses minimax with alpha-beta pruning and a depth limit.
    It checks for immediate wins and blocks, then uses search to select the best move.
    """
    # Precompute all winning lines (3-in-a-row) on a 5x5 board
    LINES = []
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        if not TicTacToeAgent.LINES:
            self._generate_lines()
    
    def _generate_lines(self):
        """Generate all 48 possible winning lines (3 consecutive cells)."""
        lines = []
        # Rows: 5 rows, each has 3 possible 3-in-a-row segments
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))
        # Columns: 5 columns, each has 3 possible segments
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))
        # Diagonals (down-right): 3x3 grid of starting positions
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))
        # Diagonals (down-left): 3x3 grid of starting positions
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))
        TicTacToeAgent.LINES = lines
    
    def get_empty_cells(self, board):
        """Return list of indices of empty cells."""
        return [i for i, cell in enumerate(board) if cell == ' ']
    
    def is_win(self, board, player):
        """Check if the player has a winning line."""
        for a, b, c in self.LINES:
            if board[a] == board[b] == board[c] == player:
                return True
        return False
    
    def evaluate(self, board, player):
        """Heuristic evaluation of the board from the perspective of the player."""
        opponent = 'O' if player == 'X' else 'X'
        score = 0.0
        
        for a, b, c in self.LINES:
            cells = [board[a], board[b], board[c]]
            p_count = cells.count(player)
            o_count = cells.count(opponent)
            
            if p_count == 3:
                return 1000  # Win
            if o_count == 3:
                return -1000  # Loss
            
            if p_count == 2 and o_count == 0:
                score += 10
            elif p_count == 1 and o_count == 0:
                score += 1
            elif o_count == 2 and p_count == 0:
                score -= 10
            elif o_count == 1 and p_count == 0:
                score -= 1
        
        # Small bonus for controlling center cells (more connections)
        center_indices = [6, 7, 8, 11, 12, 13, 16, 17, 18]
        for idx in center_indices:
            if board[idx] == player:
                score += 0.1
            elif board[idx] == opponent:
                score -= 0.1
        
        # Add tiny random noise to break ties
        score += random.uniform(-0.01, 0.01)
        return score
    
    def minimax(self, board, depth, alpha, beta, maximizing, player):
        """Minimax with alpha-beta pruning. Returns the evaluation score."""
        opponent = 'O' if player == 'X' else 'X'
        
        # Terminal state checks
        if self.is_win(board, player):
            return 1000 - depth  # Prefer faster wins
        if self.is_win(board, opponent):
            return -1000 + depth  # Prefer slower losses
        if depth == 0:
            return self.evaluate(board, player)
        
        empty_cells = self.get_empty_cells(board)
        if not empty_cells:
            return 0  # Draw
        
        if maximizing:
            best_score = -float('inf')
            for move in empty_cells:
                board[move] = player
                score = self.minimax(board, depth - 1, alpha, beta, False, player)
                board[move] = ' '
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score
        else:
            best_score = float('inf')
            for move in empty_cells:
                board[move] = opponent
                score = self.minimax(board, depth - 1, alpha, beta, True, player)
                board[move] = ' '
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score
    
    def get_winning_move(self, board, player):
        """Return a winning move if exists, else None."""
        for move in self.get_empty_cells(board):
            board[move] = player
            if self.is_win(board, player):
                board[move] = ' '
                return move
            board[move] = ' '
        return None
    
    def get_blocking_move(self, board, player):
        """Return a move that blocks opponent's immediate win, else None."""
        opponent = 'O' if player == 'X' else 'X'
        for move in self.get_empty_cells(board):
            board[move] = opponent
            if self.is_win(board, opponent):
                board[move] = ' '
                return move
            board[move] = ' '
        return None
    
    def make_move(self, board):
        """
        Choose the best move using minimax with a depth limit of 4.
        First checks for immediate win or block.
        """
        # 1. Check for immediate win
        win_move = self.get_winning_move(board, self.symbol)
        if win_move is not None:
            return win_move
        
        # 2. Check for immediate block
        block_move = self.get_blocking_move(board, self.symbol)
        if block_move is not None:
            return block_move
        
        # 3. Use minimax to select the best move
        empty_cells = self.get_empty_cells(board)
        if not empty_cells:
            return None  # Should not happen
        
        # Set depth limit: 4, but adjust if few empty cells
        depth = min(4, len(empty_cells))
        
        best_score = -float('inf')
        best_move = None
        
        # We are the maximizing player
        for move in empty_cells:
            board[move] = self.symbol
            score = self.minimax(board, depth - 1, -float('inf'), float('inf'), False, self.symbol)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        
        # Fallback: if no best move found (shouldn't happen), choose random
        if best_move is None:
            best_move = random.choice(empty_cells)
        
        return best_move
