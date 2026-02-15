"""
Agent Code: A2-TicTacToe
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 1
Generated: 2026-02-13 14:53:21
"""

import time

import random
import time

class TicTacToeAgent:
    """
    Advanced Tic Tac Toe agent using minimax with alpha-beta pruning,
    pattern recognition, and strategic positioning for 5x5 board.
    """
    
    # Precomputed winning patterns for 5x5 board (3 in a row)
    WINNING_PATTERNS = []
    
    # Generate all winning patterns
    @classmethod
    def _generate_patterns(cls):
        if cls.WINNING_PATTERNS:
            return
        
        # Horizontal patterns
        for row in range(5):
            for col in range(3):
                pattern = [row * 5 + col, row * 5 + col + 1, row * 5 + col + 2]
                cls.WINNING_PATTERNS.append(tuple(pattern))
        
        # Vertical patterns
        for col in range(5):
            for row in range(3):
                pattern = [row * 5 + col, (row + 1) * 5 + col, (row + 2) * 5 + col]
                cls.WINNING_PATTERNS.append(tuple(pattern))
        
        # Diagonal down-right patterns
        for row in range(3):
            for col in range(3):
                pattern = [row * 5 + col, (row + 1) * 5 + col + 1, (row + 2) * 5 + col + 2]
                cls.WINNING_PATTERNS.append(tuple(pattern))
        
        # Diagonal down-left patterns
        for row in range(3):
            for col in range(2, 5):
                pattern = [row * 5 + col, (row + 1) * 5 + col - 1, (row + 2) * 5 + col - 2]
                cls.WINNING_PATTERNS.append(tuple(pattern))
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self._generate_patterns()
        
        # Strategic positions (center and near-center are valuable)
        self.position_values = [
            1, 1, 1, 1, 1,
            1, 2, 2, 2, 1,
            1, 2, 3, 2, 1,
            1, 2, 2, 2, 1,
            1, 1, 1, 1, 1
        ]
        
        # Time management
        self.start_time = 0
        self.time_limit = 0.95  # 95% of 1 second limit
        
        # Opening book for common patterns
        self.opening_book = {
            'X': self._x_opening_moves,
            'O': self._o_opening_moves
        }
    
    def make_move(self, board):
        """Main move decision method with fallback to random move."""
        self.start_time = time.time()
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        
        if not empty_cells:
            return None
        
        # Early game: use opening book for first few moves
        move_count = 25 - len(empty_cells)
        if move_count <= 4:
            opening_move = self._try_opening_book(board)
            if opening_move is not None:
                return opening_move
        
        # Always check for immediate win or block
        immediate_move = self._find_immediate_win_or_block(board)
        if immediate_move is not None:
            return immediate_move
        
        # Use minimax for deeper search
        best_move = self._minimax_decision(board, empty_cells)
        if best_move is not None:
            return best_move
        
        # Fallback: strategic move based on heuristics
        return self._strategic_move(board, empty_cells)
            
    def _try_opening_book(self, board):
        """Try to find a good opening move from precomputed patterns."""
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        move_count = 25 - len(empty_cells)
        
        if move_count == 1 and self.symbol == 'X':
            # First move for X (after random placement by engine)
            # Look for strategic response
            x_pos = board.index('X')
            # If X is in corner, take opposite corner or center
            if x_pos in [0, 4, 20, 24]:
                return 12  # Center is usually best
            # If X is on edge, take center
            elif x_pos in [2, 7, 11, 13, 17, 22]:
                return 12
            # If X is in center, take a corner
            elif x_pos == 12:
                return 0
        
        elif move_count == 1 and self.symbol == 'O':
            # First move for O - respond to X's random placement
            x_pos = board.index('X')
            # If X is in center, take a corner
            if x_pos == 12:
                return 0
            # Otherwise, take center if available
            elif board[12] == ' ':
                return 12
            # If center taken, take opposite corner
            else:
                opposite_corners = {0: 24, 4: 20, 20: 4, 24: 0}
                if x_pos in opposite_corners and board[opposite_corners[x_pos]] == ' ':
                    return opposite_corners[x_pos]
        
        return None
    
    def _find_immediate_win_or_block(self, board):
        """Check for immediate winning move or opponent's threat."""
        # Check for winning move
        for pattern in self.WINNING_PATTERNS:
            cells = [board[i] for i in pattern]
            if cells.count(self.symbol) == 2 and cells.count(' ') == 1:
                empty_idx = pattern[cells.index(' ')]
                return empty_idx
        
        # Check for blocking opponent's winning move
        for pattern in self.WINNING_PATTERNS:
            cells = [board[i] for i in pattern]
            if cells.count(self.opponent) == 2 and cells.count(' ') == 1:
                empty_idx = pattern[cells.index(' ')]
                return empty_idx
        
        return None
    
    def _minimax_decision(self, board, empty_cells):
        """Use minimax with alpha-beta pruning to find best move."""
        if time.time() - self.start_time > self.time_limit:
            return None  # Timeout, fallback to heuristic
        
        # Limit search depth based on remaining cells and time
        depth = min(4, len(empty_cells))
        if len(empty_cells) > 15:
            depth = min(3, depth)
        
        best_score = -float('inf')
        best_moves = []
        
        # Evaluate each possible move
        for move in empty_cells:
            if time.time() - self.start_time > self.time_limit:
                break
                
            new_board = board.copy()
            new_board[move] = self.symbol
            
            score = self._minimax(new_board, depth - 1, False, -float('inf'), float('inf'))
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        
        if best_moves:
            # Choose best move, preferring center and strategic positions
            best_moves.sort(key=lambda m: self.position_values[m], reverse=True)
            return best_moves[0]
        
        return None
    
    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with alpha-beta pruning."""
        if depth == 0 or self._is_terminal(board):
            return self._evaluate_board(board)
        
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in empty_cells:
                new_board = board.copy()
                new_board[move] = self.symbol
                eval_score = self._minimax(new_board, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in empty_cells:
                new_board = board.copy()
                new_board[move] = self.opponent
                eval_score = self._minimax(new_board, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    def _is_terminal(self, board):
        """Check if game is over."""
        # Check for win
        for pattern in self.WINNING_PATTERNS:
            if (board[pattern[0]] == board[pattern[1]] == board[pattern[2]] and 
                board[pattern[0]] != ' '):
                return True
        
        # Check for draw
        return ' ' not in board
    
    def _evaluate_board(self, board):
        """Evaluate board state with heuristic scoring."""
        # Terminal state evaluation
        winner = self._check_winner(board)
        if winner == self.symbol:
            return 1000
        elif winner == self.opponent:
            return -1000
        elif winner == 'DRAW':
            return 0
        
        # Heuristic evaluation
        score = 0
        
        # Evaluate each winning pattern
        for pattern in self.WINNING_PATTERNS:
            cells = [board[i] for i in pattern]
            my_count = cells.count(self.symbol)
            opp_count = cells.count(self.opponent)
            empty_count = cells.count(' ')
            
            if my_count == 2 and empty_count == 1:
                score += 10  # Two in a row with open third
            elif opp_count == 2 and empty_count == 1:
                score -= 9   # Block opponent's two in a row (slightly less than creating our own)
            elif my_count == 1 and empty_count == 2:
                score += 1   # Potential for future two in a row
            elif opp_count == 1 and empty_count == 2:
                score -= 1   # Opponent's potential
        
        # Position value bonus
        for i in range(25):
            if board[i] == self.symbol:
                score += self.position_values[i] * 0.1
            elif board[i] == self.opponent:
                score -= self.position_values[i] * 0.1
        
        # Mobility bonus (more moves available is good)
        empty_cells = sum(1 for cell in board if cell == ' ')
        score += empty_cells * 0.01
        
        return score
    
    def _check_winner(self, board):
        """Check if there's a winner on the board."""
        for pattern in self.WINNING_PATTERNS:
            if (board[pattern[0]] == board[pattern[1]] == board[pattern[2]] and 
                board[pattern[0]] != ' '):
                return board[pattern[0]]
        
        if ' ' not in board:
            return 'DRAW'
        
        return None
    
    def _strategic_move(self, board, empty_cells):
        """Fallback strategic move selection."""
        # Try to create a fork (multiple winning threats)
        fork_move = self._find_fork_opportunity(board)
        if fork_move is not None:
            return fork_move
        
        # Try to block opponent's potential fork
        block_fork = self._find_fork_block(board)
        if block_fork is not None:
            return block_fork
        
        # Choose move with highest position value
        empty_cells.sort(key=lambda x: self.position_values[x], reverse=True)
        
        # Prefer moves that create opportunities
        for move in empty_cells:
            # Check if this move creates a two-in-a-row
            new_board = board.copy()
            new_board[move] = self.symbol
            if self._count_potential_wins(new_board, self.symbol) > 0:
                return move
        
        # Default to highest value position
        return empty_cells[0] if empty_cells else None
    
    def _find_fork_opportunity(self, board):
        """Find a move that creates multiple winning threats."""
        for move in [i for i, cell in enumerate(board) if cell == ' ']:
            new_board = board.copy()
            new_board[move] = self.symbol
            if self._count_potential_wins(new_board, self.symbol) >= 2:
                return move
        return None
    
    def _find_fork_block(self, board):
        """Find a move that blocks opponent's potential fork."""
        for move in [i for i, cell in enumerate(board) if cell == ' ']:
            new_board = board.copy()
            new_board[move] = self.opponent
            if self._count_potential_wins(new_board, self.opponent) >= 2:
                # This move would give opponent a fork, so block it
                return move
        return None
    
    def _count_potential_wins(self, board, player):
        """Count how many ways player can win on next move."""
        count = 0
        for pattern in self.WINNING_PATTERNS:
            cells = [board[i] for i in pattern]
            if cells.count(player) == 2 and cells.count(' ') == 1:
                count += 1
        return count
    
    # Opening move strategies
    def _x_opening_moves(self, board, move_count):
        """Opening strategy for X."""
        # Already handled in _try_opening_book
        return None
    
    def _o_opening_moves(self, board, move_count):
        """Opening strategy for O."""
        # Already handled in _try_opening_book
        return None
