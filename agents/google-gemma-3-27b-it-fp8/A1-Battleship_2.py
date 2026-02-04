"""
Agent Code: A1-Battleship
Model: google/gemma-3-27b-it@preset/fp8
Run: 2
Generated: 2026-02-04 16:47:48
"""

import os
import time
from collections import deque

import random
import os
import time
from collections import deque

# --- Game Configuration ---
BOARD_SIZE = 8
SHIPS = [5, 4, 3]
NUM_GAMES = 5

# --- Board Representations ---
EMPTY = 'O'
SHIP = 'S'
HIT = 'X'
SUNK = '#' 
MISS = 'M'

class BattleshipGame:
    """ Manages the state and rules of the game. """
    def __init__(self, size, ships_config):
        self.size = size
        self.ships_config = ships_config
        self.player1_ships_board = self._create_ship_board()
        self.player2_ships_board = self._create_ship_board()

    def _create_empty_board(self):
        return [[EMPTY for _ in range(self.size)] for _ in range(self.size)]

    def _create_ship_board(self):
        """Creates a board and places ships on it."""
        board = self._create_empty_board()
        for length in self.ships_config:
            placed = False
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])
                r = random.randint(0, self.size - (length if orientation == 'vertical' else 1))
                c = random.randint(0, self.size - (length if orientation == 'horizontal' else 1))
                
                if orientation == 'horizontal':
                    if all(board[r][c+i] == EMPTY for i in range(length)):
                        for i in range(length): board[r][c+i] = SHIP
                        placed = True
                else: # vertical
                    if all(board[r+i][c] == EMPTY for i in range(length)):
                        for i in range(length): board[r+i][c] = SHIP
                        placed = True
        return board

    def is_game_over(self, ships_board):
        """Checks if all ships on a given board have been sunk."""
        return not any(SHIP in row for row in ships_board)

class BattleshipUI:
    """ Handles all the visual representation of the game. """
    def display_full_game_view(self, p1_ships, p2_ships, p1_guesses, p2_guesses, game_num, scores):
        os.system('cls' if os.name == 'nt' else 'clear')
        title = f"BATTLESHIPS - GAME {game_num}/{NUM_GAMES}"
        print("=" * 60)
        print(f"{title:^60}")
        print(f"SCORE: Agent-1 ({scores['Agent-1']}) - Agent-2 ({scores['Agent-2']})".center(60))
        print("=" * 60)
        
        print("\n--- INITIAL FLEET DEPLOYMENT (GROUND TRUTH) ---")
        header = "    " + " ".join([chr(ord('A') + i) for i in range(BOARD_SIZE)])
        print("   AGENT-1'S FLEET" + " " * 13 + "AGENT-2'S FLEET")
        print(header + "      " + header)
        for i in range(BOARD_SIZE):
            row_num = str(i + 1).rjust(2)
            p1_row_str = f"{row_num}  " + " ".join(p1_ships[i])
            p2_row_str = f"{row_num}  " + " ".join(p2_ships[i])
            print(p1_row_str + "      " + p2_row_str)
        print("\n" + "=" * 60)
        print("\n--- BOMBING PHASE (PLAYER VIEWS) ---")
        print("   AGENT-1'S GUESSES" + " " * 11 + "AGENT-2'S GUESSES")
        print(header + "      " + header)
        for i in range(BOARD_SIZE):
            row_num = str(i + 1).rjust(2)
            p1_row_str = f"{row_num}  " + " ".join(p1_guesses[i])
            p2_row_str = f"{row_num}  " + " ".join(p2_guesses[i])
            print(p1_row_str + "      " + p2_row_str)
        
        print("\n" + "=" * 60)
        print("--- LOGS ---")

# -------------------------------------------------------------------------------
class BattleshipAgent:
    """
    Your agent implementation goes here.
    Implement smart bombing logic to beat your opponent.
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.possible_moves = deque([(r, c) for r in range(board_size) for c in range(board_size)])
        self.hit_streak = []

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Return a tuple: ((row, col), sunk_coords)
        - (row, col): The cell to bomb (0-indexed)
        - sunk_coords: List of coordinates if you've sunk a ship, else []
        
        last_shot_result: 'HIT' or 'MISS' from your previous shot (None on first turn)
        last_shot_coord: (row, col) of your previous shot (None on first turn)
        """
        if last_shot_result == 'HIT':
            if not self.hit_streak:
                self.hit_streak.append(last_shot_coord)
            
            row, col = last_shot_coord
            
            # Check adjacent cells
            possible_next_shots = []
            if row > 0 and (row - 1, col) not in self.possible_moves:
                possible_next_shots.append((row - 1, col))
            if row < self.board_size - 1 and (row + 1, col) not in self.possible_moves:
                possible_next_shots.append((row + 1, col))
            if col > 0 and (row, col - 1) not in self.possible_moves:
                possible_next_shots.append((row, col - 1))
            if col < self.board_size - 1 and (row, col + 1) not in self.possible_moves:
                possible_next_shots.append((row, col + 1))

            if possible_next_shots:
                next_shot = random.choice(possible_next_shots)
                return next_shot, []
            else:
                # No more adjacent cells, start a new search
                self.hit_streak = []
                
        elif last_shot_result == 'MISS':
            self.hit_streak = []

        # If no hit streak, choose a random possible move
        if self.possible_moves:
            move = self.possible_moves.pop()
            return move, []
        else:
            return None, [] # Should not happen if game logic is correct
