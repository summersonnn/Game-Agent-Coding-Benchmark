"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-max-thinking
Run: 2
Generated: 2026-02-13 14:53:21
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        # Precompute all winning line triples
        self.all_lines = []
        # Horizontal
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.all_lines.append((start, start + 1, start + 2))
        # Vertical
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.all_lines.append((start, start + 5, start + 10))
        # Diagonal down-right
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.all_lines.append((start, start + 6, start + 12))
        # Diagonal down-left
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.all_lines.append((start, start + 4, start + 8))
        # Map cells to lines they participate in
        self.lines_for_cell = [[] for _ in range(25)]
        for line in self.all_lines:
            for cell in line:
                self.lines_for_cell[cell].append(line)
        # Positional weights (center = highest value)
        self.center_weights = [
            1, 2, 3, 2, 1,
            2, 4, 5, 4, 2,
            3, 5, 6, 5, 3,
            2, 4, 5, 4, 2,
            1, 2, 3, 2, 1
        ]
        # Search constants
        self.INF = 10**9
        self.MAX_SEARCH_DEPTH = 2  # Plies to search after root move

    def _can_win_move(self, board, move, player):
        """True if placing 'player' at 'move' completes a winning line."""
        for line in self.lines_for_cell[move]:
            cnt = 0
            for idx in line:
                if board[idx] == player:
                    cnt += 1
            if cnt == 2:
                return True
        return False

    def _evaluate(self, board):
        """Static board evaluation from agent's ('self.symbol') side.
        Returns integer score: Higher=better for agent.
        """
        score = 0
        for line in self.all_lines:
            cells = [board[i] for i in line]
            own = cells.count(self.symbol)
            opp = cells.count(self.opponent)
            if own > 0 and opp > 0:
                continue
            if own == 2:
                score += 120
            elif own == 1:
                score += 20
            elif opp == 2:
                score -= 180
            elif opp == 1:
                score -= 30
        for i in range(25):
            if board[i] == self.symbol:
                score += self.center_weights[i] * 0.5
            elif board[i] == self.opponent:
                score -= self.center_weights[i] * 0.5
        return score

    def _order_moves(self, board, player):
        """Return empty cells sorted by positional importance (descending)."""
        empty = [i for i in range(25) if board[i] == ' ']
        empty.sort(key=lambda i: self.center_weights[i], reverse=True)
        return empty

    def _minimax(self, board, player, depth, alpha, beta):
        # Check if current player can win immediately
        for move in range(25):
            if board[move] == ' ' and self._can_win_move(board, move, player):
                return self.INF if player == self.symbol else -self.INF
        # Check draw
        if ' ' not in board:
            return 0
        # Depth cutoff
        if depth == 0:
            return self._evaluate(board)
        # Generate sorted moves
        moves = self._order_moves(board, player)
        if player == self.symbol:  # Maximizing player (agent's turn)
            max_val = -self.INF
            for move in moves:
                board[move] = player
                val = self._minimax(board, self.opponent, depth - 1, alpha, beta)
                board[move] = ' '
                if val > max_val:
                    max_val = val
                if max_val >= beta:
                    break
                if max_val > alpha:
                    alpha = max_val
            return max_val
        else:  # Minimizing player (opponent's turn)
            min_val = self.INF
            for move in moves:
                board[move] = player
                val = self._minimax(board, self.symbol, depth - 1, alpha, beta)
                board[move] = ' '
                if val < min_val:
                    min_val = val
                if min_val <= alpha:
                    break
                if min_val < beta:
                    beta = min_val
            return min_val

    def make_move(self, board):
        # 1. Check for immediate winning move
        for move in range(25):
            if board[move] == ' ' and self._can_win_move(board, move, self.symbol):
                return move
        # 2. Check for opponent's immediate winning moves and block
        for move in range(25):
            if board[move] == ' ' and self._can_win_move(board, move, self.opponent):
                return move
        # 3. Minimax search with alpha-beta pruning
        best_move = None
        best_score = -self.INF
        moves = self._order_moves(board, self.symbol)
        for move in moves:
            board[move] = self.symbol
            # Redundant safety check (should be caught by step 1)
            if self._can_win_move(board, move, self.symbol):
                board[move] = ' '
                return move
            score = self._minimax(board, self.opponent, self.MAX_SEARCH_DEPTH, -self.INF, self.INF)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
                if score >= self.INF // 2:
                    break
        # Fallback: select first valid empty cell
        if best_move is None:
            for i in range(25):
                if board[i] == ' ':
                    return i
            return 0
        return best_move
