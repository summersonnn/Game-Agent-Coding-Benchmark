"""
Agent Code: A1-Battleship
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-11 19:24:56
"""



import random

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # Track our shots and hits for bombing phase
        self.shot_coords = set()
        self.hits = set()
        self.targets = []  # Queue of promising targets (adjacent to hits)

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._bomb(state)

    def _place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        # Collect all valid placements (non-overlapping)
        valid_placements = []
        for orientation in ['horizontal', 'vertical']:
            if orientation == 'horizontal':
                for row in range(self.board_size):
                    for col in range(self.board_size - ship_length + 1):
                        if all(board[row][col+i] == 'O' for i in range(ship_length)):
                            valid_placements.append(((row, col), orientation))
            else:  # vertical
                for row in range(self.board_size - ship_length + 1):
                    for col in range(self.board_size):
                        if all(board[row+i][col] == 'O' for i in range(ship_length)):
                            valid_placements.append(((row, col), orientation))
        
        if valid_placements:
            # Prefer placements that are isolated (no adjacent existing ships)
            isolated = []
            for (start, orient) in valid_placements:
                row, col = start
                isolated_flag = True
                cells = []
                if orient == 'horizontal':
                    cells = [(row, col+i) for i in range(ship_length)]
                else:
                    cells = [(row+i, col) for i in range(ship_length)]
                
                for (r, c) in cells:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                                if board[nr][nc] == 'S':
                                    isolated_flag = False
                                    break
                        if not isolated_flag:
                            break
                    if not isolated_flag:
                        break
                
                if isolated_flag:
                    isolated.append(((row, col), orient))
            
            if isolated:
                start, orientation = random.choice(isolated)
            else:
                start, orientation = random.choice(valid_placements)
        else:
            # Fallback: should not happen with proper board, but return something
            start, orientation = (0, 0), 'horizontal'
        
        return {
            'ship_length': ship_length,
            'start': start,
            'orientation': orientation
        }

    def _bomb(self, state):
        # Update tracking from state
        new_shots = set()
        for shot in state['shot_history']:
            coord = shot['coord']
            result = shot['result']
            new_shots.add(coord)
            if result == 'HIT':
                self.hits.add(coord)
                # Add adjacent cells as potential targets
                r, c = coord
                for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if (nr, nc) not in self.shot_coords and (nr, nc) not in self.targets:
                            self.targets.append((nr, nc))
        
        self.shot_coords.update(new_shots)
        
        # Clean up targets that we've already shot
        self.targets = [t for t in self.targets if t not in self.shot_coords]
        
        # Choose target
        if self.targets:
            # Prioritize targets from hunting (adjacent to hits)
            target = self.targets.pop(0)
        else:
            # Hunting mode: use checkerboard pattern to maximize coverage
            all_cells = [(r, c) for r in range(self.board_size) for c in range(self.board_size)]
            remaining = [cell for cell in all_cells if cell not in self.shot_coords]
            
            if not remaining:
                # Shouldn't happen, but fallback
                target = (0, 0)
            else:
                # Checkerboard pattern: (r+c) % 2 == 0
                checkerboard = [cell for cell in remaining if (cell[0] + cell[1]) % 2 == 0]
                if checkerboard:
                    target = random.choice(checkerboard)
                else:
                    target = random.choice(remaining)
        
        return {'target': target}
