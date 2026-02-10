"""
Agent Code: A1-Battleship
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-10 16:22:20
"""



class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._placement_move(state, feedback)
        else:
            return self._bombing_move(state, feedback)

    def _placement_move(self, state, feedback):
        current_board = state['my_board']
        ship_length = state['ships_to_place'][0]

        possible_placements = []
        for orientation in ['horizontal', 'vertical']:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if orientation == 'horizontal':
                        if col + ship_length <= self.board_size:
                            valid = True
                            for i in range(ship_length):
                                if current_board[row][col + i] == 'S':
                                    valid = False
                                    break
                            if valid:
                                possible_placements.append((row, col, orientation))
                    else:
                        if row + ship_length <= self.board_size:
                            valid = True
                            for i in range(ship_length):
                                if current_board[row + i][col] == 'S':
                                    valid = False
                                    break
                            if valid:
                                possible_placements.append((row, col, orientation))

        if possible_placements:
            chosen = random.choice(possible_placements)
            return {
                'ship_length': ship_length,
                'start': (chosen[0], chosen[1]),
                'orientation': chosen[2]
            }
        else:
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            return {
                'ship_length': ship_length,
                'start': (row, col),
                'orientation': orientation
            }

    def _bombing_move(self, state, feedback):
        shot_history = state['shot_history']
        shot_cells = set(entry['coord'] for entry in shot_history)
        hits = set(entry['coord'] for entry in shot_history if entry['result'] == 'HIT')

        targets = set()
        for (r, c) in hits:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and (nr, nc) not in shot_cells:
                    targets.add((nr, nc))

        if targets:
            target = random.choice(list(targets))
        else:
            unshot_cells = [(r, c) for r in range(self.board_size) for c in range(self.board_size) if (r, c) not in shot_cells]
            if unshot_cells:
                target = random.choice(unshot_cells)
            else:
                target = (0, 0)

        return {'target': target}
