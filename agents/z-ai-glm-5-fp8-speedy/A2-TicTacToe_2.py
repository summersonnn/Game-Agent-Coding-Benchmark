"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-5@preset/fp8-speedy
Run: 2
Generated: 2026-02-13 14:53:21
"""


import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_lines = self._create_win_lines()
    
    def _create_win_lines(self):
        lines = []
        # Horizontal
        for r in range(5):
            for c in range(3):
                lines.append((r*5+c, r*5+c+1, r*5+c+2))
        # Vertical
        for c in range(5):
            for r in range(3):
                lines.append((r*5+c, (r+1)*5+c, (r+2)*5+c))
        # Diagonal down-right
        for r in range(3):
            for c in range(3):
                lines.append((r*5+c, (r+1)*5+c+1, (r+2)*5+c+2))
        # Diagonal down-left
        for r in range(3):
            for c in range(2, 5):
                lines.append((r*5+c, (r+1)*5+c-1, (r+2)*5+c-2))
        return lines
    
    def _get_empty(self, board):
        return [i for i in range(25) if board[i] == ' ']
    
    def _is_winner(self, board, player):
        for a, b, c in self.win_lines:
            if board[a] == board[b] == board[c] == player:
                return True
        return False
    
    def _get_winning_move(self, board, player):
        for move in self._get_empty(board):
            board[move] = player
            won = self._is_winner(board, player)
            board[move] = ' '
            if won:
                return move
        return None
    
    def _count_threats(self, board, player):
        count = 0
        for a, b, c in self.win_lines:
            vals = [board[a], board[b], board[c]]
            if vals.count(player) == 2 and vals.count(' ') == 1:
                count += 1
        return count
    
    def _evaluate(self, board):
        score = 0
        for a, b, c in self.win_lines:
            vals = [board[a], board[b], board[c]]
            my = vals.count(self.symbol)
            opp = vals.count(self.opponent)
            if opp == 0 and my > 0:
                score += my * my * 10
            elif my == 0 and opp > 0:
                score -= opp * opp * 10
        return score
    
    def _alphabeta(self, board, depth, alpha, beta, maximizing):
        if self._is_winner(board, self.symbol):
            return 1000 + depth
        if self._is_winner(board, self.opponent):
            return -1000 - depth
        
        moves = self._get_empty(board)
        if not moves:
            return 0
        if depth == 0:
            return self._evaluate(board)
        
        if maximizing:
            value = float('-inf')
            for m in moves:
                board[m] = self.symbol
                value = max(value, self._alphabeta(board, depth-1, alpha, beta, False))
                board[m] = ' '
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            for m in moves:
                board[m] = self.opponent
                value = min(value, self._alphabeta(board, depth-1, alpha, beta, True))
                board[m] = ' '
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value
    
    def make_move(self, board):
        board = list(board)
        moves = self._get_empty(board)
        if not moves:
            return None
        
        # 1. Immediate win
        m = self._get_winning_move(board, self.symbol)
        if m is not None:
            return m
        
        # 2. Block opponent win
        m = self._get_winning_move(board, self.opponent)
        if m is not None:
            return m
        
        # 3. Create fork (two winning threats)
        for move in moves:
            board[move] = self.symbol
            threats = self._count_threats(board, self.symbol)
            board[move] = ' '
            if threats >= 2:
                return move
        
        # 4. Block opponent fork
        for move in moves:
            board[move] = self.opponent
            threats = self._count_threats(board, self.opponent)
            board[move] = ' '
            if threats >= 2:
                return move
        
        # 5. Minimax search with alpha-beta pruning
        num_moves = len(moves)
        if num_moves <= 15:
            depth = 5 if num_moves > 8 else 6
            best_move = None
            best_val = float('-inf')
            
            # Sort moves by heuristic for better pruning
            scored_moves = []
            for move in moves:
                board[move] = self.symbol
                score = self._evaluate(board)
                board[move] = ' '
                scored_moves.append((score, move))
            scored_moves.sort(reverse=True)
            
            for _, move in scored_moves:
                board[move] = self.symbol
                val = self._alphabeta(board, depth-1, float('-inf'), float('inf'), False)
                board[move] = ' '
                if val > best_val:
                    best_val = val
                    best_move = move
            if best_move is not None:
                return best_move
        
        # 6. Positional preference
        priority = [12, 7, 11, 13, 17, 6, 8, 16, 18, 
                    0, 4, 20, 24, 1, 3, 5, 9, 15, 19, 21, 23,
                    2, 10, 14, 22]
        for p in priority:
            if p in moves:
                return p
        
        return random.choice(moves)