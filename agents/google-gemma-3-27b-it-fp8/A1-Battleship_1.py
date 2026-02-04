"""
Agent Code: A1-Battleship
Model: google/gemma-3-27b-it@preset/fp8
Run: 1
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
        self.last_hit = None
        self.hit_streak = 0

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        """
        Return a tuple: ((row, col), sunk_coords)
        - (row, col): The cell to bomb (0-indexed)
        - sunk_coords: List of coordinates if you've sunk a ship, else []
        
        last_shot_result: 'HIT' or 'MISS' from your previous shot (None on first turn)
        last_shot_coord: (row, col) of your previous shot (None on first turn)
        """
        if last_shot_result == 'HIT':
            self.hit_streak += 1
            row, col = last_shot_coord
            
            # Check adjacent cells
            possible_directions = []
            if row > 0: possible_directions.append((row - 1, col))
            if row < self.board_size - 1: possible_directions.append((row + 1, col))
            if col > 0: possible_directions.append((row, col - 1))
            if col < self.board_size - 1: possible_directions.append((row, col + 1))

            valid_moves = [move for move in possible_directions if move in self.possible_moves]

            if valid_moves:
                return random.choice(valid_moves), []
            else:
                self.hit_streak = 0  # Reset streak if no adjacent hits
                self.last_hit = None
                
        else:
            self.hit_streak = 0
            self.last_hit = None
            
        # If no hit streak, choose a random move
        if self.possible_moves:
            move = self.possible_moves.pop()
            return move, []
        else:
            return None, []  # No moves left

# -------------------------------------------------------------------------------
        
def play_game(game_num, scores):
    """Plays a single, observable game of Battleship and returns the winner's name."""
    game = BattleshipGame(BOARD_SIZE, SHIPS)
    ui = BattleshipUI()
    agent1 = BattleshipAgent("Agent-1", BOARD_SIZE, SHIPS)
    agent2 = BattleshipAgent("Agent-2", BOARD_SIZE, SHIPS)
    
    p1_active_board = [row[:] for row in game.player1_ships_board]
    p2_active_board = [row[:] for row in game.player2_ships_board]
    p1_guess_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    p2_guess_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    players = {
        agent1: {'opponent_ships_board': p2_active_board, 'guess_board': p1_guess_board},
        agent2: {'opponent_ships_board': p1_active_board, 'guess_board': p2_guess_board}
    }
    current_agent, opponent_agent = agent1, agent2
    
    last_shot_coord, last_shot_result = None, None
    turn_continues = False

    while True:
        ui.display_full_game_view(game.player1_ships_board, game.player2_ships_board, p1_guess_board, p2_guess_board, game_num, scores)
        
        if turn_continues:
            print(f"-> {current_agent.name} gets to go again!")

        move, sunk_coords = current_agent.make_move(last_shot_result, last_shot_coord)
        
        if move is None: return opponent_agent.name
            
        row, col = move
        p_data = players[current_agent]
        opponent_ships_board, guess_board = p_data['opponent_ships_board'], p_data['guess_board']
        
        coord_str = f"{chr(ord('A') + col)}{row + 1}"
        print(f"-> {current_agent.name} is bombing {coord_str}.")
        
        result = opponent_ships_board[row][col]
        
        if result == SHIP:
            print("Result: HIT!")
            opponent_ships_board[row][col] = HIT
            guess_board[row][col] = HIT
            last_shot_result = 'HIT'
            turn_continues = True
        else:
            print("Result: MISS!")
            guess_board[row][col] = MISS
            last_shot_result = 'MISS'
            turn_continues = False

        last_shot_coord = move

        if sunk_coords:
            for r, c in sunk_coords:
                guess_board[r][c] = SUNK

        if game.is_game_over(opponent_ships_board):
            ui.display_full_game_view(game.player1_ships_board, game.player2_ships_board, p1_guess_board, p2_guess_board, game_num, scores)
            print(f"\nGAME OVER! {current_agent.name} wins game {game_num}!")
            return current_agent.name
        
        if not turn_continues:
            print(f"Turn passes to {opponent_agent.name}.")
            current_agent, opponent_agent = opponent_agent, current_agent
            last_shot_coord, last_shot_result = None, None

        time.sleep(0.2)

def main():
    """Main function to run the Battleship simulation."""
    scores = {"Agent-1": 0, "Agent-2": 0}

    for i in range(NUM_GAMES):
        game_num = i + 1
        winner = play_game(game_num, scores)
        if winner in scores:
            scores[winner] += 1
        
        time.sleep(1)
        
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "="*45)
    print("---            FINAL SIMULATION SCORE           ---")
    print("="*45)
    print(f"  Total Games Played: {NUM_GAMES}")
    print(f"  Agent-1 Final Score: {scores['Agent-1']}")
    print(f"  Agent-2 Final Score: {scores['Agent-2']}")
    print("="*45)

if __name__ == "__main__":
    main()
