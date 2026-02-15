"""
Agent Code: A1-Battleship
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-14 16:15:50
"""

from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.opponent_board = [[None] * board_size for _ in range(board_size)]
        self.target_queue = deque()
        self.in_queue = set()

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            valid_placements = []
            
            # Check horizontal placements
            for r in range(self.board_size):
                for c in range(0, self.board_size - ship_length + 1):
                    if all(state['my_board'][r][c + i] == 'O' for i in range(ship_length)):
                        valid_placements.append((r, c, 'horizontal'))
            
            # Check vertical placements
            for r in range(0, self.board_size - ship_length + 1):
                for c in range(self.board_size):
                    if all(state['my_board'][r + i][c] == 'O' for i in range(ship_length)):
                        valid_placements.append((r, c, 'vertical'))
            
            if valid_placements:
                r, c, orientation = random.choice(valid_placements)
                return {
                    'ship_length': ship_length,
                    'start': (r, c),
                    'orientation': orientation
                }
            else:
                return {
                    'ship_length': ship_length,
                    'start': (0, 0),
                    'orientation': 'horizontal'
                }
        
        else:  # Bombing phase
            if state['last_shot_coord'] is not None:
                r, c = state['last_shot_coord']
                result = state['last_shot_result']
                
                if self.opponent_board[r][c] is None:
                    if result == 'HIT':
                        self.opponent_board[r][c] = 'H'
                        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                                if self.opponent_board[nr][nc] is None and (nr, nc) not in self.in_queue:
                                    self.target_queue.append((nr, nc))
                                    self.in_queue.add((nr, nc))
                    else:  # MISS
                        self.opponent_board[r][c] = 'M'
            
            if self.target_queue:
                target = self.target_queue.popleft()
                self.in_queue.discard(target)
                return {'target': target}
            
            candidates = []
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self.opponent_board[r][c] is None:
                        candidates.append((r, c))
            
            if not candidates:
                return {'target': (0, 0)}
            
            pattern0 = [cell for cell in candidates if (cell[0] + cell[1]) % 2 == 0]
            target = random.choice(pattern0) if pattern0 else random.choice(candidates)
            return {'target': target}
