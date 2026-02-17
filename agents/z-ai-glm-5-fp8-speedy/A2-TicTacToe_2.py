"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-5@preset/fp8-speedy
Run: 2
Generated: 2026-02-13 14:53:21
"""


class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opp = 'O' if symbol == 'X' else 'X'
        self.lines = self._init_lines()
    
    def _init_lines(self):
        lines = []
        # Rows
        for r in range(5):
            for c in range(3):
                s = r * 5 + c
                lines.append((s, s + 1, s + 2))
        # Columns
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                lines.append((s, s + 5, s + 10))
        # Diagonals down-right
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                lines.append((s, s + 6, s + 12))
        # Diagonals down-left
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                lines.append((s, s + 4, s + 8))
        return lines
    
    def make_move(self, board):
        empty = [i for i in range(25) if board[i] == ' ']
        if not empty:
            return None
        
        # Priority 1: Win immediately
        for move in empty:
            board[move] = self.symbol
            if self._is_winner(board, self.symbol):
                board[move] = ' '
                return move
            board[move] = ' '
        
        # Priority 2: Block opponent's win
        for move in empty:
            board[move] = self.opp
            if self._is_winner(board, self.opp):
                board[move] = ' '
                return move
            board[move] = ' '
        
        # Priority 3: Create a fork (two winning threats)
        for move in empty:
            board[move] = self.symbol
            if self._count_threats(board, self.symbol) >= 2:
                board[move] = ' '
                return move
            board[move] = ' '
        
        # Priority 4: Block opponent's fork
        for move in empty:
            board[move] = self.opp
            if self._count_threats(board, self.opp) >= 2:
                board[move] = ' '
                return move
            board[move] = ' '
        
        # Priority 5: Strategic search via minimax
        return self._search_move(board, empty)
    
    def _is_winner(self, board, player):
        for a, b, c in self.lines:
            if board[a] == board[b] == board[c] == player:
                return True
        return False
    
    def _count_threats(self, board, player):
        count = 0
        for a, b, c in self.lines:
            cells = (board[a], board[b], board[c])
            if cells.count(player) == 2 and cells.count(' ') == 1:
                count += 1
        return count
    
    def _search_move(self, board, empty):
        n = len(empty)
        depth = 2 if n > 15 else 3 if n > 10 else 4 if n > 5 else 6
        
        # Order moves by static evaluation for better pruning
        scored = []
        for m in empty:
            board[m] = self.symbol
            scored.append((m, self._evaluate(board)))
            board[m] = ' '
        scored.sort(key=lambda x: -x[1])
        
        best_move = scored[0][0]
        best_score = -100000
        
        for move, _ in scored:
            board[move] = self.symbol
            score = self._minimax(board, depth - 1, False, -100000, 100000)
            board[move] = ' '
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _minimax(self, board, depth, maximizing, alpha, beta):
        winner = self._get_winner(board)
        if winner == self.symbol:
            return 10000 + depth
        if winner == self.opp:
            return -10000 - depth
        
        empty = [i for i in range(25) if board[i] == ' ']
        if not empty:
            return 0
        if depth == 0:
            return self._evaluate(board)
        
        if maximizing:
            value = -100000
            for m in empty:
                board[m] = self.symbol
                value = max(value, self._minimax(board, depth - 1, False, alpha, beta))
                board[m] = ' '
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = 100000
            for m in empty:
                board[m] = self.opp
                value = min(value, self._minimax(board, depth - 1, True, alpha, beta))
                board[m] = ' '
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value
    
    def _get_winner(self, board):
        for a, b, c in self.lines:
            if board[a] != ' ' and board[a] == board[b] == board[c]:
                return board[a]
        return None
    
    def _evaluate(self, board):
        score = 0
        for a, b, c in self.lines:
            cells = (board[a], board[b], board[c])
            my = cells.count(self.symbol)
            opp = cells.count(self.opp)
            
            if opp == 0 and my > 0:
                score += my * my
            elif my == 0 and opp > 0:
                score -= opp * opp
        
        # Center control bonus
        if board[12] == self.symbol:
            score += 3
        elif board[12] == self.opp:
            score -= 3
        
        return score