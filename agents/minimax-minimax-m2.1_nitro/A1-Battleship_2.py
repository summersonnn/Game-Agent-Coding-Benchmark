"""
Agent Code: A1-Battleship
Model: minimax/minimax-m2.1:nitro
Run: 2
Generated: 2026-02-11 19:21:34
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    """
    Your agent implementation goes here.
    Implement smart placement and bombing logic to beat your opponent.
    """
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        # Initialize state for bombing phase
        self.shots = set()
        self.hunt_stack = []
        self.hunt_set = set()

    def make_move(self, state, feedback):
        """
        Handles both placement and bombing phases based on state['phase'].

        Parameters:
        - state: Dictionary containing game state (see phase-specific documentation above)
        - feedback: Always None (reserved for future use)

        Returns:
        - During placement phase: Dictionary with 'ship_length', 'start', and 'orientation'
        - During bombing phase: Dictionary with 'target'

        Examples:

        # Placement phase
        if state['phase'] == 'placement':
            return {
                'ship_length': 5,
                'start': (0, 0),
                'orientation': 'horizontal'
            }

        # Bombing phase
        if state['phase'] == 'bombing':
            return {
                'target': (3, 4)
            }
        """
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            
            # Try up to 100 attempts to find a valid placement
            for _ in range(100):
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - ship_length)
                else:
                    row = random.randint(0, self.board_size - ship_length)
                    col = random.randint(0, self.board_size - 1)
                
                # Check if placement is valid
                valid = True
                for i in range(ship_length):
                    if orientation == 'horizontal':
                        r, c = row, col + i
                    else:
                        r, c = row + i, col
                    
                    if not (0 <= r < self.board_size and 0 <= c < self.board_size):
                        valid = False
                        break
                    if state['my_board'][r][c] != 'O':
                        valid = False
                        break
                
                if valid:
                    return {
                        'ship_length': ship_length,
                        'start': (row, col),
                        'orientation': orientation
                    }
            
            # Fallback to random placement if no valid placement found
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
            # Update shots from shot_history
            self.shots = set(shot['coord'] for shot in state['shot_history'])
            
            # Remove cells from hunt_stack that are already shot
            while self.hunt_stack and self.hunt_stack[-1] in self.shots:
                cell = self.hunt_stack.pop()
                self.hunt_set.discard(cell)
            
            if self.hunt_stack:
                # Pop from hunt stack
                target = self.hunt_stack.pop()
                self.hunt_set.discard(target)
                return {'target': target}
            else:
                # Random hunting mode
                available_cells = [(r, c) for r in range(self.board_size) 
                                 for c in range(self.board_size) 
                                 if (r, c) not in self.shots]
                
                if not available_cells:
                    # All cells shot, but game should be over
                    return {'target': (0, 0)}
                
                target = random.choice(available_cells)
                return {'target': target}
