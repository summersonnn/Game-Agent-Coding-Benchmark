"""
Agent Code: A2-TicTacToe
Model: anthropic/claude-haiku-4.5
Run: 1
Generated: 2026-02-13 14:53:21
"""



import random

EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'


class TicTacToeAgent:
    """
    Intelligent Tic Tac Toe agent using a combination of heuristics and minimax.
    """
    # Pre-compute all winning combinations once
    WIN_CONDITIONS = []
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = O_MARK if symbol == X_MARK else X_MARK
        
        # Initialize WIN_CONDITIONS on first instance
        if not TicTacToeAgent.WIN_CONDITIONS:
            TicTacToeAgent.WIN_CONDITIONS = self._generate_win_conditions()
        
        # Center positions with bonus values
        self.center_bonus = {
            6: 2, 7: 3, 8: 2,
            11: 3, 12: 5, 13: 3,
            16: 2, 17: 3, 18: 2
        }
    
    @staticmethod
    def _generate_win_conditions():
        """Generate all possible winning combinations."""
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
        return win_conditions
    
    def make_move(self, board):
        """Return the best move for the current board state."""
        # Priority 1: Try to win immediately
        winning_move = self._find_winning_move(board, self.symbol)
        if winning_move is not None:
            return winning_move
        
        # Priority 2: Block opponent's winning move
        blocking_move = self._find_winning_move(board, self.opponent)
        if blocking_move is not None:
            return blocking_move
        
        # Priority 3: Use strategic decision-making
        available_moves = [i for i, spot in enumerate(board) if spot == EMPTY]
        if not available_moves:
            return None
        
        # Early game: use heuristics for speed; Late game: use minimax for accuracy
        if len(available_moves) > 15:
            return self._heuristic_move(board, available_moves)
        else:
            return self._minimax_move(board, available_moves)
    
    def _heuristic_move(self, board, available_moves):
        """Use heuristic evaluation for early-game moves."""
        best_move = None
        best_score = float('-inf')
        
        for move in available_moves:
            board[move] = self.symbol
            score = self._evaluate(board)
            board[move] = EMPTY
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _minimax_move(self, board, available_moves):
        """Use minimax with alpha-beta pruning for late-game moves."""
        best_move = None
        best_score = float('-inf')
        
        for move in available_moves:
            board[move] = self.symbol
            score = self._minimax(board, 0, False, float('-inf'), float('inf'), max_depth=6)
            board[move] = EMPTY
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move is not None else random.choice(available_moves)
    
    def _find_winning_move(self, board, player):
        """Find a move that would result in three in a row for the given player."""
        for i in range(25):
            if board[i] == EMPTY:
                board[i] = player
                if self._check_winner(board) == player:
                    board[i] = EMPTY
                    return i
                board[i] = EMPTY
        return None
    
    def _check_winner(self, board):
        """Check if there's a winner on the current board."""
        for combo in TicTacToeAgent.WIN_CONDITIONS:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != EMPTY:
                return board[combo[0]]
        if EMPTY not in board:
            return 'DRAW'
        return None
    
    def _minimax(self, board, depth, is_maximizing, alpha, beta, max_depth=6):
        """Minimax with alpha-beta pruning."""
        winner = self._check_winner(board)
        
        if winner == self.symbol:
            return 100 - depth
        elif winner == self.opponent:
            return depth - 100
        elif winner == 'DRAW':
            return 0
        elif depth >= max_depth:
            return self._evaluate(board)
        
        if is_maximizing:
            max_score = float('-inf')
            for i in range(25):
                if board[i] == EMPTY:
                    board[i] = self.symbol
                    score = self._minimax(board, depth + 1, False, alpha, beta, max_depth)
                    board[i] = EMPTY
                    max_score = max(score, max_score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break
            return max_score
        else:
            min_score = float('inf')
            for i in range(25):
                if board[i] == EMPTY:
                    board[i] = self.opponent
                    score = self._minimax(board, depth + 1, True, alpha, beta, max_depth)
                    board[i] = EMPTY
                    min_score = min(score, min_score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
            return min_score
    
    def _evaluate(self, board):
        """Heuristic evaluation of the board position."""
        score = 0
        
        # Evaluate all three-in-a-row combinations
        for combo in TicTacToeAgent.WIN_CONDITIONS:
            cells = [board[combo[0]], board[combo[1]], board[combo[2]]]
            
            my_count = cells.count(self.symbol)
            opp_count = cells.count(self.opponent)
            empty_count = cells.count(EMPTY)
            
            # Reward my positions
            if my_count == 3:
                score += 1000
            elif my_count == 2 and empty_count == 1:
                score += 50
            elif my_count == 1 and empty_count == 2:
                score += 5
            
            # Penalize opponent positions
            if opp_count == 3:
                score -= 1000
            elif opp_count == 2 and empty_count == 1:
                score -= 50
            elif opp_count == 1 and empty_count == 2:
                score -= 5
        
        # Favor control of center positions
        for pos, value in self.center_bonus.items():
            if board[pos] == self.symbol:
                score += value
            elif board[pos] == self.opponent:
                score -= value
        
        return score
