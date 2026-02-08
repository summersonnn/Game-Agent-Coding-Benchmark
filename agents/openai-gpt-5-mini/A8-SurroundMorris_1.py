"""
Dummy Agent for A8-SurroundMorris
"""
import random

class SurroundMorrisAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, state, feedback=None):
        # We don't have access to game logic classes here easily unless we duplicate them
        # or rely on the runner context. The runner injects this code.
        # The runner template has 'SurroundMorrisGame' class available in the global scope?
        # Yes, GAME_CODE_TEMPLATE defines SurroundMorrisGame BEFORE converting agents.
        # Wait, the template order is:
        # 1. Imports
        # 2. Agent 1 Code
        # 3. Agent 2 Code
        # 4. Adjacency
        # 5. Game Class
        # So Agent code CANNOT use SurroundMorrisGame class directly because it's defined AFTER.
        # But `ADJACENCY` is defined after agents too?
        # Let's check template.
        
        # Template:
        # {agent1_code}
        # {agent2_code}
        # ADJACENCY = ...
        # class SurroundMorrisGame ...
        
        # This means agents cannot use Game class or ADJACENCY global at import time.
        # But inside `make_move`, they naturally can if it's available in global scope at runtime.
        # BUT they are defined AFTER. Python reads top to bottom.
        # If `play_game` instantiates agents, the class definitions are already processed?
        # No.
        # The file structure is:
        # ...
        # {agent1_code}
        # ...
        # ADJACENCY = ...
        # ...
        
        # When python loads the file, it executes specific lines.
        # `class SurroundMorrisAgent` is defined.
        # `make_move` is a method.
        # When `play_game` runs (at the bottom), everything is defined.
        # So inside `make_move`, we can access `ADJACENCY` if we use strict lookups.
        
        # Safe bet: Implement standalone random logic.
        
        phase = state["phase"]
        board = state["board"]
        
        if phase == 'placement':
            # Just try random empty spots
            empties = [i for i, x in enumerate(board) if x == '']
            if empties:
                return random.choice(empties)
            return 0
        else:
            # Movement
            my_pieces = [i for i, x in enumerate(board) if x == self.color]
            if not my_pieces:
                return None
            
            # Try 10 random moves
            for _ in range(10):
                f = random.choice(my_pieces)
                # We need adjacency... which might not be visible yet if this class is compiled before ADJACENCY?
                # Actually, if ADJACENCY is defined later in the file, functions defined earlier captures it from global scope
                # ONLY IF it is defined when the function is CALLED.
                # Since `play_game` is called at the end, `ADJACENCY` will be defined by then.
                # So we can access `ADJACENCY`.
                try:
                    targets = ADJACENCY[f]
                    for t in targets:
                        if board[t] == '':
                            return (f, t)
                except NameError:
                    # Fallback if ADJACENCY not found (shouldn't happen if my understanding of python script execution is correct)
                    pass
            
            return None
