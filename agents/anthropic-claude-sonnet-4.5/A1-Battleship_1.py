"""
Agent Code: A1-Battleship
Model: anthropic/claude-sonnet-4.5
Run: 1
Generated: 2026-02-11 19:24:56
"""



class BattleshipAgent:
    """
    Smart Battleship agent with strategic placement and intelligent bombing.
    Uses hunt-and-target strategy with checkerboard search pattern.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        
    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self._place_ship(state)
        else:
            return self._make_shot(state)
    
    def _place_ship(self, state):
        """Place ships randomly but validly on the board"""
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        # Try random placements
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            # Validate placement
            valid = True
            if orientation == 'horizontal':
                for c in range(col, col + ship_length):
                    if board[row][c] != 'O':
                        valid = False
                        break
            else:
                for r in range(row, row + ship_length):
                    if board[r][col] != 'O':
                        valid = False
                        break
            
            if valid:
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        # Fallback: systematic search for valid placement
        return self._find_valid_placement(board, ship_length)
    
    def _find_valid_placement(self, board, length):
        """Find first valid placement systematically"""
        # Try horizontal
        for r in range(self.board_size):
            for c in range(self.board_size - length + 1):
                if all(board[r][c+i] == 'O' for i in range(length)):
                    return {'ship_length': length, 'start': (r, c), 'orientation': 'horizontal'}
        
        # Try vertical
        for r in range(self.board_size - length + 1):
            for c in range(self.board_size):
                if all(board[r+i][c] == 'O' for i in range(length)):
                    return {'ship_length': length, 'start': (r, c), 'orientation': 'vertical'}
        
        return {'ship_length': length, 'start': (0, 0), 'orientation': 'horizontal'}
    
    def _make_shot(self, state):
        """Make intelligent shot using hunt-and-target strategy"""
        shot_history = state.get('shot_history', [])
        
        # Build knowledge from shot history
        shots = set()
        hits = set()
        
        for shot in shot_history:
            coord = shot['coord']
            shots.add(coord)
            if shot['result'] == 'HIT':
                hits.add(coord)
        
        # Find groups of connected hits (unsunk ships)
        unsunk_groups = self._find_hit_groups(hits)
        
        # Generate hunt targets for each group
        hunt_targets = []
        for group in unsunk_groups:
            targets = self._get_hunt_targets(group, shots)
            hunt_targets.extend(targets)
        
        # Choose target: prioritize hunting, otherwise search
        if hunt_targets:
            return {'target': hunt_targets[0]}
        else:
            target = self._search_target(shots)
            return {'target': target}
    
    def _find_hit_groups(self, hits):
        """Find connected components of hits (each group is a ship)"""
        if not hits:
            return []
        
        visited = set()
        groups = []
        
        for hit in hits:
            if hit in visited:
                continue
            
            # BFS to find all connected hits
            group = []
            queue = [hit]
            visited.add(hit)
            
            while queue:
                curr = queue.pop(0)
                group.append(curr)
                
                r, c = curr
                # Check 4 adjacent cells
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (r + dr, c + dc)
                    if neighbor in hits and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            groups.append(sorted(group))
        
        return groups
    
    def _get_hunt_targets(self, group, shots):
        """Get priority targets adjacent to a hit group"""
        targets = []
        
        if len(group) == 1:
            # Single hit: check all 4 directions
            r, c = group[0]
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                target = (r + dr, c + dc)
                if self._is_valid(target) and target not in shots:
                    targets.append(target)
        else:
            # Multiple hits: determine ship orientation and target ends
            rows = [g[0] for g in group]
            cols = [g[1] for g in group]
            
            if len(set(rows)) == 1:
                # Horizontal ship
                row = rows[0]
                min_col = min(cols)
                max_col = max(cols)
                
                # Target both ends of the line
                for target in [(row, min_col - 1), (row, max_col + 1)]:
                    if self._is_valid(target) and target not in shots:
                        targets.append(target)
            elif len(set(cols)) == 1:
                # Vertical ship
                col = cols[0]
                min_row = min(rows)
                max_row = max(rows)
                
                # Target both ends of the line
                for target in [(min_row - 1, col), (max_row + 1, col)]:
                    if self._is_valid(target) and target not in shots:
                        targets.append(target)
        
        return targets
    
    def _search_target(self, shots):
        """Choose target using checkerboard pattern for efficiency"""
        # Checkerboard pattern (ensures we don't miss ships >= 2 cells)
        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r + c) % 2 == 0 and (r, c) not in shots:
                    candidates.append((r, c))
        
        if candidates:
            return random.choice(candidates)
        
        # Fallback: any untargeted cell
        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) not in shots:
                    return (r, c)
        
        # Should never reach here in a valid game
        return (0, 0)
    
    def _is_valid(self, coord):
        """Check if coordinate is within board bounds"""
        r, c = coord
        return 0 <= r < self.board_size and 0 <= c < self.board_size
