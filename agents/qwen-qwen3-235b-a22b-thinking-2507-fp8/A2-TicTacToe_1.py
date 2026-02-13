"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-13 14:53:21
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.lines = self.generate_lines()
    
    def generate_lines(self):
        lines = []
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start+1, start+2))
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                lines.append((start, start+5, start+10))
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                lines.append((start, start+6, start+12))
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                lines.append((start, start+4, start+8))
        return lines

    def is_winning_move(self, board, move, symbol):
        for line in self.lines:
            if move in line:
                other_cells = [c for c in line if c != move]
                if board[other_cells[0]] == symbol and board[other_cells[1]] == symbol:
                    return True
        return False

    def make_move(self, board):
        available_moves = [i for i, cell in enumerate(board) if cell == ' ']
        if not available_moves:
            return None

        for move in available_moves:
            if self.is_winning_move(board, move, self.symbol):
                return move

        opponent_symbol = 'O' if self.symbol == 'X' else 'X'
        blocking_candidates = {}
        for line in self.lines:
            symbols = [board[i] for i in line]
            if symbols.count(opponent_symbol) == 2 and symbols.count(' ') == 1:
                empty_idx = line[symbols.index(' ')]
                if empty_idx in available_moves:
                    blocking_candidates[empty_idx] = blocking_candidates.get(empty_idx, 0) + 1
        
        if blocking_candidates:
            sorted_blocks = sorted(blocking_candidates.items(), key=lambda x: (-x[1], x[0]))
            return sorted_blocks[0][0]

        fork_candidates = []
        for move in available_moves:
            temp_board = board.copy()
            temp_board[move] = self.symbol
            threat_count = 0
            for line in self.lines:
                line_symbols = [temp_board[i] for i in line]
                if line_symbols.count(self.symbol) == 2 and line_symbols.count(' ') == 1:
                    threat_count += 1
            if threat_count >= 2:
                fork_candidates.append((move, threat_count))
        
        if fork_candidates:
            fork_candidates.sort(key=lambda x: (-x[1], x[0]))
            return fork_candidates[0][0]

        center = 12
        if center in available_moves:
            return center
        
        corners = [0, 4, 20, 24]
        for corner in corners:
            if corner in available_moves:
                return corner
        
        edges = [1, 2, 3, 5, 9, 10, 14, 15, 19, 21, 22, 23]
        for edge in edges:
            if edge in available_moves:
                return edge
        
        return available_moves[0]
