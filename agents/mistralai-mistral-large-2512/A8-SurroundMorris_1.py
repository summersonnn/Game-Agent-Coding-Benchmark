"""
Dummy Agent for A8-SurroundMorris (Mistral)
"""
import random

class SurroundMorrisAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, state, feedback=None):
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
                # ADJACENCY check
                try:
                    targets = ADJACENCY[f]
                    for t in targets:
                        if board[t] == '':
                            return (f, t)
                except NameError:
                    pass
            
            return None
