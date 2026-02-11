"""
Agent Code: A1-Battleship
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-11 19:24:56
"""



class BattleshipAgent:
    """
    Your agent implementation goes here.
    Implement smart placement and bombing logic to beat your opponent.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.remaining_ships = list(ships)  # Track remaining opponent ships for bombing phase

    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].
        """
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            my_board = state['my_board']
            valid_placements = []
            
            # Check horizontal placements
            for row in range(self.board_size):
                for col in range(0, self.board_size - ship_length + 1):
                    valid = True
                    for k in range(col, col + ship_length):
                        if my_board[row][k] != 'O':
                            valid = False
                            break
                    if valid:
                        valid_placements.append(('horizontal', row, col))
            
            # Check vertical placements
            for row in range(0, self.board_size - ship_length + 1):
                for col in range(self.board_size):
                    valid = True
                    for k in range(row, row + ship_length):
                        if my_board[k][col] != 'O':
                            valid = False
                            break
                    if valid:
                        valid_placements.append(('vertical', row, col))
            
            # Select random valid placement or fallback to random if none found
            if valid_placements:
                orientation, row, col = random.choice(valid_placements)
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
        
        else:  # bombing phase
            # Extract shot history information
            shot_cells = set()
            misses = set()
            hits_set = set()
            for entry in state['shot_history']:
                coord = entry['coord']
                shot_cells.add(coord)
                if entry['result'] == 'MISS':
                    misses.add(coord)
                else:  # 'HIT'
                    hits_set.add(coord)
            
            # Update remaining_ships by checking for sunk ships
            for L in list(self.remaining_ships):
                found = False
                # Check horizontal segments
                for i in range(self.board_size):
                    j = 0
                    while j < self.board_size:
                        if (i, j) in hits_set:
                            k = j
                            while k < self.board_size and (i, k) in hits_set:
                                k += 1
                            seg_len = k - j
                            if seg_len == L:
                                found = True
                                break
                            j = k
                        else:
                            j += 1
                    if found:
                        break
                # Check vertical segments if not found horizontally
                if not found:
                    for j in range(self.board_size):
                        i = 0
                        while i < self.board_size:
                            if (i, j) in hits_set:
                                k = i
                                while k < self.board_size and (k, j) in hits_set:
                                    k += 1
                                seg_len = k - i
                                if seg_len == L:
                                    found = True
                                    break
                                i = k
                            else:
                                i += 1
                        if found:
                            break
                if found:
                    self.remaining_ships.remove(L)
            
            # Identify unshot cells
            unshot_cells = []
            for i in range(self.board_size):
                for j in range(self.board_size):
                    if (i, j) not in shot_cells:
                        unshot_cells.append((i, j))
            
            # Fallback if no unshot cells (should not happen in normal gameplay)
            if not unshot_cells:
                return {'target': (0, 0)}
            
            # Calculate probability map for unshot cells
            best_cell = None
            best_count = -1
            for cell in unshot_cells:
                i, j = cell
                total = 0
                for L in self.remaining_ships:
                    count = 0
                    # Horizontal placements covering (i,j)
                    for c in range(max(0, j - L + 1), min(j, self.board_size - L) + 1):
                        valid = True
                        for k in range(c, c + L):
                            if (i, k) in misses:
                                valid = False
                                break
                        if valid:
                            count += 1
                    # Vertical placements covering (i,j)
                    for r in range(max(0, i - L + 1), min(i, self.board_size - L) + 1):
                        valid = True
                        for k in range(r, r + L):
                            if (k, j) in misses:
                                valid = False
                                break
                        if valid:
                            count += 1
                    total += count
                # Skip cells with zero probability (logically water)
                if total == 0:
                    continue
                # Update best cell with highest probability
                if total > best_count:
                    best_count = total
                    best_cell = cell
                elif total == best_count and random.random() < 0.5:
                    best_cell = cell
            
            # Fallback to random unshot cell if all cells have zero probability
            if best_cell is None:
                best_cell = random.choice(unshot_cells)
            
            return {'target': best_cell}
