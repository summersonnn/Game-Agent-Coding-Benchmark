"""
Agent Code: A1-Battleship
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-11 19:24:56
"""



class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            valid_placements = []
            
            for r in range(self.board_size):
                for c in range(self.board_size - ship_length + 1):
                    if all(state['my_board'][r][c + i] == 'O' for i in range(ship_length)):
                        valid_placements.append((ship_length, (r, c), 'horizontal'))
            
            for c in range(self.board_size):
                for r in range(self.board_size - ship_length + 1):
                    if all(state['my_board'][r + i][c] == 'O' for i in range(ship_length)):
                        valid_placements.append((ship_length, (r, c), 'vertical'))
            
            if not valid_placements:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    r = random.randint(0, self.board_size - 1)
                    c = random.randint(0, self.board_size - ship_length)
                else:
                    r = random.randint(0, self.board_size - ship_length)
                    c = random.randint(0, self.board_size - 1)
                return {
                    'ship_length': ship_length,
                    'start': (r, c),
                    'orientation': orientation
                }
            else:
                ship_length, start, orientation = random.choice(valid_placements)
                return {
                    'ship_length': ship_length,
                    'start': start,
                    'orientation': orientation
                }
        else:
            known_board = [[None] * self.board_size for _ in range(self.board_size)]
            for shot in state['shot_history']:
                r, c = shot['coord']
                known_board[r][c] = shot['result'].lower()
            
            counts = [[0] * self.board_size for _ in range(self.board_size)]
            
            for ship_length in self.ships:
                for r in range(self.board_size):
                    for c in range(self.board_size - ship_length + 1):
                        if all(known_board[r][c + i] != 'miss' for i in range(ship_length)):
                            for i in range(ship_length):
                                counts[r][c + i] += 1
                
                for c in range(self.board_size):
                    for r in range(self.board_size - ship_length + 1):
                        if all(known_board[r + i][c] != 'miss' for i in range(ship_length)):
                            for i in range(ship_length):
                                counts[r + i][c] += 1
            
            best_score = -1
            best_cells = []
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if known_board[r][c] is None:
                        if counts[r][c] > best_score:
                            best_score = counts[r][c]
                            best_cells = [(r, c)]
                        elif counts[r][c] == best_score:
                            best_cells.append((r, c))
            
            if best_cells:
                return {'target': random.choice(best_cells)}
            else:
                for r in range(self.board_size):
                    for c in range(self.board_size):
                        if known_board[r][c] is None:
                            return {'target': (r, c)}
                return {'target': (0, 0)}
