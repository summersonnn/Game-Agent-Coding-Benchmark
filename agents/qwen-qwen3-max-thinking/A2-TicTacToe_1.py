"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-13 14:53:21
"""



import random

class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opp_symbol = 'O' if symbol == 'X' else 'X'
        self.all_lines = []
        # Generate all winning lines (triplets)
        for r in range(5):
            for c in range(3):
                s = r * 5 + c
                self.all_lines.append((s, s + 1, s + 2))
        for c in range(5):
            for r in range(3):
                s = r * 5 + c
                self.all_lines.append((s, s + 5, s + 10))
        for r in range(3):
            for c in range(3):
                s = r * 5 + c
                self.all_lines.append((s, s + 6, s + 12))
        for r in range(3):
            for c in range(2, 5):
                s = r * 5 + c
                self.all_lines.append((s, s + 4, s + 8))
        # Precompute which lines each cell belongs to
        self.lines_for_cell = [[] for _ in range(25)]
        for line in self.all_lines:
            for idx in line:
                self.lines_for_cell[idx].append(line)

    def make_move(self, board):
        empty_cells = [i for i, val in enumerate(board) if val == ' ']

        # 1. Immediate winning move (return first found)
        for cell in empty_cells:
            for line in self.lines_for_cell[cell]:
                opp_in_line = False
                our_count = 0
                for idx in line:
                    if idx == cell:
                        continue
                    if board[idx] == self.opp_symbol:
                        opp_in_line = True
                        break
                    elif board[idx] == self.symbol:
                        our_count += 1
                if opp_in_line:
                    continue
                if our_count == 2:
                    return cell

        # 2. Collect blocking moves (prevent opponent's immediate win)
        block_moves = []
        for cell in empty_cells:
            for line in self.lines_for_cell[cell]:
                our_in_line = False
                opp_count = 0
                for idx in line:
                    if idx == cell:
                        continue
                    if board[idx] == self.symbol:
                        our_in_line = True
                        break
                    elif board[idx] == self.opp_symbol:
                        opp_count += 1
                if our_in_line:
                    continue
                if opp_count == 2:
                    block_moves.append(cell)
                    break  # Identified as block move; skip other lines for this cell

        # Evaluate and select from block moves if necessary
        if block_moves:
            best_move = None
            best_score = -float('inf')
            for cell in block_moves:
                board_copy = board.copy()
                board_copy[cell] = self.symbol
                score = self._evaluate_board(board_copy)
                if score > best_score:
                    best_score = score
                    best_move = cell
            return best_move

        # 3. No forced win/block; evaluate all available moves
        best_score = -float('inf')
        equal_best_moves = []
        for cell in empty_cells:
            board_copy = board.copy()
            board_copy[cell] = self.symbol
            score = self._evaluate_board(board_copy)
            if score > best_score:
                best_score = score
                equal_best_moves = [cell]
            elif score == best_score:
                equal_best_moves.append(cell)
        # Random tie-breaking among equally best moves
        if equal_best_moves:
            return random.choice(equal_best_moves)
        return random.choice(empty_cells)  # Fallback (should not occur)

    def _evaluate_board(self, board):
        score = 0
        for line in self.all_lines:
            me = 0
            opp = 0
            for idx in line:
                if board[idx] == self.symbol:
                    me += 1
                elif board[idx] == self.opp_symbol:
                    opp += 1
            if me > 0 and opp > 0:
                continue  # Dead line
            if opp == 0:  # Line has only our marks (or empty)
                if me == 1:
                    score += 10
                elif me == 2:
                    score += 1000
            if me == 0:  # Line has only opponent marks (or empty)
                if opp == 1:
                    score -= 10
                elif opp == 2:
                    score -= 1000
        return score
