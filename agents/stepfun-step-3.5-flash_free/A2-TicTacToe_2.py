"""
Agent Code: A2-TicTacToe
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-13 15:25:40
"""



class TicTacToeAgent:
    EMPTY = ' '
    X_MARK = 'X'
    O_MARK = 'O'

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.winning_lines = self._generate_winning_lines()
        self.cell_to_lines = [[] for _ in range(25)]
        for i, line in enumerate(self.winning_lines):
            for idx in line:
                self.cell_to_lines[idx].append(i)

    def _generate_winning_lines(self):
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 1, start + 2))
        # Columns
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start + 4, start + 8))
        return lines

    def _is_threat(self, board, move, player):
        """Check if playing at move would complete a 3-in-a-row for player."""
        for line_idx in self.cell_to_lines[move]:
            a, b, c = self.winning_lines[line_idx]
            cells = [board[a], board[b], board[c]]
            # Count player marks and empty cells in this line
            player_count = sum(1 for cell in cells if cell == player)
            empty_count = sum(1 for cell in cells if cell == self.EMPTY)
            if player_count == 2 and empty_count == 1:
                return True
        return False

    def _check_winner(self, board):
        """Return winner symbol, 'DRAW', or None."""
        for a, b, c in self.winning_lines:
            if board[a] == board[b] == board[c] and board[a] != self.EMPTY:
                return board[a]
        if self.EMPTY not in board:
            return 'DRAW'
        return None

    def _evaluate(self, board, player):
        """Heuristic evaluation from player's perspective."""
        opp = self.O_MARK if player == self.X_MARK else self.X_MARK
        our_2 = our_1 = opp_2 = opp_1 = 0
        
        for a, b, c in self.winning_lines:
            line = [board[a], board[b], board[c]]
            p = sum(1 for cell in line if cell == player)
            o = sum(1 for cell in line if cell == opp)
            e = sum(1 for cell in line if cell == self.EMPTY)
            
            if p > 0 and o == 0:
                if p == 2:
                    our_2 += 1
                elif p == 1:
                    our_1 += 1
            elif o > 0 and p == 0:
                if o == 2:
                    opp_2 += 1
                elif o == 1:
                    opp_1 += 1
        
        return (our_2 * 100 + our_1 * 10) - (opp_2 * 100 + opp_1 * 10)

    def _minimax(self, board, player, depth, alpha, beta, original_player, max_depth):
        winner = self._check_winner(board)
        if winner is not None:
            if winner == original_player:
                return 10000 - depth
            elif winner == (self.O_MARK if original_player == self.X_MARK else self.X_MARK):
                return -10000 + depth
            else:
                return 0
        
        if depth >= max_depth:
            return self._evaluate(board, original_player)
        
        available_moves = [i for i in range(25) if board[i] == self.EMPTY]
        next_player = self.O_MARK if player == self.X_MARK else self.X_MARK
        
        if player == original_player:
            best = -float('inf')
            for move in available_moves:
                board[move] = player
                score = self._minimax(board, next_player, depth + 1, alpha, beta, original_player, max_depth)
                board[move] = self.EMPTY
                best = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = float('inf')
            for move in available_moves:
                board[move] = player
                score = self._minimax(board, original_player, depth + 1, alpha, beta, original_player, max_depth)
                board[move] = self.EMPTY
                best = min(best, score)
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    def _find_best_move(self, board, player, original_player, max_depth):
        available_moves = [i for i in range(25) if board[i] == self.EMPTY]
        # Order moves by number of winning lines they participate in (more lines first)
        available_moves.sort(key=lambda m: len(self.cell_to_lines[m]), reverse=True)
        
        best_move = None
        best_score = -float('inf')
        next_player = self.O_MARK if player == self.X_MARK else self.X_MARK
        
        for move in available_moves:
            board[move] = player
            score = self._minimax(board, next_player, 1, -float('inf'), float('inf'), original_player, max_depth)
            board[move] = self.EMPTY
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def make_move(self, board):
        available_moves = [i for i in range(25) if board[i] == self.EMPTY]
        if not available_moves:
            return 0  # Should not happen, but fallback
        
        # 1. Check for immediate winning move
        for move in available_moves:
            if self._is_threat(board, move, self.symbol):
                return move
        
        # 2. Check for immediate block (opponent's winning move)
        opponent = self.O_MARK if self.symbol == self.X_MARK else self.X_MARK
        for move in available_moves:
            if self._is_threat(board, move, opponent):
                return move
        
        # 3. Use minimax with adaptive depth
        max_depth = min(4, len(available_moves))
        return self._find_best_move(board, self.symbol, self.symbol, max_depth)
