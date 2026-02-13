"""
Agent Code: A1-Battleship
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-13 14:03:41
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Battleship agent with optimized placement and bombing phases.
    Placement: Systematically generates valid placements, prioritizing non-overlapping positions.
    Bombing: Uses Hunt/Target strategy with parity-based hunting and adjacency targeting after hits.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = boats = tuple(ships)
        self.opponent_board = [[0] * board_size for _ in range(board_size)]  # 0=unknown, 1=miss, 2=hit
        self.mode = 'hunt'  # 'hunt' or 'target'
        self.target_queue = deque()
        self.remaining_ships = tuple(ships)  # Track for potential future enhancements

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            valid_placements = []
            
            # Check horizontal placements
            for row in range(self.board_size):
                for col in range(self.board_size - ship_length + 1):
                    valid = True
                    for c in range(col, col + ship_length):
                        if state['my_board'][row][c] != 'O':
                            valid = False
                            break
                    if valid:
                        valid_placements.append({
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': 'horizontal'
                        })
            
            # Check vertical placements
            for row in range(self.board_size - ship_length + 1):
                for col in range(self.board_size):
                    valid = True
                    for r in range(row, row + ship_length):
                        if state['my_board'][r][col] != 'O':
                            valid = False
                            break
                    if valid:
                        valid_placements.append({
                            'ship_length': ship_length,
                            'start': (row, col),
                            'orientation': 'vertical'
                        })
            
            # Return valid placement or fallback safely
            if valid_placements:
                return random.choice(valid_placements)
            else:
                # Fallback: generate valid placement by retrying (should rarely execute)
                orientation = None
                for _ in range(100):
                    orientation = random.choice(['horizontal', 'horizontal', 'vertical', 'vertical'])  # Bias for horizontal
                    if orientation == 'horizontal':
                        row = random.randint(0, self.board_size - 1)
                        col = random.randint(0, self.board_size - ship_length)
                        if all(state['my_board'][row][c] == 'O' for c in range(col, col + ship_length)):
                            return {
                                'ship_length': ship_length,
                                'start': (row, col),
                                'orientation': orientation
                            }
                    else:
                        row = random.randint(0, self.board_size - ship_length)
                        col = random.randint(0, self.board_size - 1)
                        if all(state['my_board'][r][col] == 'O' for r in range(row, row + ship_length)):
                            return {
                                'ship_length': ship_length,
                                'start': (row, col),
                                'orientation': orientation
                            }
                # Last resort: return first valid found in systematic search
                return valid_placements[0] if valid_placements else {
                    'ship_length': ship_length,
                    'start': (0, 0),
                    'orientation': 'horizontal'
                }
        
        else:  # Bombs phase
            # Update board with last shot result
            if state['last_shot_coord'] is not None:
                r, c = state['last_shot_coord']
                if state['last_shot_result'] == 'HIT':
                    self.opponent_board[r][c] = 2  # Hit detected
                    # Add adjacent cells to target queue if valid
                    for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < self.board_size and 0 <= nc < self.board_size 
                            and self.opponent_board[nr][nc] == 0  # Unknown
                            and (nr, nc) not in self.target_queue):
                            self.target_queue.append((nr, nc))
                    self.mode = 'target'
                else:
                    self.opponent_board[r][c] = 1  # Miss recorded
            
            # Select next target
            target = None
            
            # Prioritize target queue if in target mode and queue has valid cells
            if self.mode == 'target' and self.target_queue:
                while self.target_queue:
                    candidate = self.target_queue.popleft()
                    if (self.opponent_board[candidate[0]][candidate[1]] == 0):  # Still viable
                        target = candidate
                        break
                if not target:
                    self.mode = 'hunt'  # Exhausted targets; return to Hunt phase
            
            # Hunt phase: Use parity strategy (even sum parity cells for initial coverage)
            if target is None:
                candidates = []
                for i in range(self.board_size):
                    for j in range(self.board_size):
                        if self.opponent_board[i][j] == 0:
                            if (i + j) % 2 == 0:  # Prioritize even parity cells
                                candidates.append((i, j))
                ifcandidates = not candidates  # If no even parity left, use all unknown
                for i in range(self.board_size):
                    for j in range(self.board_size):
                        if self.opponent_board[i][j] == 0:
                            candidates.append((i, j))
                if candidates:
                    target = random.choice(candidates)
                else:
                    # Fallback (should not occur in valid game state)
                    for i in range(self.board_size):
                        for j in range(self.board_size):
                            if self.opponent_board[i][j] == 0:
                                target = (i, j)
                                break
                        if target: break
                    if not target: target = (0, 0)
            
            return {'target': target}
