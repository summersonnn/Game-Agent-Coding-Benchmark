"""
Agent Code: A1-Battleship
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-11 19:24:56
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.potential_targets = deque()
        self.sunk_ships = set()

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            return self.place_ship(state)
        else:
            return self.bomb(state)

    def place_ship(self, state):
        ship_length = state['ships_to_place'][0]
        board = state['my_board']
        
        for _ in range(100):
            orientation = random.choice(['horizontal', 'vertical'])
            if orientation == 'horizontal':
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - ship_length)
            else:
                row = random.randint(0, self.board_size - ship_length)
                col = random.randint(0, self.board_size - 1)
            
            if self.is_valid_placement(board, row, col, ship_length, orientation):
                return {
                    'ship_length': ship_length,
                    'start': (row, col),
                    'orientation': orientation
                }
        
        return {
            'ship_length': ship_length,
            'start': (0, 0),
            'orientation': 'horizontal'
        }

    def is_valid_placement(self, board, row, col, ship_length, orientation):
        if orientation == 'horizontal':
            if col + ship_length > self.board_size:
                return False
            for c in range(col, col + ship_length):
                if board[row][c] != 'O':
                    return False
        else:
            if row + ship_length > self.board_size:
                return False
            for r in range(row, row + ship_length):
                if board[r][col] != 'O':
                    return False
        return True

    def bomb(self, state):
        shots_taken = {shot['coord'] for shot in state['shot_history']}
        hits = [shot['coord'] for shot in state['shot_history'] if shot['result'] == 'HIT']
        
        # Check for newly sunk ships and clear related targets
        self.check_and_handle_sunk_ships(hits, shots_taken)
        
        # Handle hit - add adjacent cells to potential targets
        if state['last_shot_result'] == 'HIT':
            last_hit = state['last_shot_coord']
            self.add_adjacent_targets(last_hit, shots_taken, hits)
        
        # Try potential targets first (hunting mode)
        while self.potential_targets:
            target = self.potential_targets.popleft()
            if target not in shots_taken:
                return {'target': target}
        
        # Use search pattern (checkerboard for efficiency)
        return self.search_pattern(state, shots_taken)

    def add_adjacent_targets(self, coord, shots_taken, hits):
        row, col = coord
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        # If we have at least 2 hits, determine orientation and prioritize that direction
        if len(hits) >= 2:
            component = self.get_connected_component(coord, hits)
            if len(component) >= 2:
                coords = list(component)
                r1, c1 = coords[0]
                r2, c2 = coords[1]
                if r1 == r2:
                    # Horizontal ship - prioritize horizontal directions
                    directions = [(0, 1), (0, -1)]
                else:
                    # Vertical ship - prioritize vertical directions
                    directions = [(1, 0), (-1, 0)]
        
        random.shuffle(directions)
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.board_size and 0 <= new_col < self.board_size:
                if (new_row, new_col) not in shots_taken:
                    self.potential_targets.appendleft((new_row, new_col))

    def get_connected_component(self, coord, hits):
        """Find all connected hits that belong to the same ship."""
        visited = set()
        component = set()
        queue = [coord]
        visited.add(coord)
        hits_set = set(hits)
        
        while queue:
            current = queue.pop(0)
            component.add(current)
            
            row, col = current
            neighbors = [(row+1, col), (row-1, col), (row, col+1), (row, col-1)]
            for neighbor in neighbors:
                if neighbor in hits_set and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return component

    def check_and_handle_sunk_ships(self, hits, shots_taken):
        """Check if any ships are sunk and remove their adjacent targets."""
        visited = set()
        hits_set = set(hits)
        
        for hit in hits:
            if hit not in visited:
                component = set()
                queue = [hit]
                visited.add(hit)
                
                while queue:
                    current = queue.pop(0)
                    component.add(current)
                    
                    row, col = current
                    neighbors = [(row+1, col), (row-1, col), (row, col+1), (row, col-1)]
                    for neighbor in neighbors:
                        if neighbor in hits_set and neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                # Check if component matches a ship length
                length = len(component)
                if length in self.ships and length not in self.sunk_ships:
                    self.sunk_ships.add(length)
                    # Filter out targets adjacent to this sunk ship
                    self.filter_targets_near_sunk_ship(component, shots_taken)

    def filter_targets_near_sunk_ship(self, sunk_component, shots_taken):
        """Remove potential targets that are adjacent to a sunk ship."""
        filtered = deque()
        for target in self.potential_targets:
            # Check if target is adjacent to the sunk ship
            row, col = target
            neighbors = [(row+1, col), (row-1, col), (row, col+1), (row, col-1)]
            is_adjacent_to_sunk = any(n in sunk_component for n in neighbors)
            if not is_adjacent_to_sunk:
                filtered.append(target)
        self.potential_targets = filtered

    def search_pattern(self, state, shots_taken):
        """Use checkerboard pattern to efficiently search for ships."""
        # Checkerboard pattern (every other cell) - guarantees finding all ships
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row + col) % 2 == 0:
                    if (row, col) not in shots_taken:
                        return {'target': (row, col)}
        
        # If checkerboard exhausted, try remaining cells
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in shots_taken:
                    return {'target': (row, col)}
        
        # Fallback
        return {'target': (0, 0)}
