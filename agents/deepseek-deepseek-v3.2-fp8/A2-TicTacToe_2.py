"""
Agent Code: A2-TicTacToe
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-13 14:53:21
"""

import math

import math
import random

class TicTacToeAgent:
    """
    Advanced TicTacToe agent for 5x5 board with 3-in-a-row win condition.
    Implements minimax with alpha-beta pruning, pattern recognition, and strategic positioning.
    """
    
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        
        # Precompute all winning lines for 5x5 board with 3-in-a-row
        self.win_lines = self._generate_win_lines()
        
        # Strategic positions (center and corners are valuable)
        self.center_cells = [6, 7, 8, 11, 12, 13, 16, 17, 18]
        self.corner_cells = [0, 4, 20, 24]
        self.edge_centers = [2, 10, 14, 22]
        
        # Opening book for first few moves
        self.opening_moves = self._generate_opening_book()
        self.move_count = 0
        
        # Difficulty levels (adjustable)
        self.max_depth = 3  # Depth for minimax search
        self.use_opening_book = True
        
    def _generate_win_lines(self):
        """Generate all possible winning lines (3-in-a-row) for 5x5 board."""
        lines = []
        
        # Horizontal lines
        for row in range(5):
            for col in range(3):
                start = row * 5 + col
                lines.append([start, start + 1, start + 2])
        
        # Vertical lines
        for col in range(5):
            for row in range(3):
                start = row * 5 + col
                lines.append([start, start + 5, start + 10])
        
        # Main diagonals (down-right)
        for row in range(3):
            for col in range(3):
                start = row * 5 + col
                lines.append([start, start + 6, start + 12])
        
        # Anti-diagonals (down-left)
        for row in range(3):
            for col in range(2, 5):
                start = row * 5 + col
                lines.append([start, start + 4, start + 8])
        
        return lines
    
    def _generate_opening_book(self):
        """Generate opening moves based on common TicTacToe strategies."""
        openings = {}
        
        # As X (first player after random placement)
        openings['X'] = [
            # If center is available, take it
            lambda board: 12 if board[12] == ' ' else None,
            # Otherwise take strong corner
            lambda board: 0 if board[0] == ' ' else 4 if board[4] == ' ' else 20 if board[20] == ' ' else 24,
            # Develop towards center
            lambda board: self._find_best_development_move(board)
        ]
        
        # As O (second player)
        openings['O'] = [
            # Counter opponent's first move
            lambda board: self._counter_opening_move(board),
            # Take center if available
            lambda board: 12 if board[12] == ' ' else None,
            # Block obvious threats
            lambda board: self._find_urgent_block(board)
        ]
        
        return openings
    
    def _counter_opening_move(self, board):
        """Find good counter move in opening as O."""
        # Find where X has played
        x_positions = [i for i, cell in enumerate(board) if cell == 'X']
        
        if len(x_positions) == 1:
            x_pos = x_positions[0]
            
            # If X is in center, take a corner
            if x_pos == 12:
                return random.choice(self.corner_cells)
            
            # If X is in corner, take opposite corner or center
            if x_pos in self.corner_cells:
                opposite_corners = {0: 24, 4: 20, 20: 4, 24: 0}
                return opposite_corners.get(x_pos, 12)
            
            # If X is on edge, take center
            if x_pos in self.edge_centers:
                return 12
        
        return None
    
    def _find_best_development_move(self, board):
        """Find good development move in early game."""
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        
        # Prioritize moves that create multiple threats
        for cell in empty_cells:
            if self._count_potential_threats(board, cell, self.symbol) >= 2:
                return cell
        
        # Otherwise, take a strategic position
        for cell in [12, 0, 4, 20, 24, 6, 8, 16, 18]:
            if cell in empty_cells:
                return cell
        
        return random.choice(empty_cells)
    
    def _count_potential_threats(self, board, cell, symbol):
        """Count how many winning lines would be threatened by placing symbol at cell."""
        temp_board = board.copy()
        temp_board[cell] = symbol
        count = 0
        
        for line in self.win_lines:
            if cell in line:
                cells = [temp_board[i] for i in line]
                if cells.count(symbol) == 2 and cells.count(' ') == 1:
                    count += 1
        
        return count
    
    def _find_urgent_block(self, board):
        """Find urgent blocking move."""
        # Check if opponent has immediate win
        for line in self.win_lines:
            cells = [board[i] for i in line]
            if cells.count(self.opponent) == 2 and cells.count(' ') == 1:
                for i in line:
                    if board[i] == ' ':
                        return i
        
        # Check if we can create fork (two threats at once)
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        for cell in empty_cells:
            if self._count_potential_threats(board, cell, self.symbol) >= 2:
                return cell
        
        return None
    
    def make_move(self, board: list[str]) -> int:
        """Main method to choose the best move."""
        self.move_count += 1
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        
        # Handle edge case
        if not empty_cells:
            return 0
        
        # Use opening book for first few moves
        if self.use_opening_book and self.move_count <= 3:
            opening_moves = self.opening_moves[self.symbol]
            for move_func in opening_moves:
                move = move_func(board)
                if move is not None and board[move] == ' ':
                    return move
        
        # Check for immediate win
        win_move = self._find_winning_move(board, self.symbol)
        if win_move is not None:
            return win_move
        
        # Check for immediate block
        block_move = self._find_winning_move(board, self.opponent)
        if block_move is not None:
            return block_move
        
        # Use minimax with alpha-beta pruning for deeper search
        if len(empty_cells) <= 12:  # Use deeper search in mid/end game
            best_move = self._minimax_ab(board, self.max_depth, -math.inf, math.inf, True)[1]
            if best_move is not None:
                return best_move
        
        # Fallback to heuristic evaluation
        return self._heuristic_move(board)
    
    def _find_winning_move(self, board, symbol):
        """Find a move that would win immediately."""
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        
        for cell in empty_cells:
            temp_board = board.copy()
            temp_board[cell] = symbol
            if self._check_winner(temp_board) == symbol:
                return cell
        
        return None
    
    def _check_winner(self, board):
        """Check if there's a winner on the board."""
        for line in self.win_lines:
            a, b, c = line
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        
        if ' ' not in board:
            return 'DRAW'
        
        return None
    
    def _minimax_ab(self, board, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        winner = self._check_winner(board)
        
        if winner == self.symbol:
            return (100 + depth, None)  # Prefer faster wins
        elif winner == self.opponent:
            return (-100 - depth, None)  # Prefer slower losses
        elif winner == 'DRAW':
            return (0, None)
        
        if depth == 0:
            return (self._evaluate_board(board), None)
        
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        
        if maximizing:
            best_score = -math.inf
            best_move = None
            
            for move in empty_cells:
                new_board = board.copy()
                new_board[move] = self.symbol
                score = self._minimax_ab(new_board, depth - 1, alpha, beta, False)[0]
                
                if score > best_score:
                    best_score = score
                    best_move = move
                
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return (best_score, best_move)
        else:
            best_score = math.inf
            best_move = None
            
            for move in empty_cells:
                new_board = board.copy()
                new_board[move] = self.opponent
                score = self._minimax_ab(new_board, depth - 1, alpha, beta, True)[0]
                
                if score < best_score:
                    best_score = score
                    best_move = move
                
                beta = min(beta, best_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return (best_score, best_move)
    
    def _evaluate_board(self, board):
        """Evaluate board state with heuristic scoring."""
        score = 0
        
        # Evaluate each winning line
        for line in self.win_lines:
            line_cells = [board[i] for i in line]
            my_count = line_cells.count(self.symbol)
            opp_count = line_cells.count(self.opponent)
            empty_count = line_cells.count(' ')
            
            if opp_count == 0:
                # Line is not blocked by opponent
                if my_count == 2 and empty_count == 1:
                    score += 50  # One move from win
                elif my_count == 1 and empty_count == 2:
                    score += 10  # Potential threat
                elif my_count == 0 and empty_count == 3:
                    score += 1   # Open line
            
            if my_count == 0:
                # Opponent has potential in this line
                if opp_count == 2 and empty_count == 1:
                    score -= 40  # Need to block
                elif opp_count == 1 and empty_count == 2:
                    score -= 5   # Opponent threat
        
        # Positional evaluation
        center_bonus = 3
        corner_bonus = 2
        edge_bonus = 1
        
        for cell in self.center_cells:
            if board[cell] == self.symbol:
                score += center_bonus
            elif board[cell] == self.opponent:
                score -= center_bonus
        
        for cell in self.corner_cells:
            if board[cell] == self.symbol:
                score += corner_bonus
            elif board[cell] == self.opponent:
                score -= corner_bonus
        
        # Mobility - number of available moves
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        score += len(empty_cells) * 0.5  # Slight preference for keeping options open
        
        return score
    
    def _heuristic_move(self, board):
        """Choose move based on heuristic evaluation when minimax isn't used."""
        empty_cells = [i for i, cell in enumerate(board) if cell == ' ']
        
        # If very few moves left, check all possibilities
        if len(empty_cells) <= 5:
            best_score = -math.inf
            best_move = empty_cells[0]
            
            for move in empty_cells:
                new_board = board.copy()
                new_board[move] = self.symbol
                score = self._evaluate_board(new_board)
                
                if score > best_score:
                    best_score = score
                    best_move = move
            
            return best_move
        
        # Otherwise use pattern-based heuristics
        # 1. Try to create forks
        for cell in empty_cells:
            if self._count_potential_threats(board, cell, self.symbol) >= 2:
                return cell
        
        # 2. Try to block opponent forks
        for cell in empty_cells:
            temp_board = board.copy()
            temp_board[cell] = self.opponent
            if self._count_potential_threats(temp_board, cell, self.opponent) >= 2:
                return cell
        
        # 3. Take center if available
        if 12 in empty_cells:
            return 12
        
        # 4. Take corners
        corners = [cell for cell in self.corner_cells if cell in empty_cells]
        if corners:
            return random.choice(corners)
        
        # 5. Take edge centers
        edges = [cell for cell in self.edge_centers if cell in empty_cells]
        if edges:
            return random.choice(edges)
        
        # 6. Fallback to random move
        return random.choice(empty_cells)
