"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3.5-397b-a17b
Run: 2
Generated: 2026-02-16 18:23:36
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_lines = []
        self._init_win_lines()

    def _init_win_lines(self):
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                self.win_lines.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                self.win_lines.append((start, start + 4, start + 8))

    def make_move(self, board):
        empty_indices = [i for i, v in enumerate(board) if v == ' ']
        if not empty_indices:
            return 0

        # 1. Check for immediate win
        for move in empty_indices:
            board[move] = self.symbol
            if self._check_win(board, self.symbol):
                board[move] = ' '
                return move
            board[move] = ' '

        # 2. Check for immediate block (opponent win)
        for move in empty_indices:
            board[move] = self.opponent
            if self._check_win(board, self.opponent):
                board[move] = ' '
                return move
            board[move] = ' '

        # 3. Strategic move
        best_move = None
        best_score = -float('inf')
        
        for move in empty_indices:
            score = 0
            for line in self.win_lines:
                if move not in line:
                    continue
                marks_me = 0
                marks_opp = 0
                for idx in line:
                    if idx == move:
                        continue
                    if board[idx] == self.symbol:
                        marks_me += 1
                    elif board[idx] == self.opponent:
                        marks_opp += 1
                
                # Create threat (2 in a row)
                if marks_me == 1 and marks_opp == 0:
                    score += 10
                
                # Block opponent threat (prevent them from getting 2 in a row)
                if marks_opp == 1 and marks_me == 0:
                    score += 5

            # Positional bias (Center is better)
            dist = abs((move // 5) - 2) + abs((move % 5) - 2)
            score -= dist 

            if score > best_score:
                best_score = score
                best_move = move
        
        if best_move is None:
            return random.choice(empty_indices)
            
        return best_move

    def _check_win(self, board, symbol):
        for a, b, c in self.win_lines:
            if board[a] == board[b] == board[c] == symbol:
                return True
        return False
